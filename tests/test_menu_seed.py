from fastapi.testclient import TestClient

from backend.database import SessionLocal
from backend.main import app
from backend.models import Categoria, Producto
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


def test_current_lunch_price_is_normalized_when_zero():
    db = SessionLocal()
    try:
        db.query(Producto).delete()
        db.commit()
        seed_database(db)
        categoria = db.query(Categoria).filter(Categoria.nombre.ilike('%almuerzos corrientes%')).first()
        db.query(Producto).filter(Producto.categoria_id == categoria.id).update({Producto.precio: 0})
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    response = client.get('/api/menu/completo')

    assert response.status_code == 200, response.text
    payload = response.json()
    corrientes = next(cat for cat in payload if 'almuerzos corrientes' in cat['nombre'].lower())
    assert corrientes['productos']
    assert all(p['precio'] > 0 for p in corrientes['productos'])
    assert any(p['nombre'].lower().startswith('almuerzo') and p['precio'] == 18000 for p in corrientes['productos'])
