from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ConfigRestaurante, SolicitudPlan
from ..schemas import SolicitudPlanCreate

router = APIRouter()

PLANES = {
    "esencial": {"nombre": "Esencial", "valor": 49000},
    "profesional": {"nombre": "Profesional", "valor": 89000},
    "empresa": {"nombre": "Empresa", "valor": 149000},
}


def _config(db, clave, defecto=""):
    item = db.query(ConfigRestaurante).filter(ConfigRestaurante.clave == clave).first()
    return item.valor if item and item.valor else defecto


@router.get("/planes")
def listar_planes():
    return PLANES


@router.post("/solicitudes")
def crear_solicitud(data: SolicitudPlanCreate, db: Session = Depends(get_db)):
    if data.plan not in PLANES:
        raise HTTPException(status_code=400, detail="Selecciona un plan válido")
    if data.metodo_pago not in ("nequi", "daviplata"):
        raise HTTPException(status_code=400, detail="Selecciona Nequi o Daviplata")
    if not data.acepta_terminos:
        raise HTTPException(status_code=400, detail="Debes aceptar el tratamiento de datos")

    info = PLANES[data.plan]
    referencia = f"GP-{datetime.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
    solicitud = SolicitudPlan(
        referencia=referencia, plan=data.plan, valor=info["valor"], estado="reportado" if data.referencia_pago else "pendiente",
        **data.model_dump(exclude={"plan"})
    )
    db.add(solicitud)

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
