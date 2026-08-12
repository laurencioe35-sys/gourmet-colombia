from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models import Mesa


def test_mesas_route_loads_with_existing_db_schema():
    db = SessionLocal()
    db.query(Mesa).filter(Mesa.numero == 999).delete()
    db.add(Mesa(numero=999, capacidad=4, ubicacion="Salon principal"))
    db.commit()
    db.close()

    client = TestClient(app)
    response = client.get("/api/mesas/")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert any(m["numero"] == 999 for m in payload)
