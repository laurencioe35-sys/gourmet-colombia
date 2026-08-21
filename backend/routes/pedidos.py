from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from ..database import get_db

from ..models import (
    Pedido,
    DetallePedido,
    Producto,
    Mesa,
    Cliente,
    Pago,
    EstadoPedido,
    EstadoMesa,
    SesionCaja,
)

from ..schemas import (
    PedidoCreate,
    PedidoUpdate,
    PedidoOut,
    DetalleCreate,
    DetalleUpdate,
    PagarPedido,
)


router = APIRouter()


# ============================================================
# CONFIGURACIÓN
# ============================================================

IVA = 0.19


# ============================================================
# RECALCULAR TOTALES
# ============================================================

def _recalcular_totales(
    pedido: Pedido,
    iva_rate: float = IVA
):
    """
    Recalcula subtotal, IVA y total del pedido.
    """

    subtotal = sum(
        float(d.subtotal or 0)
        for d in pedido.detalles
    )

    igv = round(
        subtotal * iva_rate,
        2
    )

    descuento = float(
        pedido.descuento or 0
    )

    total = round(
        subtotal + igv - descuento,
        2
    )

    pedido.subtotal = round(
        subtotal,
        2
    )

    pedido.igv = igv

    pedido.total = max(
        0,
        total
    )


# ============================================================
# GENERAR NÚMERO DE TICKET
# ============================================================

def _generar_ticket(
    db: Session
) -> str:

    total = db.query(Pedido).count()

    return (
        f"T-"
        f"{datetime.now().strftime('%Y%m%d')}-"
        f"{total + 1:04d}"
    )


# ============================================================
# LISTAR PEDIDOS
# ============================================================

@router.get(
    "/",
    response_model=List[PedidoOut]
)
def listar_pedidos(
    estado: Optional[str] = None,
    canal: Optional[str] = None,
    fecha: Optional[str] = None,
    db: Session = Depends(get_db)
):

    q = db.query(Pedido).options(

        joinedload(
            Pedido.detalles
        ).joinedload(
            DetallePedido.producto
        ),

        joinedload(
            Pedido.mesa
        ),

        joinedload(
            Pedido.cliente
        )
    )

    if estado:
        q = q.filter(
            Pedido.estado == estado
        )

    if canal:
        q = q.filter(
            Pedido.canal == canal
        )

    if fecha:
        try:

            d = datetime.strptime(
                fecha,
                "%Y-%m-%d"
            ).date()

            q = q.filter(
                Pedido.created_at >= datetime.combine(
                    d,
                    datetime.min.time()
                )
            )

            q = q.filter(
                Pedido.created_at <= datetime.combine(
                    d,
                    datetime.max.time()
                )
            )

        except ValueError:
            pass

    return (
        q
        .order_by(
            Pedido.created_at.desc()
        )
        .limit(200)
        .all()
    )


# ============================================================
# COCINA
# ============================================================

@router.get("/cocina")
def pedidos_cocina(
    db: Session = Depends(get_db)
):
    """
    Devuelve los pedidos pendientes,
    en preparación y listos para la cocina.
    """

    PRIO_ORDEN = {
        "urgente": 0,
        "alta": 1,
        "normal": 2
    }

    pedidos = (
        db.query(Pedido)
        .options(

            joinedload(
                Pedido.detalles
            ).joinedload(
                DetallePedido.producto
            ),

            joinedload(
                Pedido.mesa
            ),

            joinedload(
                Pedido.cliente
            )
        )
        .filter(
            Pedido.estado.in_([
                EstadoPedido.pendiente,
                EstadoPedido.en_preparacion,
                EstadoPedido.listo
            ])
        )
        .order_by(
            Pedido.created_at
        )
        .all()
    )

    pedidos.sort(
        key=lambda p: (
            PRIO_ORDEN.get(
                getattr(
                    p,
                    "prioridad",
                    "normal"
                ),
                2
            ),
            p.created_at
        )
    )

    resultado = []

    for p in pedidos:

        minutos = int(
            (
                datetime.utcnow() -
                p.created_at
            ).total_seconds() / 60
        )

        urgencia = (
            "verde"
            if minutos < 15
            else (
                "amarillo"
                if minutos < 30
                else "rojo"
            )
        )

        resultado.append({

            "id": p.id,

            "numero_ticket": p.numero_ticket,

            "mesa": (
                p.mesa.numero
                if p.mesa
                else None
            ),

            "cliente": (
                p.cliente.nombre
                if p.cliente
                else None
            ),

            "canal": p.canal.value,

            "estado": p.estado.value,

            "prioridad": (
                getattr(
                    p,
                    "prioridad",
                    "normal"
                )
                or "normal"
            ),

            "minutos": minutos,

            "urgencia": urgencia,

            "total": p.total,

            "notas": p.notas,

            "items": [

                {
                    "id": d.id,

                    "nombre": (
                        d.producto.nombre
                        if d.producto
                        else "Producto"
                    ),

                    "emoji": (
                        d.producto.emoji
                        if d.producto
                        else "🍽️"
                    ),

                    "cantidad": d.cantidad,

                    "notas": d.notas,

                    "estado": d.estado
                }

                for d in p.detalles
            ]
        })

    return resultado


