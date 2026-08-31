from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Pedido, DetallePedido, Producto, Mesa, Cliente, EstadoPedido

router = APIRouter()


@router.get("/dashboard")
def dashboard_kpis(db: Session = Depends(get_db)):
    hoy = datetime.utcnow().date()
    inicio_hoy = datetime.combine(hoy, datetime.min.time())

    mesas = db.query(Mesa).filter(Mesa.activo == True).all()
    mesas_ocupadas = 0
    mesas_libres = 0

    for mesa in mesas:
        pedido_activo = db.query(Pedido).filter(
            Pedido.mesa_id == mesa.id,
            Pedido.estado.in_([EstadoPedido.pendiente, EstadoPedido.en_preparacion, EstadoPedido.listo])
        ).order_by(Pedido.created_at.desc()).first()

        if pedido_activo is None:
            mesas_libres += 1
        else:
            mesas_ocupadas += 1

    pedidos_hoy = db.query(Pedido).filter(
        Pedido.created_at >= inicio_hoy,
        Pedido.estado == EstadoPedido.entregado
    ).all()

    pedidos_pendientes = db.query(Pedido).filter(
        Pedido.estado == EstadoPedido.pendiente
    ).count()

    pedidos_cocina = db.query(Pedido).filter(
        Pedido.estado.in_([EstadoPedido.pendiente, EstadoPedido.en_preparacion])
    ).count()

    ventas_hoy = sum(p.total for p in pedidos_hoy)
    ticket_prom = round(ventas_hoy / len(pedidos_hoy), 2) if pedidos_hoy else 0

    clientes_hoy = db.query(Pedido).filter(
        Pedido.created_at >= inicio_hoy,
        Pedido.cliente_id.isnot(None)
    ).distinct(Pedido.cliente_id).count()

    return {
        "mesas_ocupadas": mesas_ocupadas,
        "mesas_libres": mesas_libres,
        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_cocina": pedidos_cocina,
        "ventas_hoy": round(ventas_hoy, 2),
        "ticket_promedio": ticket_prom,
        "clientes_hoy": clientes_hoy,
        "total_pedidos_hoy": len(pedidos_hoy),
    }


@router.get("/ventas")
def reporte_ventas(
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Pedido).filter(Pedido.estado == EstadoPedido.entregado)

    if desde:
        q = q.filter(Pedido.created_at >= datetime.fromisoformat(desde))
    if hasta:
        q = q.filter(Pedido.created_at <= datetime.fromisoformat(hasta))

    pedidos = q.order_by(Pedido.created_at.desc()).limit(500).all()

    return [
        {
            "id": p.id,
            "ticket": p.numero_ticket,
            "mesa": p.mesa.numero if p.mesa else None,
            "canal": p.canal.value,
            "subtotal": p.subtotal,
            "igv": p.igv,
            "descuento": p.descuento,
            "total": p.total,
            "metodo_pago": p.metodo_pago.value if p.metodo_pago else None,
            "fecha": p.created_at.isoformat(),
            "items": len(p.detalles),
        }
        for p in pedidos
    ]


@router.get("/productos-top")
def productos_top(
    limite: int = 10,
    desde: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(
        Producto.nombre,
        Producto.emoji,
        func.sum(DetallePedido.cantidad).label("total_vendido"),
        func.sum(DetallePedido.subtotal).label("total_ingresos")
    ).join(DetallePedido).join(Pedido).filter(
        Pedido.estado == EstadoPedido.entregado
    )

    if desde:
        q = q.filter(Pedido.created_at >= datetime.fromisoformat(desde))

    resultado = q.group_by(Producto.id).order_by(
        func.sum(DetallePedido.cantidad).desc()
    ).limit(limite).all()

    return [
        {
            "nombre": r.nombre,
            "emoji": r.emoji,
            "total_vendido": int(r.total_vendido or 0),
            "total_ingresos": round(float(r.total_ingresos or 0), 2),
        }
        for r in resultado
    ]


@router.get("/metodos-pago")
def reporte_metodos_pago(
    desde: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(
        Pedido.metodo_pago,
        func.count(Pedido.id).label("cantidad"),
        func.sum(Pedido.total).label("total")
    ).filter(Pedido.estado == EstadoPedido.entregado)

    if desde:
        q = q.filter(Pedido.created_at >= datetime.fromisoformat(desde))

    resultado = q.group_by(Pedido.metodo_pago).all()

    return [
        {
            "metodo": r.metodo_pago.value if r.metodo_pago else "sin_pago",
            "cantidad": int(r.cantidad),
            "total": round(float(r.total or 0), 2),
        }
        for r in resultado
    ]


@router.get("/ventas-por-hora")
def ventas_por_hora(fecha: Optional[str] = None, db: Session = Depends(get_db)):
    if fecha:
        d = datetime.fromisoformat(fecha).date()
    else:
        d = datetime.utcnow().date()

    inicio = datetime.combine(d, datetime.min.time())
    fin = datetime.combine(d, datetime.max.time())

    pedidos = db.query(Pedido).filter(
        Pedido.estado == EstadoPedido.entregado,
        Pedido.created_at >= inicio,
        Pedido.created_at <= fin,
    ).all()

    por_hora = {}
    for p in pedidos:
        hora = p.created_at.hour
        if hora not in por_hora:
            por_hora[hora] = {"pedidos": 0, "total": 0}
        por_hora[hora]["pedidos"] += 1
        por_hora[hora]["total"] += p.total

    return [
        {"hora": f"{h:02d}:00", "pedidos": v["pedidos"], "total": round(v["total"], 2)}
        for h, v in sorted(por_hora.items())
    ]


@router.get("/exportar-excel")
def exportar_excel(
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Genera y retorna datos para Excel."""
    try:
        import pandas as pd
        from io import BytesIO
        from fastapi.responses import StreamingResponse

        q = db.query(Pedido).options(
            joinedload(Pedido.detalles).joinedload(DetallePedido.producto),
            joinedload(Pedido.cliente)
        ).filter(Pedido.estado == EstadoPedido.entregado)

        if desde:
            q = q.filter(Pedido.created_at >= datetime.fromisoformat(desde))
        if hasta:
            q = q.filter(Pedido.created_at <= datetime.fromisoformat(hasta))

        pedidos = q.all()

        filas = []
        for p in pedidos:
            for d in p.detalles:
                filas.append({
                    "Ticket": p.numero_ticket,
                    "Fecha": p.created_at.strftime("%Y-%m-%d %H:%M"),
                    "Mesa": p.mesa.numero if p.mesa else "WhatsApp",
                    "Canal": p.canal.value,
                    "Cliente": p.cliente.nombre if p.cliente else "",
                    "Producto": d.producto.nombre if d.producto else "",
                    "Cantidad": d.cantidad,
                    "Precio Unit.": d.precio_unitario,
                    "Subtotal Item": d.subtotal,
                    "Total Pedido": p.total,
                    "Metodo Pago": p.metodo_pago.value if p.metodo_pago else "",
                })

        df = pd.DataFrame(filas)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Ventas Detalladas", index=False)

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=reporte_ventas.xlsx"}
        )
    except ImportError:
        return {"error": "pandas y openpyxl son requeridos para exportar"}
