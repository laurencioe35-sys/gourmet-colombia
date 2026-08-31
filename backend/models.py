from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum


class EstadoMesa(str, enum.Enum):
    libre = "libre"
    ocupada = "ocupada"
    cuenta = "cuenta"
    reservada = "reservada"


class EstadoPedido(str, enum.Enum):
    pendiente = "pendiente"
    en_preparacion = "en_preparacion"
    listo = "listo"
    entregado = "entregado"
    cancelado = "cancelado"


class MetodoPago(str, enum.Enum):
    efectivo = "efectivo"
    tarjeta = "tarjeta"
    yape = "yape"
    plin = "plin"
    nequi = "nequi"
    daviplata = "daviplata"


class CanalPedido(str, enum.Enum):
    pos = "pos"
    whatsapp = "whatsapp"
    delivery = "delivery"


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    emoji = Column(String(10), default="🍽️")
    color = Column(String(20), default="#FF6B35")
    orden = Column(Integer, default=0)
    activo = Column(Boolean, default=True)

    productos = relationship("Producto", back_populates="categoria")


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, default="")
    precio = Column(Float, nullable=False)
    emoji = Column(String(10), default="🍽️")
    imagen_url = Column(String(500), default="")
    disponible = Column(Boolean, default=True)
    destacado = Column(Boolean, default=False)
    tiempo_prep = Column(Integer, default=15)  # minutos

    categoria = relationship("Categoria", back_populates="productos")
    detalles = relationship("DetallePedido", back_populates="producto")


class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, nullable=False)
    capacidad = Column(Integer, default=4)
    estado = Column(SAEnum(EstadoMesa), default=EstadoMesa.libre)
    ubicacion = Column(String(50), default="Salon")
    activo = Column(Boolean, default=True)

    pedidos = relationship("Pedido", back_populates="mesa")


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    telefono = Column(String(20), unique=True, index=True)
    email = Column(String(150), default="")
    direccion = Column(String(300), default="")
    puntos_fidelidad = Column(Integer, default=0)
    total_pedidos = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    pedidos = relationship("Pedido", back_populates="cliente")
    conversaciones = relationship("ConversacionWhatsApp", back_populates="cliente")
    saludo_voz = relationship("ClienteSaludoVoz", back_populates="cliente", uselist=False, cascade="all, delete-orphan")


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    mesa_id = Column(Integer, ForeignKey("mesas.id"), nullable=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    estado = Column(SAEnum(EstadoPedido), default=EstadoPedido.pendiente)
    canal = Column(SAEnum(CanalPedido), default=CanalPedido.pos)
    subtotal = Column(Float, default=0.0)
    igv = Column(Float, default=0.0)
    descuento = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    metodo_pago = Column(SAEnum(MetodoPago), nullable=True)
    notas = Column(Text, default="")
    numero_ticket = Column(String(20), unique=True, nullable=True)
    prioridad = Column(String(10), default="normal")  # normal / alta / urgente
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cerrado_at = Column(DateTime, nullable=True)

    mesa = relationship("Mesa", back_populates="pedidos")
    cliente = relationship("Cliente", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")
    pago = relationship("Pago", back_populates="pedido", uselist=False)


class DetallePedido(Base):
    __tablename__ = "detalles_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    notas = Column(String(300), default="")
    estado = Column(String(20), default="pendiente")  # pendiente/listo
    created_at = Column(DateTime, default=datetime.utcnow)

    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles")


class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    monto = Column(Float, nullable=False)
    metodo = Column(SAEnum(MetodoPago), nullable=False)
    referencia = Column(String(100), default="")
    estado = Column(String(20), default="confirmado")
    created_at = Column(DateTime, default=datetime.utcnow)

    pedido = relationship("Pedido", back_populates="pago")


class SesionCaja(Base):
    __tablename__ = "sesiones_caja"

    id = Column(Integer, primary_key=True, index=True)
    monto_inicial = Column(Float, default=0.0)
    monto_final = Column(Float, nullable=True)
    total_ventas = Column(Float, default=0.0)
    total_efectivo = Column(Float, default=0.0)
    total_digital = Column(Float, default=0.0)
    estado = Column(String(20), default="abierta")  # abierta/cerrada
    abierta_por = Column(String(100), default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)
    cerrada_at = Column(DateTime, nullable=True)


class ConversacionWhatsApp(Base):
    __tablename__ = "conversaciones_whatsapp"

    id = Column(Integer, primary_key=True, index=True)
    telefono = Column(String(20), index=True)
    nombre = Column(String(150), default="Cliente")
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    estado_flujo = Column(String(50), default="inicio")
    datos_pedido_json = Column(Text, default="{}")
    ultimo_mensaje = Column(Text, default="")
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=True)
    activa = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="conversaciones")