# ============================================================
# CAMBIAR PRIORIDAD
# ============================================================

@router.put("/{pedido_id}/prioridad")
def cambiar_prioridad(
    pedido_id: int,
    body: dict,
    db: Session = Depends(get_db)
):

    pedido = (
        db.query(Pedido)
        .filter(
            Pedido.id == pedido_id
        )
        .first()
    )

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    nivel = body.get(
        "prioridad",
        "normal"
    )

    if nivel not in (
        "normal",
        "alta",
        "urgente"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "prioridad debe ser "
                "normal|alta|urgente"
            )
        )

    pedido.prioridad = nivel

    db.commit()

    return {
        "ok": True,
        "prioridad": nivel
    }


# ============================================================
# OBTENER PEDIDO COMPLETO
# ============================================================

@router.get(
    "/{pedido_id}",
    response_model=PedidoOut
)
def obtener_pedido(
    pedido_id: int,
    db: Session = Depends(get_db)
):

    pedido = (
        db.query(Pedido)
        .options(

            joinedload(
                Pedido.detalles
            )
            .joinedload(
                DetallePedido.producto
            )
            .joinedload(
                Producto.categoria
            ),

            joinedload(
                Pedido.mesa
            ),

            joinedload(
                Pedido.cliente
            )
        )
        .filter(
            Pedido.id == pedido_id
        )
        .first()
    )

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    return pedido


# ============================================================
# CREAR PEDIDO
# ============================================================

@router.post(
    "/",
    response_model=PedidoOut
)
def crear_pedido(
    data: PedidoCreate,
    db: Session = Depends(get_db)
):

    if data.mesa_id:

        mesa = (
            db.query(Mesa)
            .filter(
                Mesa.id == data.mesa_id
            )
            .first()
        )

        if not mesa:
            raise HTTPException(
                status_code=404,
                detail="Mesa no encontrada"
            )

        mesa.estado = EstadoMesa.ocupada

    pedido = Pedido(
        mesa_id=data.mesa_id,
        cliente_id=data.cliente_id,
        canal=data.canal,
        notas=data.notas,
        numero_ticket=_generar_ticket(db)
    )

    db.add(pedido)

    db.commit()

    db.refresh(pedido)

    return pedido


# ============================================================
# AGREGAR ITEM AL PEDIDO
# ============================================================

@router.post("/{pedido_id}/items")
def agregar_item(
    pedido_id: int,
    data: DetalleCreate,
    db: Session = Depends(get_db)
):

    pedido = (
        db.query(Pedido)
        .options(
            joinedload(
                Pedido.detalles
            )
        )
        .filter(
            Pedido.id == pedido_id
        )
        .first()
    )

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    if pedido.estado in [
        EstadoPedido.entregado,
        EstadoPedido.cancelado
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "No se puede modificar "
                "un pedido cerrado"
            )
        )

    if data.cantidad < 1:
        raise HTTPException(
            status_code=400,
            detail="La cantidad debe ser mayor que 0"
        )

    producto = (
        db.query(Producto)
        .filter(
            Producto.id == data.producto_id
        )
        .first()
    )

    if not producto:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado"
        )

    detalle = DetallePedido(
        pedido_id=pedido_id,
        producto_id=data.producto_id,
        cantidad=data.cantidad,
        precio_unitario=producto.precio,
        subtotal=round(
            producto.precio * data.cantidad,
            2
        ),
        notas=data.notas
    )

    pedido.detalles.append(detalle)

    db.flush()

    _recalcular_totales(
        pedido
    )

    db.commit()

    db.refresh(pedido)

    return {

        "ok": True,

        "detalle_id": detalle.id,

        "subtotal": pedido.subtotal,

        "igv": pedido.igv,

        "total": pedido.total
    }


# ============================================================
# ACTUALIZAR ITEM
# ============================================================

