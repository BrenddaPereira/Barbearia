from datetime import datetime, timezone
from pathlib import Path
import logging
import os
import uuid

from dotenv import load_dotenv
import httpx
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
app = FastAPI(title="Carille Barbearia API")
api_router = APIRouter(prefix="/api")


class Appointment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service: dict
    barber: dict
    date: str
    time: str
    name: str
    phone: str
    status: str = "Confirmado"
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    whatsappStatus: str = "pending"


def normalize_whatsapp_phone(phone: str) -> str:
    digits = "".join(character for character in phone if character.isdigit())
    if digits.startswith("55"):
        return digits
    if len(digits) in (10, 11):
        return f"55{digits}"
    return digits


async def send_whatsapp_confirmation(appointment: Appointment):
    phone_id = os.environ.get("META_PHONE_NUMBER_ID")
    access_token = os.environ.get("META_ACCESS_TOKEN")
    if not phone_id or not access_token:
        logging.getLogger(__name__).warning("WhatsApp não configurado; reserva mantida sem envio")
        await db.appointments.update_one(
            {"id": appointment.id}, {"$set": {"whatsappStatus": "not_configured"}}
        )
        return

    version = os.environ.get("META_GRAPH_VERSION", "v23.0")
    template = os.environ.get("META_WA_TEMPLATE", "appointment_confirmation")
    language = os.environ.get("META_WA_LANGUAGE", "pt_BR")
    when = f"{appointment.date} às {appointment.time}"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": normalize_whatsapp_phone(appointment.phone),
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": language},
            "components": [{
                "type": "body",
                "parameters": [
                    {"type": "text", "text": appointment.name},
                    {"type": "text", "text": appointment.time},
                    {"type": "text", "text": when},
                    {"type": "text", "text": appointment.barber.get("name", "Barbeiro")},
                    {"type": "text", "text": appointment.service.get("name", "serviço")},
                ],
            }],
        },
    }
    try:
        async with httpx.AsyncClient(timeout=15) as http_client:
            response = await http_client.post(
                f"https://graph.facebook.com/{version}/{phone_id}/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                json=payload,
            )
        status = "sent" if response.is_success else "failed"
        await db.appointments.update_one(
            {"id": appointment.id}, {"$set": {"whatsappStatus": status}}
        )
        if not response.is_success:
            logging.getLogger(__name__).error("Falha no envio WhatsApp: status=%s", response.status_code)
    except httpx.HTTPError:
        await db.appointments.update_one(
            {"id": appointment.id}, {"$set": {"whatsappStatus": "retry"}}
        )


@api_router.get("/")
async def root():
    return {"message": "Carille Barbearia API online"}


@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appointment: Appointment, background_tasks: BackgroundTasks):
    existing = await db.appointments.find_one(
        {"date": appointment.date, "time": appointment.time, "barber.id": appointment.barber.get("id")},
        {"_id": 0},
    )
    if existing:
        raise HTTPException(status_code=409, detail="Este horário já foi reservado.")
    document = appointment.model_dump()
    await db.appointments.insert_one(document)
    background_tasks.add_task(send_whatsapp_confirmation, appointment)
    return appointment


@api_router.get("/appointments", response_model=list[Appointment])
async def list_appointments():
    documents = await db.appointments.find({}, {"_id": 0}).sort("date", 1).to_list(1000)
    return documents


@api_router.delete("/appointments/{appointment_id}")
async def cancel_appointment(appointment_id: str):
    result = await db.appointments.delete_one({"id": appointment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    return {"deleted": True, "id": appointment_id}


app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()