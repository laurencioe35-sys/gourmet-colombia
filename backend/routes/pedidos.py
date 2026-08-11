from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date
from ..database import get_db
from ..models import (
    Pedido, DetallePedido, Producto, Mesa, Cliente, Pago,
    EstadoPedido, EstadoMesa, SesionCaja
)
from ..schemas import (
    PedidoCreate, PedidoUpdate, PedidoOut,
    DetalleCreate, DetalleUpdate, PagarPedido
)

router = APIRouter()

IVA = 0.19


def _recalcular_totales(pedido: Pedido, iva_rate: float = IVA):
    subtotal = sum(d.subtotal for d in pedido.detalles)
    igv = round(subtotal * iva_rate, 2)
    pedido.subtotal = round(subtotal, 2)
    pedido.igv = igv
    pedido.total = round(subtotal + igv - pedido.descuento, 2)


def _generar_ticket(db: Session) -> str:
    total = db.query(Pedido).count()
    return f"T-{datetime.now().strftime('%Y%m%d')}-{total + 1:04d}"


@router.get("/", response_model=List[PedidoOut])
def listar_pedidos(
    estado: Optional[str] = None,
    canal: Optional[str] = None,
    fecha: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Pedido).options(
        joinedload(Pedido.detalles).joinedload(DetallePedido.producto),
        joinedload(Pedido.mesa),
        joinedload(Pedido.cliente)
    )
    if estado:
        q = q.filter(Pedido.estado == estado)
    if canal:
        q = q.filter(Pedido.canal == canal)
    if fecha:
        try:
            d = datetime.strptime(fecha, "%Y-%m-%d").date()
            q = q.filter(Pedido.created_at >= datetime.combine(d, datetime.min.time()))
            q = q.filter(Pedido.created_at <= datetime.combine(d, datetime.max.time()))
        except ValueError:
            pass
    return q.order_by(Pedido.created_at.desc()).limit(200).all()


@router.get("/cocina")
def pedidos_cocina(db: Session = Depends(get_db)):
    """Pedidos pendientes, en preparación y listos — agrupados para la pantalla de cocina."""
    PRIO_ORDEN = {"urgente": 0, "alta": 1, "normal": 2}

    pedidos = db.query(Pedido).options(
        joinedload(Pedido.detalles).joinedload(DetallePedido.producto),
        joinedload(Pedido.mesa),
        joinedload(Pedido.cliente)
    ).filter(
        Pedido.estado.in_([EstadoPedido.pendiente, EstadoPedido.en_preparacion, EstadoPedido.listo])
    ).order_by(Pedido.created_at).all()

    # Ordenar: primero por prioridad, luego por tiempo
    pedidos.sort(key=lambda p: (PRIO_ORDEN.get(getattr(p, "prioridad", "normal"), 2), p.created_at))

    resultado = []
    for p in pedidos:
        minutos = int((datetime.utcnow() - p.created_at).total_seconds() / 60)
        urgencia = "verde" if minutos < 15 else ("amarillo" if minutos < 30 else "rojo")
        resultado.append({
            "id":            p.id,
            "numero_ticket": p.numero_ticket,
            "mesa":          p.mesa.numero if p.mesa else None,
            "cliente":       p.cliente.nombre if p.cliente else None,
            "canal":         p.canal.value,
            "estado":        p.estado.value,
            "prioridad":     getattr(p, "prioridad", "normal") or "normal",
            "minutos":       minutos,
            "urgencia":      urgencia,
            "total":         p.total,
            "notas":         p.notas,
            "items": [
                {
                    "id":       d.id,
                    "nombre":   d.producto.nombre if d.producto else "?",
                    "emoji":    d.producto.emoji  if d.producto else "🍽️",
                    "cantidad": d.cantidad,
                    "notas":    d.notas,
                    "estado":   d.estado,
                }
                for d in p.detalles
            ]
        })
    return resultado


@router.put("/{pedido_id}/prioridad")
def cambiar_prioridad(pedido_id: int, body: dict, db: Session = Depends(get_db)):
    """Cambia la prioridad de un pedido: normal / alta / urgente."""
    p = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    nivel = body.get("prioridad", "normal")
    if nivel not in ("normal", "alta", "urgente"):
        raise HTTPException(status_code=400, detail="prioridad debe ser normal|alta|urgente")
    p.prioridad = nivel
    db.commit()
    return {"ok": True, "prioridad": nivel}


