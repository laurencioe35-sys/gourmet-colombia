import hashlib
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Mesa, Pedido, EstadoMesa, EstadoPedido
from ..schemas import MesaCreate, MesaUpdate, MesaOut, PedidoOut


def generar_token_diario_mesa(mesa_id: int, dia: date | None = None) -> str:
    """Genera un token único por mesa y por día. Se renueva cada jornada."""
    dia_actual = dia or date.today()
    seed = f"mesa:{mesa_id}:day:{dia_actual.isoformat()}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"mesa-{mesa_id}-{dia_actual.strftime('%Y%m%d')}-{digest}"

router = APIRouter()


def _estado_mesa_desde_pedido(mesa: Mesa, db: Session):
    pedido_activo = db.query(Pedido).filter(
        Pedido.mesa_id == mesa.id,
        Pedido.estado.in_([
            EstadoPedido.pendiente,
            EstadoPedido.en_preparacion,
            EstadoPedido.listo,
        ])
    ).order_by(Pedido.created_at.desc()).first()

    if pedido_activo is None:
        mesa.estado = EstadoMesa.libre
        return "libre", None, 0, 0

    if pedido_activo.estado == EstadoPedido.listo:
        mesa.estado = EstadoMesa.cuenta
    else:
        mesa.estado = EstadoMesa.ocupada

    return mesa.estado.value, pedido_activo.id, pedido_activo.total or 0, len(pedido_activo.detalles or [])


@router.get("/", response_model=List[dict])
def listar_mesas(db: Session = Depends(get_db)):
    mesas = db.query(Mesa).filter(Mesa.activo == True).order_by(Mesa.numero).all()
    resultado = []
    for mesa in mesas:
        estado, pedido_id, total_pedido, items_count = _estado_mesa_desde_pedido(mesa, db)
        if mesa.estado != EstadoMesa(estado):
            mesa.estado = EstadoMesa(estado)
        db.commit()
        resultado.append({
            "id": mesa.id,
            "numero": mesa.numero,
            "capacidad": mesa.capacidad,
            "estado": estado,
            "ubicacion": mesa.ubicacion,
            "pedido_activo_id": pedido_id,
            "total_pedido": total_pedido,
            "items_count": items_count,
        })
    return resultado


@router.get("/{mesa_id}")
def obtener_mesa(mesa_id: int, db: Session = Depends(get_db)):
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return mesa


@router.post("/", response_model=dict)
def crear_mesa(data: MesaCreate, db: Session = Depends(get_db)):
    existe = db.query(Mesa).filter(Mesa.numero == data.numero).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe una mesa con ese número")
    mesa = Mesa(**data.model_dump())
    db.add(mesa)
    db.commit()
    db.refresh(mesa)
    return {"id": mesa.id, "numero": mesa.numero, "estado": mesa.estado.value}


@router.put("/{mesa_id}/estado")
def actualizar_estado_mesa(mesa_id: int, data: MesaUpdate, db: Session = Depends(get_db)):
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    if data.estado:
        mesa.estado = data.estado
    if data.capacidad:
        mesa.capacidad = data.capacidad
    if data.ubicacion:
        mesa.ubicacion = data.ubicacion
    db.commit()
    return {"ok": True, "estado": mesa.estado.value}


@router.delete("/{mesa_id}")
def eliminar_mesa(mesa_id: int, db: Session = Depends(get_db)):
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    mesa.activo = False
    db.commit()
    return {"ok": True}


@router.post("/configurar")
def configurar_mesas(cantidad: int, db: Session = Depends(get_db)):
    """Ajusta la cantidad total de mesas del restaurante."""
    if cantidad < 1 or cantidad > 100:
        raise HTTPException(status_code=400, detail="Cantidad debe ser entre 1 y 100")

    actuales = db.query(Mesa).filter(Mesa.activo == True).count()

    if cantidad > actuales:
        for i in range(actuales + 1, cantidad + 1):
            db.add(Mesa(numero=i, capacidad=4))
    elif cantidad < actuales:
        mesas_extra = db.query(Mesa).filter(
            Mesa.numero > cantidad, Mesa.activo == True
        ).all()
        for m in mesas_extra:
            m.activo = False

    db.commit()
    return {"ok": True, "mesas_activas": cantidad}


@router.post("/{mesa_id}/token-diario")
def renovar_token_diario_mesa(mesa_id: int, db: Session = Depends(get_db)):
    """Genera y persiste un token nuevo para la mesa para el día actual."""
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id, Mesa.activo == True).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    token = generar_token_diario_mesa(mesa.id)
    mesa.qr_token = token
    db.commit()
    return {
        "ok": True,
        "mesa_id": mesa.id,
        "numero": mesa.numero,
        "token": token,
        "fecha": date.today().isoformat(),
        "uso": "Se usa como QR de acceso del cliente para ese día. Cualquier token viejo queda inválido."
    }


@router.post("/{mesa_id}/liberar")
def liberar_mesa(mesa_id: int, data: dict | None = None, db: Session = Depends(get_db)):
    """Libera la mesa cuando el cliente se retira. Si hay pedido activo, solo se libera si se fuerza."""
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id, Mesa.activo == True).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    fuerza = bool((data or {}).get("forzar", False))
    pedido_abierto = db.query(Pedido).filter(
        Pedido.mesa_id == mesa.id,
        Pedido.estado.in_([
            EstadoPedido.pendiente,
            EstadoPedido.en_preparacion,
            EstadoPedido.listo,
        ])
    ).order_by(Pedido.created_at.desc()).first()

    if pedido_abierto and not fuerza:
        raise HTTPException(
            status_code=409,
            detail="Hay un pedido activo en la mesa. Debe forzar la liberación o cerrarlo antes."
        )

    if pedido_abierto and fuerza:
        pedido_abierto.estado = EstadoPedido.cancelado
        pedido_abierto.updated_at = date.today()

    mesa.estado = EstadoMesa.libre
    db.commit()
    return {
        "ok": True,
        "mesa_id": mesa.id,
        "numero": mesa.numero,
        "estado": mesa.estado.value,
        "forzado": fuerza,
        "mensaje": "La mesa quedó disponible para nuevo cliente."
    }