class ConfigRestaurante(Base):
    __tablename__ = "config_restaurante"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(100), unique=True, nullable=False)
    valor = Column(Text, default="")
    descripcion = Column(String(300), default="")


class SaludoVoz(Base):
    __tablename__ = "saludos_voz"

    id = Column(Integer, primary_key=True, index=True)
    texto = Column(String(300), nullable=False, unique=True)
    activo = Column(Boolean, default=True)
    orden = Column(Integer, default=0)

    clientes = relationship("ClienteSaludoVoz", back_populates="saludo")


class ClienteSaludoVoz(Base):
    __tablename__ = "clientes_saludos_voz"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, unique=True)
    saludo_id = Column(Integer, ForeignKey("saludos_voz.id"), nullable=False)
    asignado_at = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="saludo_voz")
    saludo = relationship("SaludoVoz", back_populates="clientes")


class SolicitudPlan(Base):
    """Solicitud de suscripción creada antes de validar el pago manual."""
    __tablename__ = "solicitudes_plan"

    id = Column(Integer, primary_key=True, index=True)
    referencia = Column(String(32), unique=True, nullable=False, index=True)
    plan = Column(String(30), nullable=False)
    valor = Column(Float, nullable=False)
    estado = Column(String(20), default="pendiente")  # pendiente / reportado / aprobado
    nombre_negocio = Column(String(150), nullable=False)
    nit = Column(String(40), nullable=False)
    razon_social = Column(String(180), default="")
    responsable = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False)
    telefono = Column(String(30), nullable=False)
    direccion = Column(String(300), default="")
    ciudad = Column(String(100), default="")
    metodo_pago = Column(String(20), nullable=False)
    referencia_pago = Column(String(100), default="")
    acepta_terminos = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UsuarioGoogle(Base):
    __tablename__ = "usuarios_google"

    id = Column(Integer, primary_key=True, index=True)
    google_sub = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    nombre = Column(String(200), default="")
    foto_url = Column(String(500), default="")
    activo = Column(Boolean, default=True)
    solicitud_plan_id = Column(Integer, ForeignKey("solicitudes_plan.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    solicitud_plan = relationship("SolicitudPlan")


class UsuarioAdmin(Base):
    __tablename__ = "usuarios_admin"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    nombre = Column(String(150), default="Administrador")
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MensajeProgramado(Base):
    """Mensajes automáticos que se envían a todos los contactos en el horario configurado."""
    __tablename__ = "mensajes_programados"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)          # Ej: "Menú del almuerzo"
    tipo = Column(String(20), default="texto")            # texto / botones / menu
    mensaje = Column(Text, nullable=False)
    botones_json = Column(Text, default="[]")             # JSON lista de botones
    hora = Column(String(5), nullable=False)              # "11:30"
    dias = Column(String(50), default="lunes,martes,miercoles,jueves,viernes,sabado,domingo")
    activo = Column(Boolean, default=True)
    destinatarios = Column(String(20), default="todos")   # todos / nueva_lista
    ultimo_envio = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
