"""WhatsApp confirmation integration behavior and failure-state tests."""

import asyncio
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
import server


class FakeCollection:
    def __init__(self):
        self.updates = []

    async def update_one(self, selector, update):
        self.updates.append((selector, update))


class FakeDb:
    def __init__(self):
        self.appointments = FakeCollection()


def appointment():
    return server.Appointment(
        service={"id": "s1", "name": "Corte Clássico"},
        barber={"id": "b1", "name": "Carille"},
        date="2026-12-30",
        time="09:00",
        name="Cliente Teste",
        phone="(11) 99999-9999",
    )


def test_missing_meta_credentials_marks_not_configured(monkeypatch):
    fake_db = FakeDb()
    monkeypatch.setattr(server, "db", fake_db)
    monkeypatch.delenv("META_PHONE_NUMBER_ID", raising=False)
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)

    asyncio.run(server.send_whatsapp_confirmation(appointment()))

    assert fake_db.appointments.updates[0][1] == {"$set": {"whatsappStatus": "not_configured"}}


def test_graph_payload_uses_template_locale_and_expected_parameters(monkeypatch):
    fake_db = FakeDb()
    monkeypatch.setattr(server, "db", fake_db)
    monkeypatch.setenv("META_PHONE_NUMBER_ID", "phone-id")
    monkeypatch.setenv("META_ACCESS_TOKEN", "secret-token")

    captured = {}

    class Response:
        is_success = True
        status_code = 200

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers, json):
            captured.update(url=url, headers=headers, json=json)
            return Response()

    monkeypatch.setattr(server.httpx, "AsyncClient", lambda timeout: Client())
    asyncio.run(server.send_whatsapp_confirmation(appointment()))

    assert captured["url"] == "https://graph.facebook.com/v23.0/phone-id/messages"
    assert captured["headers"]["Authorization"] == "Bearer secret-token"
    template = captured["json"]["template"]
    assert template["name"] == "appointment_confirmation"
    assert template["language"] == {"code": "pt_BR"}
    assert [item["text"] for item in template["components"][0]["parameters"]] == [
        "Cliente Teste", "09:00", "2026-12-30 às 09:00", "Carille", "Corte Clássico"
    ]
    assert fake_db.appointments.updates[0][1] == {"$set": {"whatsappStatus": "sent"}}


def test_http_failure_marks_failed_and_transport_error_marks_retry(monkeypatch):
    fake_db = FakeDb()
    monkeypatch.setattr(server, "db", fake_db)
    monkeypatch.setenv("META_PHONE_NUMBER_ID", "phone-id")
    monkeypatch.setenv("META_ACCESS_TOKEN", "secret-token")

    class FailedResponse:
        is_success = False
        status_code = 400

    class FailedClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def post(self, *args, **kwargs): return FailedResponse()

    monkeypatch.setattr(server.httpx, "AsyncClient", lambda timeout: FailedClient())
    asyncio.run(server.send_whatsapp_confirmation(appointment()))
    assert fake_db.appointments.updates[-1][1] == {"$set": {"whatsappStatus": "failed"}}

    class ErrorClient(FailedClient):
        async def post(self, *args, **kwargs): raise server.httpx.HTTPError("network")

    monkeypatch.setattr(server.httpx, "AsyncClient", lambda timeout: ErrorClient())
    asyncio.run(server.send_whatsapp_confirmation(appointment()))
    assert fake_db.appointments.updates[-1][1] == {"$set": {"whatsappStatus": "retry"}}