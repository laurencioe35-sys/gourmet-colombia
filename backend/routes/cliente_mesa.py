from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from ..database import get_db
from ..models import Mesa, MesaClienteSession, Pedido, EstadoPedido

router = APIRouter(prefix="/api/cliente", tags=["Cliente Mesa"])


@router.post("/mesa/validar")
def validar_qr_mesa(payload: dict, db: Session = Depends(get_db)):
    mesa_id = payload.get('mesa_id')
    token = payload.get('token')
    if not mesa_id or not token:
        raise HTTPException(status_code=400, detail='Faltan mesa_id o token')

    mesa = db.query(Mesa).filter(Mesa.id == mesa_id, Mesa.activo == True).first()
    if not mesa:
        raise HTTPException(status_code=404, detail='Mesa no encontrada')
    if mesa.qr_token and token != mesa.qr_token:
        raise HTTPException(status_code=403, detail='Token QR inválido')
    return {
        'ok': True,
        'mesa_id': mesa.id,
        'numero': mesa.numero,
        'ubicacion': mesa.ubicacion,
        'capacidad': mesa.capacidad,
        'restaurante': 'GourmetPOS'
    }


@router.post("/mesa/sesion")
def crear_sesion_cliente(payload: dict, db: Session = Depends(get_db)):
    mesa_id = payload.get('mesa_id')
    token = payload.get('token')
    nombre = (payload.get('nombre') or '').strip()
    whatsapp = (payload.get('whatsapp') or '').strip()

    if not mesa_id or not token or not nombre or not whatsapp:
        raise HTTPException(status_code=400, detail='Faltan datos para iniciar sesión')

    mesa = db.query(Mesa).filter(Mesa.id == mesa_id, Mesa.activo == True).first()
    if not mesa:
        raise HTTPException(status_code=404, detail='Mesa no encontrada')
    if mesa.qr_token and token != mesa.qr_token:
        raise HTTPException(status_code=403, detail='Token QR inválido')

    session_id = uuid.uuid4().hex
    sesion = MesaClienteSession(
        mesa_id=mesa.id,
        session_id=session_id,
        nombre=nombre,
        whatsapp=whatsapp,
        token=token,
        estado='activo',
        expira_en=datetime.utcnow() + timedelta(hours=6)
    )
    db.add(sesion)
    db.commit()
    db.refresh(sesion)

    return {
        'ok': True,
        'session_id': session_id,
        'mesa_id': mesa.id,
        'numero': mesa.numero,
        'whatsapp': whatsapp,
        'nombre': nombre,
        'expira_en': sesion.expira_en.isoformat()
    }


@router.post("/{session_id}/pedido")
def crear_pedido_cliente(session_id: str, payload: dict, db: Session = Depends(get_db)):
    sesion = db.query(MesaClienteSession).filter(MesaClienteSession.session_id == session_id).first()
    if not sesion:
        raise HTTPException(status_code=404, detail='Sesión no encontrada')
    if sesion.expira_en and sesion.expira_en < datetime.utcnow():
        raise HTTPException(status_code=401, detail='La sesión expiró')

    mesa_id = payload.get('mesa_id') or sesion.mesa_id
    if not mesa_id:
        raise HTTPException(status_code=400, detail='Falta mesa_id')

    pedido = Pedido(
        mesa_id=mesa_id,
        estado=EstadoPedido.pendiente,
        notas=payload.get('notas', ''),
        numero_ticket=f'CLI-{uuid.uuid4().hex[:8].upper()}'
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    sesion.pedido_id = pedido.id
    db.commit()

    return {
        'ok': True,
        'pedido_id': pedido.id,
        'mesa_id': mesa_id,
        'numero_ticket': pedido.numero_ticket,
        'estado': pedido.estado.value,
        'session_id': session_id
    }


@router.get("/{session_id}/pedido")
def obtener_pedido_cliente(session_id: str, db: Session = Depends(get_db)):
    sesion = db.query(MesaClienteSession).filter(MesaClienteSession.session_id == session_id).first()
    if not sesion:
        raise HTTPException(status_code=404, detail='Sesión no encontrada')
    if not sesion.pedido_id:
        raise HTTPException(status_code=404, detail='No hay pedido activo para esta sesión')
    pedido = db.query(Pedido).filter(Pedido.id == sesion.pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail='Pedido no encontrado')
    return {
        'pedido_id': pedido.id,
        'mesa_id': pedido.mesa_id,
        'estado': pedido.estado.value,
        'total': pedido.total,
        'numero_ticket': pedido.numero_ticket,
        'nombre': sesion.nombre,
        'whatsapp': sesion.whatsapp
    }
