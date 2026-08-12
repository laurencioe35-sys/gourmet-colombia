import hashlib
import os
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db, engine, Base
from ..models import SolicitudPlan, UsuarioAdmin

router = APIRouter()
sesiones = {}


def hash_password(password: str, salt: str = None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, encoded: str):
    salt, digest = encoded.split("$", 1)
    return secrets.compare_digest(hash_password(password, salt), encoded)


def bootstrap_admin(db):
    Base.metadata.create_all(bind=engine)
    email = (os.getenv("ADMIN_EMAIL") or "edwinsumara3@gmail.com").lower().strip()
    password = os.getenv("ADMIN_PASSWORD") or "GourmetPOS2026!"
    user = db.query(UsuarioAdmin).filter_by(email=email).first()

    if not user:
        db.add(UsuarioAdmin(email=email, password_hash=hash_password(password), nombre="Administrador GourmetPOS"))
        db.commit()
        return

    if not verify_password(password, user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()


class LoginData(BaseModel):
    email: str
    password: str


def require_admin(authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ").strip()
    if not token or token not in sesiones:
        raise HTTPException(status_code=401, detail="Inicia sesión como administrador")
    return sesiones[token]


@router.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    bootstrap_admin(db)
    user = db.query(UsuarioAdmin).filter_by(email=data.email.lower().strip()).first()
    if not user or not user.activo or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    token = secrets.token_urlsafe(32)
    sesiones[token] = {"email": user.email, "nombre": user.nombre, "at": datetime.utcnow().isoformat()}
    return {"token": token, "usuario": sesiones[token]}


@router.get("/solicitudes")
def solicitudes(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    items = db.query(SolicitudPlan).order_by(SolicitudPlan.created_at.desc()).all()
    return [{"id": x.id, "referencia": x.referencia, "plan": x.plan, "valor": x.valor,
             "estado": x.estado, "negocio": x.nombre_negocio, "nit": x.nit, "responsable": x.responsable,
             "email": x.email, "telefono": x.telefono, "metodo_pago": x.metodo_pago,
             "referencia_pago": x.referencia_pago, "created_at": x.created_at} for x in items]


@router.put("/solicitudes/{solicitud_id}/aprobar")
def aprobar(solicitud_id: int, _: dict = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.get(SolicitudPlan, solicitud_id)
    if not item:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    referencia_duplicada = db.query(SolicitudPlan).filter(
        SolicitudPlan.referencia_pago == item.referencia_pago,
        SolicitudPlan.id != item.id,
    ).first()
    if referencia_duplicada:
        raise HTTPException(
            status_code=400,
            detail="No se puede aprobar: la referencia ya está asociada a otra solicitud o usuario.",
        )

    if item.estado == "aprobado":
        return {"ok": True, "estado": item.estado, "mensaje": "La solicitud ya estaba aprobada."}

    item.estado = "aprobado"
    db.commit()
    return {"ok": True, "estado": item.estado}
