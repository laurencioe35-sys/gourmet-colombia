from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models import SolicitudPlan


def setup_approved_email(email: str = "cliente@test.com", referencia: str = "123456"):
    db = SessionLocal()
    db.query(SolicitudPlan).filter(SolicitudPlan.email == email).delete()
    db.add(
        SolicitudPlan(
            referencia="TEST-GOOGLE-1",
            plan="profesional",
            valor=20000,
            estado="aprobado",
            nombre_negocio="Negocio Google",
            nit="900123456-1",
            razon_social="Negocio Google SAS",
            responsable="Ana",
            email=email,
            telefono="3001234567",
            direccion="Calle 123",
            ciudad="Bogota",
            metodo_pago="nequi",
            referencia_pago=referencia,
            acepta_terminos=True,
        )
    )
    db.commit()
    db.close()


def test_google_access_is_allowed_for_approved_email():
    setup_approved_email()
    client = TestClient(app)

    response = client.post("/api/suscripciones/validar-acceso-google", json={"email": "cliente@test.com"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["token"]


def test_google_access_is_rejected_for_unapproved_email():
    db = SessionLocal()
    db.query(SolicitudPlan).filter(SolicitudPlan.email == "nueva@test.com").delete()
    db.close()

    client = TestClient(app)
    response = client.post("/api/suscripciones/validar-acceso-google", json={"email": "nueva@test.com"})

    assert response.status_code == 403
