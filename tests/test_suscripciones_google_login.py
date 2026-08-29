from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, SessionLocal, engine
from backend.models import SolicitudPlan, UsuarioGoogle


def setup_approved_email(email: str = "cliente@test.com", referencia: str = "123456"):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(SolicitudPlan).filter(SolicitudPlan.email == email).delete()
    db.query(UsuarioGoogle).filter(UsuarioGoogle.email == email).delete()
    db.commit()
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


def test_google_access_is_allowed_for_approved_email(monkeypatch):
    setup_approved_email()
    monkeypatch.setattr(
        "backend.routes.suscripciones.verificar_google_credential",
        lambda credential: {
            "google_sub": "google-sub-cliente",
            "email": "cliente@test.com",
            "nombre": "Ana",
            "foto_url": "https://example.com/ana.jpg",
        },
    )
    with TestClient(app) as client:
        response = client.post("/api/suscripciones/google", json={"credential": "credential-falsa"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["token"]
        me = client.get("/api/suscripciones/me", headers={"Authorization": f"Bearer {payload['token']}"})
        assert me.status_code == 200
        assert me.json()["email"] == "cliente@test.com"


def test_google_access_creates_registration_token_for_new_user(monkeypatch):
    db = SessionLocal()
    db.query(SolicitudPlan).filter(SolicitudPlan.email == "nueva@test.com").delete()
    db.query(UsuarioGoogle).filter(UsuarioGoogle.email == "nueva@test.com").delete()
    db.commit()
    db.close()
    monkeypatch.setattr(
        "backend.routes.suscripciones.verificar_google_credential",
        lambda credential: {
            "google_sub": "google-sub-nueva",
            "email": "nueva@test.com",
            "nombre": "Nueva",
            "foto_url": "",
        },
    )

    with TestClient(app) as client:
        response = client.post("/api/suscripciones/google", json={"credential": "credential-falsa"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["sin_plan"] is True
        assert payload["registro_token"]


def test_subscription_status_accepts_approved_email_and_reference():
    setup_approved_email("cliente@test.com", "123456")
    with TestClient(app) as client:
        response = client.post(
            "/api/suscripciones/estado",
            json={"email": "cliente@test.com", "referencia": "123456"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["aprobado"] is True
        assert payload["estado"] == "aprobado"
