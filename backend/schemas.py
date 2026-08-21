from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class EstadoMesa(str, Enum):

    libre = "libre"
    ocupada = "ocupada"
    cuenta = "cuenta"
    reservada = "reservada"


class EstadoPedido(str, Enum):

    pendiente = "pendiente"
    en_preparacion = "en_preparacion"
    listo = "listo"
    entregado = "entregado"
    cancelado = "cancelado"


class MetodoPago(str, Enum):

    efectivo = "efectivo"
    tarjeta = "tarjeta"
    yape = "yape"
    plin = "plin"
    nequi = "nequi"
    daviplata = "daviplata"


class CanalPedido(str, Enum):

    pos = "pos"
    whatsapp = "whatsapp"
    delivery = "delivery"


# ============================================================
# SOLICITUD PLAN
# ============================================================

class SolicitudPlanCreate(BaseModel):

    plan: str

    nombre_negocio: str = Field(
        min_length=2,
        max_length=150
    )

    nit: str = Field(
        min_length=4,
        max_length=40
    )

    razon_social: str = ""

    responsable: str = Field(
        min_length=2,
        max_length=150
    )

    email: str = Field(
        min_length=5,
        max_length=150
    )

    telefono: str = Field(
        min_length=7,
        max_length=30
    )

    direccion: str = ""

    ciudad: str = ""

    metodo_pago: str

    referencia_pago: str = ""

    acepta_terminos: bool


# ============================================================
# CATEGORIA
# ============================================================

class CategoriaBase(BaseModel):

    nombre: str

    emoji: str = "🍽️"

    color: str = "#FF6B35"

    orden: int = 0


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):

    nombre: Optional[str] = None

    emoji: Optional[str] = None

    color: Optional[str] = None

    orden: Optional[int] = None

    activo: Optional[bool] = None


class CategoriaOut(CategoriaBase):

    id: int

    activo: bool

    class Config:
        from_attributes = True


# ============================================================
# PRODUCTO
# ============================================================

class ProductoBase(BaseModel):

    nombre: str

    descripcion: str = ""

    precio: float

    emoji: str = "🍽️"

    imagen_url: str = ""

    disponible: bool = True

    destacado: bool = False

    tiempo_prep: int = 15


class ProductoCreate(ProductoBase):

    categoria_id: int


class ProductoUpdate(BaseModel):

    nombre: Optional[str] = None

    descripcion: Optional[str] = None

    precio: Optional[float] = None

    emoji: Optional[str] = None

    imagen_url: Optional[str] = None

    disponible: Optional[bool] = None

    destacado: Optional[bool] = None

    tiempo_prep: Optional[int] = None

    categoria_id: Optional[int] = None


class ProductoOut(ProductoBase):

    id: int

    categoria_id: int

    categoria: Optional[CategoriaOut] = None

    class Config:
        from_attributes = True


# ============================================================
# MESA
# ============================================================

class MesaBase(BaseModel):

    numero: int

    capacidad: int = 4

    ubicacion: str = "Salon"


class MesaCreate(MesaBase):
    pass


class MesaUpdate(BaseModel):

    estado: Optional[EstadoMesa] = None

    capacidad: Optional[int] = None

    ubicacion: Optional[str] = None


class MesaOut(MesaBase):

    id: int

    estado: EstadoMesa

    activo: bool

    pedido_activo: Optional[Any] = None

    class Config:
        from_attributes = True


# ============================================================
# CLIENTE
# ============================================================

class ClienteBase(BaseModel):

    nombre: str

    telefono: str

    email: str = ""

    direccion: str = ""


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):

    nombre: Optional[str] = None

    email: Optional[str] = None

    direccion: Optional[str] = None

    puntos_fidelidad: Optional[int] = None


class ClienteOut(ClienteBase):

    id: int

    puntos_fidelidad: int

    total_pedidos: int

    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# DETALLE PEDIDO
# ============================================================

class DetalleCreate(BaseModel):

    producto_id: int

    cantidad: int = Field(
        default=1,
        ge=1
    )

    notas: str = ""


class DetalleUpdate(BaseModel):

    cantidad: Optional[int] = Field(
        default=None,
        ge=1
    )

    notas: Optional[str] = None

    estado: Optional[str] = None


class DetalleOut(BaseModel):

    id: int

    producto_id: int

    cantidad: int

    precio_unitario: float

    subtotal: float

    notas: str

    estado: str

    producto: Optional[ProductoOut] = None

    class Config:
        from_attributes = True


# ============================================================
# PEDIDO
# ============================================================

class PedidoCreate(BaseModel):

    mesa_id: Optional[int] = None

    cliente_id: Optional[int] = None

    canal: CanalPedido = CanalPedido.pos

    notas: str = ""


class PedidoUpdate(BaseModel):

    estado: Optional[EstadoPedido] = None

    notas: Optional[str] = None

    mesa_id: Optional[int] = None


class PagarPedido(BaseModel):

    metodo_pago: MetodoPago

    monto_recibido: Optional[float] = None

    referencia: str = ""

    descuento: float = Field(
        default=0.0,
        ge=0
    )


class PedidoOut(BaseModel):

    id: int

    mesa_id: Optional[int]

    cliente_id: Optional[int]

    estado: EstadoPedido

    canal: CanalPedido

    subtotal: float

    igv: float

    descuento: float

    total: float

    metodo_pago: Optional[MetodoPago]

    notas: str

    numero_ticket: Optional[str]

    created_at: datetime

    updated_at: datetime

    detalles: List[DetalleOut] = []

    mesa: Optional[MesaOut] = None

    cliente: Optional[ClienteOut] = None

    class Config:
        from_attributes = True


# ============================================================
# CAJA
# ============================================================

class AbrirCaja(BaseModel):

    monto_inicial: float

    abierta_por: str = "admin"


class CerrarCaja(BaseModel):

    monto_final: float


class SesionCajaOut(BaseModel):

    id: int

    monto_inicial: float

    monto_final: Optional[float]

    total_ventas: float

    total_efectivo: float

    total_digital: float

    estado: str

    abierta_por: str

    created_at: datetime

    cerrada_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================
# WHATSAPP
# ============================================================

class WhatsAppIncoming(BaseModel):

    telefono: str

    mensaje: str

    nombre: Optional[str] = "Cliente"

    tipo: str = "text"


class WhatsAppEnviar(BaseModel):

    telefono: str

    mensaje: str


class ConversacionOut(BaseModel):

    id: int

    telefono: str

    nombre: str

    estado_flujo: str

    ultimo_mensaje: str

    activa: bool

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# REPORTES
# ============================================================

class DashboardKPI(BaseModel):

    mesas_ocupadas: int

    mesas_libres: int

    pedidos_pendientes: int

    pedidos_cocina: int

    ventas_hoy: float

    ticket_promedio: float

    clientes_hoy: int

    total_pedidos_hoy: int


# ============================================================
# CONFIGURACIÓN
# ============================================================

class ConfigUpdate(BaseModel):

    valor: str


class ConfigOut(BaseModel):

    clave: str

    valor: str

    descripcion: str

    class Config:
        from_attributes = True