@router.put(
    "/{pedido_id}/items/{detalle_id}"
)
def actualizar_item(
    pedido_id: int,
    detalle_id: int,
    data: DetalleUpdate,
    db: Session = Depends(get_db)
):

    detalle = (
        db.query(DetallePedido)
        .filter(
            DetallePedido.id == detalle_id,
            DetallePedido.pedido_id == pedido_id
        )
        .first()
    )

    if not detalle:
        raise HTTPException(
            status_code=404,
            detail="Item no encontrado"
        )

    if data.cantidad is not None:

        if data.cantidad < 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "La cantidad debe "
                    "ser mayor que 0"
                )
            )

        detalle.cantidad = data.cantidad

        detalle.subtotal = round(
            detalle.precio_unitario *
            data.cantidad,
            2
        )

    if data.notas is not None:
        detalle.notas = data.notas

    if data.estado is not None:
        detalle.estado = data.estado

    pedido = (
        db.query(Pedido)
        .options(
            joinedload(
                Pedido.detalles
            )
        )
        .filter(
            Pedido.id == pedido_id
        )
        .first()
    )

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    _recalcular_totales(
        pedido
    )

    db.commit()

    return {
        "ok": True,
        "total": pedido.total
    }


# ============================================================
# ELIMINAR ITEM
# ============================================================

@router.delete(
    "/{pedido_id}/items/{detalle_id}"
)
def eliminar_item(
    pedido_id: int,
    detalle_id: int,
    db: Session = Depends(get_db)
):

    detalle = (
        db.query(DetallePedido)
        .filter(
            DetallePedido.id == detalle_id,
            DetallePedido.pedido_id == pedido_id
        )
        .first()
    )

    if not detalle:
        raise HTTPException(
            status_code=404,
            detail="Item no encontrado"
        )

    pedido = (
        db.query(Pedido)
        .options(
            joinedload(
                Pedido.detalles
            )
        )
        .filter(
            Pedido.id == pedido_id
        )
        .first()
    )

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    db.delete(detalle)

    db.flush()

    _recalcular_totales(
        pedido
    )

    db.commit()

    return {
        "ok": True,
        "total": pedido.total
    }


# ============================================================
# CAMBIAR ESTADO DEL PEDIDO
# ============================================================

@router.put(
    "/{pedido_id}/estado"
)
def cambiar_estado(
    pedido_id: int,
    data: PedidoUpdate,
    db: Session = Depends(get_db)
):

    pedido = (
        db.query(Pedido)
        .filter(
            Pedido.id == pedido_id
        )
        .first()
    )

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    if data.estado:
        pedido.estado = data.estado

    if data.notas is not None:
        pedido.notas = data.notas

    if data.mesa_id is not None:
        pedido.mesa_id = data.mesa_id

    pedido.updated_at = datetime.utcnow()

    db.commit()

    return {
        "ok": True,
        "estado": pedido.estado.value
    }


# ============================================================
# PAGAR PEDIDO
# ============================================================

