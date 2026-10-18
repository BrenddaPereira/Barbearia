from datetime import datetime, timezone
from pathlib import Path
import logging
import os
import uuid

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
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


@api_router.get("/")
async def root():
    return {"message": "Carille Barbearia API online"}


@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appointment: Appointment):
    existing = await db.appointments.find_one(
        {"date": appointment.date, "time": appointment.time, "barber.id": appointment.barber.get("id")},
        {"_id": 0},
    )
    if existing:
        raise HTTPException(status_code=409, detail="Este horário já foi reservado.")
    document = appointment.model_dump()
    await db.appointments.insert_one(document)
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