@router.get("/{pedido_id}", response_model=PedidoOut)
def obtener_pedido(pedido_id: int, db: Session = Depends(get_db)):
    p = db.query(Pedido).options(
        joinedload(Pedido.detalles).joinedload(DetallePedido.producto).joinedload(Producto.categoria),
        joinedload(Pedido.mesa),
        joinedload(Pedido.cliente)
    ).filter(Pedido.id == pedido_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return p


@router.post("/", response_model=PedidoOut)
def crear_pedido(data: PedidoCreate, db: Session = Depends(get_db)):
    if data.mesa_id:
        mesa = db.query(Mesa).filter(Mesa.id == data.mesa_id).first()
        if not mesa:
            raise HTTPException(status_code=404, detail="Mesa no encontrada")
        mesa.estado = EstadoMesa.ocupada

    pedido = Pedido(
        mesa_id=data.mesa_id,
        cliente_id=data.cliente_id,
        canal=data.canal,
        notas=data.notas,
        numero_ticket=_generar_ticket(db),
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido


@router.post("/{pedido_id}/items")
def agregar_item(pedido_id: int, data: DetalleCreate, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).options(joinedload(Pedido.detalles)).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.estado in [EstadoPedido.entregado, EstadoPedido.cancelado]:
        raise HTTPException(status_code=400, detail="No se puede modificar un pedido cerrado")

    producto = db.query(Producto).filter(Producto.id == data.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    detalle = DetallePedido(
        pedido_id=pedido_id,
        producto_id=data.producto_id,
        cantidad=data.cantidad,
        precio_unitario=producto.precio,
        subtotal=round(producto.precio * data.cantidad, 2),
        notas=data.notas,
    )
    db.add(detalle)
    db.flush()

    pedido.detalles.append(detalle)
    _recalcular_totales(pedido)
    db.commit()
    db.refresh(pedido)

    return {
        "ok": True,
        "detalle_id": detalle.id,
        "subtotal": pedido.subtotal,
        "igv": pedido.igv,
        "total": pedido.total,
    }


@router.put("/{pedido_id}/items/{detalle_id}")
def actualizar_item(pedido_id: int, detalle_id: int, data: DetalleUpdate, db: Session = Depends(get_db)):
    detalle = db.query(DetallePedido).filter(
        DetallePedido.id == detalle_id,
        DetallePedido.pedido_id == pedido_id
    ).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    if data.cantidad is not None:
        detalle.cantidad = data.cantidad
        detalle.subtotal = round(detalle.precio_unitario * data.cantidad, 2)
    if data.notas is not None:
        detalle.notas = data.notas
    if data.estado is not None:
        detalle.estado = data.estado

    pedido = db.query(Pedido).options(joinedload(Pedido.detalles)).filter(Pedido.id == pedido_id).first()
    _recalcular_totales(pedido)
    db.commit()
    return {"ok": True, "total": pedido.total}


@router.delete("/{pedido_id}/items/{detalle_id}")
def eliminar_item(pedido_id: int, detalle_id: int, db: Session = Depends(get_db)):
    detalle = db.query(DetallePedido).filter(
        DetallePedido.id == detalle_id,
        DetallePedido.pedido_id == pedido_id
    ).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    db.delete(detalle)
    db.flush()

    pedido = db.query(Pedido).options(joinedload(Pedido.detalles)).filter(Pedido.id == pedido_id).first()
    _recalcular_totales(pedido)
    db.commit()
    return {"ok": True, "total": pedido.total}


@router.put("/{pedido_id}/estado")
def cambiar_estado(pedido_id: int, data: PedidoUpdate, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if data.estado:
        pedido.estado = data.estado
    if data.notas is not None:
        pedido.notas = data.notas
    pedido.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "estado": pedido.estado.value}


@router.post("/{pedido_id}/pagar")
def pagar_pedido(pedido_id: int, data: PagarPedido, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).options(
        joinedload(Pedido.detalles),
        joinedload(Pedido.mesa)
    ).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.estado == EstadoPedido.entregado:
        raise HTTPException(status_code=400, detail="Pedido ya pagado")

    if data.descuento > 0:
        pedido.descuento = data.descuento
        _recalcular_totales(pedido)

    pedido.metodo_pago = data.metodo_pago
    pedido.estado = EstadoPedido.entregado
    pedido.cerrado_at = datetime.utcnow()
    pedido.updated_at = datetime.utcnow()

    pago = Pago(
        pedido_id=pedido_id,
        monto=pedido.total,
        metodo=data.metodo_pago,
        referencia=data.referencia,
        estado="confirmado",
    )
    db.add(pago)

    if pedido.mesa:
        pedido.mesa.estado = EstadoMesa.libre

    if pedido.cliente_id:
        from ..models import Cliente
        cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()
        if cliente:
            cliente.total_pedidos += 1
            puntos = int(pedido.total / 10)
            cliente.puntos_fidelidad += puntos

    sesion = db.query(SesionCaja).filter(SesionCaja.estado == "abierta").first()
    if sesion:
        sesion.total_ventas += pedido.total
        if data.metodo_pago.value == "efectivo":
            sesion.total_efectivo += pedido.total
        else:
            sesion.total_digital += pedido.total

    db.commit()

    vuelto = 0
    if data.monto_recibido and data.metodo_pago.value == "efectivo":
        vuelto = round(data.monto_recibido - pedido.total, 2)

    return {
        "ok": True,
        "ticket": pedido.numero_ticket,
        "total": pedido.total,
        "metodo": data.metodo_pago.value,
        "vuelto": vuelto,
    }


@router.put("/{pedido_id}/items/{detalle_id}/listo")
def marcar_item_listo(pedido_id: int, detalle_id: int, db: Session = Depends(get_db)):
    detalle = db.query(DetallePedido).filter(
        DetallePedido.id == detalle_id,
        DetallePedido.pedido_id == pedido_id
    ).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    detalle.estado = "listo"
    db.commit()

    pedido = db.query(Pedido).options(joinedload(Pedido.detalles)).filter(Pedido.id == pedido_id).first()
    todos_listos = all(d.estado == "listo" for d in pedido.detalles)
    if todos_listos:
        pedido.estado = EstadoPedido.listo
        db.commit()

    return {"ok": True, "todos_listos": todos_listos}