@router.post(
    "/{pedido_id}/pagar"
)
def pagar_pedido(
    pedido_id: int,
    data: PagarPedido,
    db: Session = Depends(get_db)
):

    pedido = (
        db.query(Pedido)
        .options(

            joinedload(
                Pedido.detalles
            ).joinedload(
                DetallePedido.producto
            ),

            joinedload(
                Pedido.mesa
            ),

            joinedload(
                Pedido.cliente
            )
        )
        .filter(
            Pedido.id == pedido_id
        )
        .first()
    )

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    if pedido.estado == EstadoPedido.entregado:
        raise HTTPException(
            status_code=400,
            detail="Pedido ya pagado"
        )

    if not pedido.detalles:
        raise HTTPException(
            status_code=400,
            detail="No se puede cobrar un pedido vacío"
        )

    # --------------------------------------------------------
    # DESCUENTO
    # --------------------------------------------------------

    descuento = float(
        data.descuento or 0
    )

    if descuento < 0:
        descuento = 0

    pedido.descuento = descuento

    _recalcular_totales(
        pedido
    )

    # --------------------------------------------------------
    # MÉTODO DE PAGO
    # --------------------------------------------------------

    pedido.metodo_pago = data.metodo_pago

    pedido.estado = EstadoPedido.entregado

    pedido.cerrado_at = datetime.utcnow()

    pedido.updated_at = datetime.utcnow()

    # --------------------------------------------------------
    # PAGO
    # --------------------------------------------------------

    pago = Pago(
        pedido_id=pedido_id,
        monto=pedido.total,
        metodo=data.metodo_pago,
        referencia=data.referencia,
        estado="confirmado"
    )

    db.add(pago)

    # --------------------------------------------------------
    # LIBERAR MESA
    # --------------------------------------------------------

    if pedido.mesa:
        pedido.mesa.estado = EstadoMesa.libre

    # --------------------------------------------------------
    # ACTUALIZAR CLIENTE
    # --------------------------------------------------------

    if pedido.cliente_id:

        cliente = (
            db.query(Cliente)
            .filter(
                Cliente.id == pedido.cliente_id
            )
            .first()
        )

        if cliente:

            cliente.total_pedidos += 1

            puntos = int(
                pedido.total / 10
            )

            cliente.puntos_fidelidad += puntos

    # --------------------------------------------------------
    # ACTUALIZAR CAJA
    # --------------------------------------------------------

    sesion = (
        db.query(SesionCaja)
        .filter(
            SesionCaja.estado == "abierta"
        )
        .first()
    )

    if sesion:

        sesion.total_ventas += pedido.total

        if data.metodo_pago.value == "efectivo":

            sesion.total_efectivo += (
                pedido.total
            )

        else:

            sesion.total_digital += (
                pedido.total
            )

    # --------------------------------------------------------
    # GUARDAR TODO
    # --------------------------------------------------------

    db.commit()

    db.refresh(pedido)

    # --------------------------------------------------------
    # CALCULAR VUELTO
    # --------------------------------------------------------

    vuelto = 0

    if (
        data.monto_recibido is not None
        and
        data.metodo_pago.value == "efectivo"
    ):

        vuelto = round(
            data.monto_recibido -
            pedido.total,
            2
        )

        if vuelto < 0:
            vuelto = 0

    # --------------------------------------------------------
    # DETALLES PARA FACTURA / TICKET
    # --------------------------------------------------------

    detalles_factura = []

    for detalle in pedido.detalles:

        detalles_factura.append({

            "id": detalle.id,

            "producto_id": detalle.producto_id,

            "nombre": (
                detalle.producto.nombre
                if detalle.producto
                else "Producto"
            ),

            "emoji": (
                detalle.producto.emoji
                if detalle.producto
                else "🍽️"
            ),

            "cantidad": detalle.cantidad,

            "precio_unitario": float(
                detalle.precio_unitario or 0
            ),

            "subtotal": float(
                detalle.subtotal or 0
            ),

            "notas": detalle.notas or ""
        })

    # --------------------------------------------------------
    # INFORMACIÓN DEL CLIENTE
    # --------------------------------------------------------

    cliente_info = None

    if pedido.cliente:

        cliente_info = {

            "id": pedido.cliente.id,

            "nombre": pedido.cliente.nombre,

            "telefono": pedido.cliente.telefono,

            "email": pedido.cliente.email,

            "direccion": pedido.cliente.direccion
        }

    # --------------------------------------------------------
    # RESPUESTA
    # --------------------------------------------------------

    return {

        "ok": True,

        "ticket": pedido.numero_ticket,

        "pedido_id": pedido.id,

        "mesa": (
            pedido.mesa.numero
            if pedido.mesa
            else None
        ),

        "canal": pedido.canal.value,

        "cliente": cliente_info,

        "detalles": detalles_factura,

        "subtotal": pedido.subtotal,

        "igv": pedido.igv,

        "descuento": pedido.descuento,

        "total": pedido.total,

        "metodo": data.metodo_pago.value,

        "monto_recibido": data.monto_recibido,

        "vuelto": vuelto,

        "fecha": pedido.created_at.isoformat()
        if pedido.created_at
        else datetime.utcnow().isoformat()
    }


# ============================================================
# MARCAR ITEM COMO LISTO
# ============================================================

@router.put(
    "/{pedido_id}/items/{detalle_id}/listo"
)
def marcar_item_listo(
    pedido_id: int,
    detalle_id: int,
    db: Session = Depends(get_db)
):

    detalle = (
        db.query(DetallePedido)
        .filter(
            DetallePedido.id == detalle_id,
            DetallePedido.pedido_id == pedido_id
        )
        .first()
    )

    if not detalle:
        raise HTTPException(
            status_code=404,
            detail="Item no encontrado"
        )

    detalle.estado = "listo"

    db.commit()

    # --------------------------------------------------------
    # COMPROBAR SI TODOS LOS ITEMS ESTÁN LISTOS
    # --------------------------------------------------------

    pedido = (
        db.query(Pedido)
        .options(
            joinedload(
                Pedido.detalles
            )
        )
        .filter(
            Pedido.id == pedido_id
        )
        .first()
    )

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    todos_listos = (
        len(pedido.detalles) > 0
        and all(
            d.estado == "listo"
            for d in pedido.detalles
        )
    )

    if todos_listos:

        pedido.estado = EstadoPedido.listo

        pedido.updated_at = datetime.utcnow()

        db.commit()

    return {

        "ok": True,

        "todos_listos": todos_listos

    }