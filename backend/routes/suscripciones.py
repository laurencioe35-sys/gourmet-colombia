import jwt
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy.orm import Session

from ..config import get_env
from ..database import get_db
from ..models import ConfigRestaurante, SolicitudPlan, UsuarioGoogle
from ..schemas import SolicitudPlanCreate

router = APIRouter()


def _refresh_runtime_config():
    global GOOGLE_CLIENT_ID, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_DAYS
    GOOGLE_CLIENT_ID = get_env(
        "GOOGLE_CLIENT_ID",
        "",
        (
            "GOOGLE_CLIENT_ID_WEB",
            "GOOGLE_CLIENT_ID_ANDROID",
            "GOOGLE_CLIENT_ID_IOS",
            "GOOGLE_CLIENT_ID_SERVER",
        ),
    )
    JWT_SECRET = get_env("JWT_SECRET", get_env("SECRET_KEY", ""), ("APP_SECRET", "JWT_SIGNING_SECRET"))
    JWT_ALGORITHM = get_env("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_DAYS = int(get_env("JWT_EXPIRE_DAYS", "30"))


GOOGLE_CLIENT_ID = ""
JWT_SECRET = ""
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30
_refresh_runtime_config()

PLANES = {
    "esencial": {"nombre": "Esencial", "valor": 49000},
    "profesional": {"nombre": "Profesional", "valor": 20000},
    "empresa": {"nombre": "Empresa", "valor": 149000},
}


def crear_token_usuario(usuario: UsuarioGoogle, tipo="cliente"):
    _refresh_runtime_config()
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="JWT_SECRET no está configurado.")
    ahora = datetime.utcnow()
    payload = {
        "sub": str(usuario.id),
        "google_sub": usuario.google_sub,
        "email": usuario.email,
        "tipo": tipo,
        "exp": ahora + timedelta(days=JWT_EXPIRE_DAYS),
        "iat": ahora,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verificar_google_credential(credential: str):
    _refresh_runtime_config()
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID no está configurado.")
    try:
        info = id_token.verify_oauth2_token(
            credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
            raise ValueError("Emisor de Google inválido")
        email = (info.get("email") or "").strip().lower()
        if not email or not info.get("email_verified", False) or not info.get("sub"):
            raise ValueError("Identidad de Google incompleta")
        return {
            "google_sub": info["sub"],
            "email": email,
            "nombre": info.get("name", ""),
            "foto_url": info.get("picture", ""),
        }
    except ValueError:
        raise HTTPException(status_code=401, detail="La autenticación con Google no es válida o expiró.")


def _usuario_desde_autorizacion(authorization, db: Session, permitir_registro=True):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sesión no encontrada o formato inválido.")
    try:
        payload = jwt.decode(authorization[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if not permitir_registro and payload.get("tipo") != "cliente":
            raise ValueError("Tipo de token inválido")
        usuario_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="La sesión expiró.")
    except Exception:
        raise HTTPException(status_code=401, detail="Sesión inválida.")
    usuario = db.query(UsuarioGoogle).filter(UsuarioGoogle.id == usuario_id).first()
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario no disponible.")
    return usuario


def _normalizar_referencia(valor: str) -> str:
    return (valor or "").strip()


def _solicitud_por_email_referencia(db: Session, email: str, referencia: str):
    email_normal = (email or "").strip().lower()
    referencia_normal = _normalizar_referencia(referencia)
    if not email_normal or not referencia_normal:
        return None
    return db.query(SolicitudPlan).filter(
        SolicitudPlan.email == email_normal,
        SolicitudPlan.referencia_pago == referencia_normal,
    ).order_by(SolicitudPlan.created_at.desc()).first()


def _aprobacion_valida(db: Session, email: str, referencia: str):
    solicitud = _solicitud_por_email_referencia(db, email, referencia)
    return solicitud is not None and solicitud.estado == "aprobado"


def _config(db, clave, defecto=""):
    item = db.query(ConfigRestaurante).filter(ConfigRestaurante.clave == clave).first()
    return item.valor if item and item.valor else defecto


@router.get("/planes")
def listar_planes():
    return PLANES


@router.get("/google-config")
def get_google_config():
    _refresh_runtime_config()
    return {"client_id": GOOGLE_CLIENT_ID, "enabled": bool(GOOGLE_CLIENT_ID)}


@router.post("/estado")
def estado_solicitud(data: dict, db: Session = Depends(get_db)):
    email = (data.get("email") or "").strip().lower()
    referencia = _normalizar_referencia(data.get("referencia"))
    if not email or not referencia:
        raise HTTPException(status_code=400, detail="Debes ingresar el correo y la referencia para consultar el estado.")

    solicitud = _solicitud_por_email_referencia(db, email, referencia)
    if solicitud is None:
        return {"estado": "pendiente", "aprobado": False, "mensaje": "No existe una solicitud registrada para este correo y referencia."}

    if solicitud.estado == "aprobado":
        return {"estado": "aprobado", "aprobado": True, "mensaje": "La solicitud ya fue aprobada por el administrador."}

    return {"estado": solicitud.estado, "aprobado": False, "mensaje": "La solicitud sigue pendiente por validación del administrador."}


@router.post("/google")
def autenticar_google(data: dict, db: Session = Depends(get_db)):
    datos = verificar_google_credential(data.get("credential", ""))
    usuario = db.query(UsuarioGoogle).filter(UsuarioGoogle.google_sub == datos["google_sub"]).first()
    nuevo_usuario = usuario is None
    if usuario is None:
        usuario_por_email = db.query(UsuarioGoogle).filter(UsuarioGoogle.email == datos["email"]).first()
        if usuario_por_email:
            raise HTTPException(status_code=409, detail="El correo ya está vinculado a otra cuenta de Google.")
        usuario = UsuarioGoogle(**datos)
        db.add(usuario)
        db.flush()
    else:
        usuario.email = datos["email"]
        usuario.nombre = datos["nombre"]
        usuario.foto_url = datos["foto_url"]
        usuario.last_login_at = datetime.utcnow()

    solicitud = None
    if usuario.solicitud_plan_id:
        solicitud = db.query(SolicitudPlan).filter(SolicitudPlan.id == usuario.solicitud_plan_id).first()
    if solicitud is None:
        solicitud = db.query(SolicitudPlan).filter(SolicitudPlan.email == usuario.email).order_by(SolicitudPlan.created_at.desc()).first()
        if solicitud:
            usuario.solicitud_plan_id = solicitud.id
    db.commit()

    respuesta = {"ok": True, "nuevo_usuario": nuevo_usuario, "usuario": {
        "id": usuario.id, "email": usuario.email, "nombre": usuario.nombre, "foto_url": usuario.foto_url,
    }}
    if solicitud is None:
        respuesta.update({"aprobado": False, "sin_plan": True, "registro_token": crear_token_usuario(usuario, "registro")})
        return respuesta
    if solicitud.estado != "aprobado":
        respuesta.update({"aprobado": False, "estado": solicitud.estado, "registro_token": crear_token_usuario(usuario, "registro")})
        return respuesta
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Esta cuenta está desactivada.")
    respuesta.update({"aprobado": True, "token": crear_token_usuario(usuario)})
    return respuesta


@router.post("/validar-acceso")
def validar_acceso(data: dict, db: Session = Depends(get_db)):
    email = (data.get("email") or "").strip().lower()
    referencia = _normalizar_referencia(data.get("referencia"))
    estado = estado_solicitud({"email": email, "referencia": referencia}, db)
    if not estado.get("aprobado"):
        raise HTTPException(status_code=403, detail="La cuenta aún no está aprobada por el administrador")
    usuario = db.query(UsuarioGoogle).filter(UsuarioGoogle.email == email).first()
    if usuario is None:
        raise HTTPException(status_code=403, detail="Primero debes identificarte con tu cuenta de Google.")
    return {"ok": True, "token": crear_token_usuario(usuario), "mensaje": "Acceso habilitado"}


@router.post("/solicitudes")
def crear_solicitud(
    data: SolicitudPlanCreate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    usuario = _usuario_desde_autorizacion(authorization, db)
    if data.plan not in PLANES:
        raise HTTPException(status_code=400, detail="Selecciona un plan válido")
    if data.metodo_pago not in ("nequi", "daviplata"):
        raise HTTPException(status_code=400, detail="Selecciona Nequi o Daviplata")
    if not data.acepta_terminos:
        raise HTTPException(status_code=400, detail="Debes aceptar el tratamiento de datos")

    referencia_pago = _normalizar_referencia(data.referencia_pago)
    if not referencia_pago:
        raise HTTPException(status_code=400, detail="Debes ingresar la referencia del pago de Nequi o Daviplata antes de continuar")

    email = (data.email or "").strip().lower()
    if email != usuario.email:
        raise HTTPException(status_code=400, detail="El correo debe coincidir con la cuenta de Google.")

    referencia_existente = db.query(SolicitudPlan).filter(
        SolicitudPlan.referencia_pago == referencia_pago,
        SolicitudPlan.email != email,
    ).first()
    if referencia_existente:
        raise HTTPException(
            status_code=400,
            detail="La referencia de pago ya está asociada a otro usuario o correo y no puede reutilizarse.",
        )

    email_existente = db.query(SolicitudPlan).filter(
        SolicitudPlan.email == email,
        SolicitudPlan.estado.in_(["pendiente", "reportado", "aprobado"]),
    ).first()
    if email_existente:
        mensaje = (
            "Esta cuenta ya está registrada y aprobada. Ingresa nuevamente usando Google."
            if email_existente.estado == "aprobado"
            else "Esta cuenta ya tiene una solicitud registrada y está pendiente de validación."
        )
        raise HTTPException(
            status_code=400,
            detail=mensaje,
        )

    info = PLANES[data.plan]
    referencia = f"GP-{datetime.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
    solicitud = SolicitudPlan(
        referencia=referencia,
        plan=data.plan,
        valor=info["valor"],
        estado="reportado" if referencia_pago else "pendiente",
        **data.model_dump(exclude={"plan", "referencia_pago"}),
    )
    solicitud.referencia_pago = referencia_pago
    db.add(solicitud)
    db.flush()
    usuario.solicitud_plan_id = solicitud.id

    # Estos campos alimentan el encabezado de los tickets del POS.
    valores = {"nombre": data.nombre_negocio, "ruc": data.nit, "razon_social": data.razon_social,
               "direccion": data.direccion, "telefono": data.telefono, "ciudad": data.ciudad,
               "email_facturacion": data.email, "plan_activo": info["nombre"]}
    for clave, valor in valores.items():
        item = db.query(ConfigRestaurante).filter(ConfigRestaurante.clave == clave).first()
        if item: item.valor = valor
        else: db.add(ConfigRestaurante(clave=clave, valor=valor))
    db.commit()

    cuenta = _config(db, data.metodo_pago, "Por configurar")
    return {"ok": True, "referencia": referencia, "estado": solicitud.estado, "plan": info["nombre"],
            "valor": info["valor"], "cuenta_destino": cuenta,
            "mensaje": "Solicitud registrada. Te enviaremos la confirmación al correo indicado cuando validemos el pago."}


@router.get("/me")
def obtener_usuario_actual(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    usuario = _usuario_desde_autorizacion(authorization, db, permitir_registro=False)
    return {"id": usuario.id, "email": usuario.email, "nombre": usuario.nombre, "foto_url": usuario.foto_url}
