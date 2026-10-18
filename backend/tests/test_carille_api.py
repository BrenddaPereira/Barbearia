import os
import uuid

import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://barbearia-carille.preview.emergentagent.com").rstrip("/")


def test_appointments_create_list_delete_persistence():
    appointment_id = str(uuid.uuid4())
    payload = {
        "id": appointment_id,
        "service": {"id": "s-test", "name": "TEST Corte", "duration": 45, "price": 45},
        "barber": {"id": "b-test", "name": "TEST Carille"},
        "date": "2099-12-30",
        "time": "09:00",
        "name": "TEST Cliente",
        "phone": "11999999999",
    }
    created = requests.post(f"{BASE_URL}/api/appointments", json=payload, timeout=20)
    assert created.status_code == 200, created.text
    assert created.json()["id"] == appointment_id
    listed = requests.get(f"{BASE_URL}/api/appointments", timeout=20)
    assert listed.status_code == 200
    assert any(item["id"] == appointment_id and item["name"] == "TEST Cliente" for item in listed.json())
    duplicate = requests.post(f"{BASE_URL}/api/appointments", json=payload, timeout=20)
    assert duplicate.status_code == 409
    deleted = requests.delete(f"{BASE_URL}/api/appointments/{appointment_id}", timeout=20)
    assert deleted.status_code == 200
    missing = requests.delete(f"{BASE_URL}/api/appointments/{appointment_id}", timeout=20)
    assert missing.status_code == 404