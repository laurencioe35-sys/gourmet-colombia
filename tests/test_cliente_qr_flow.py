from datetime import date

from fastapi.testclient import TestClient

from backend.database import SessionLocal
from backend.main import app
from backend.models import Mesa


def test_daily_qr_token_rotates_every_day():
    db = SessionLocal()
    try:
        db.query(Mesa).filter(Mesa.numero == 999).delete()
        db.commit()
        mesa = Mesa(numero=999, capacidad=4, activo=True)
        db.add(mesa)
        db.commit()
        db.refresh(mesa)

        from backend.routes.mesas import generar_token_diario_mesa
        token1 = generar_token_diario_mesa(mesa.id, date.today())
        mesa.qr_token = token1
        db.commit()

        token2 = generar_token_diario_mesa(mesa.id, date.today())
        assert token1 == token2
        assert token1 != ""
        assert "mesa-" in token1.lower()
    finally:
        db.close()


def test_cliente_qr_flow_creates_guest_session_and_order():
    db = SessionLocal()
    try:
        db.query(Mesa).delete()
        db.commit()

        mesa = Mesa(numero=998, capacidad=4, qr_token='mesa-qr-123', activo=True)
        db.add(mesa)
        db.commit()
        db.refresh(mesa)
        mesa_id = mesa.id
    finally:
        db.close()

    client = TestClient(app)

    validacion = client.post('/api/cliente/mesa/validar', json={
        'mesa_id': mesa_id,
        'token': 'mesa-qr-123'
    })
    assert validacion.status_code == 200, validacion.text
    assert validacion.json()['mesa_id'] == mesa_id

    sesion = client.post('/api/cliente/mesa/sesion', json={
        'mesa_id': mesa_id,
        'token': 'mesa-qr-123',
        'nombre': 'Cliente prueba',
        'whatsapp': '573001234567'
    })
    assert sesion.status_code == 200, sesion.text
    payload = sesion.json()
    assert payload['mesa_id'] == mesa_id
    assert payload['whatsapp'] == '573001234567'
    session_id = payload['session_id']

    pedido = client.post(f'/api/cliente/{session_id}/pedido', json={
        'mesa_id': mesa_id,
        'notas': 'Pedido de prueba'
    })
    assert pedido.status_code == 200, pedido.text
    assert pedido.json()['mesa_id'] == mesa_id
