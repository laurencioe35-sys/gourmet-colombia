from fastapi.testclient import TestClient

from backend.database import SessionLocal
from backend.main import app
from backend.models import Producto
from backend.seed_data import seed_database


def test_seed_database_creates_default_menu_items():
    db = SessionLocal()
    try:
        db.query(Producto).delete()
        db.commit()
        seed_database(db)
    finally:
        db.close()

    client = TestClient(app)
    response = client.get('/api/menu/completo')

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload) > 0
    assert any(len(cat['productos']) > 0 for cat in payload)
