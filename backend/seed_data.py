"""
Inicialización mínima de la base de datos.
Solo crea la configuración, las categorías vacías y las mesas.
El menú lo agrega el restaurante desde el panel Admin.
"""
from .models import Categoria, Producto, Mesa, ConfigRestaurante


CONFIG_INICIAL = [
    ("nombre",               "Mi Restaurante",     "Nombre del restaurante"),
    ("ruc",                  "",                   "RUC o NIT"),
    ("direccion",            "",                   "Dirección"),
    ("telefono",             "",                   "Teléfono"),
    ("moneda",               "$",                  "Pesos colombianos (COP)"),
    ("iva",                  "0.19",               "IVA 19%"),
    ("nequi",                "",                   "Número Nequi"),
    ("daviplata",            "",                   "Número Daviplata"),
    ("whatsapp",             "",                   "Número WhatsApp bot"),
    ("logo_url",             "",                   "URL del logo"),
    ("imagen_menu_url",      "",                   "URL imagen menú del día"),
    ("color_primario",       "#FF6B35",            "Color primario"),
    ("lat",                  "-12.0464",           "Latitud"),
    ("lon",                  "-77.0428",           "Longitud"),
    ("mensaje_bienvenida",   "¡Bienvenido! 🍽️ ¿En qué te puedo ayudar?", "Mensaje bienvenida WhatsApp"),
    ("gemini_api_key",       "",                   "Google Gemini API Key"),
    ("whatsapp_token",       "",                   "Meta WhatsApp Cloud API Token"),
    ("whatsapp_phone_id",    "",                   "Meta WhatsApp Phone ID"),
    ("whatsapp_verify_token","gormetpos2024",       "Meta Verify Token"),
]

# Categorías vacías — el dueño agrega sus propios platos desde Admin
CATEGORIAS = [
    # (nombre,                   emoji,  color,     orden)
    ("Entradas",                 "🥗",   "#00D4A1",  1),
    ("Sopas & Caldos",           "🍲",   "#FFB800",  2),
    ("Arepas & Antojos",         "🫓",   "#4FC3F7",  3),
    ("Platos Típicos",           "🍽️",   "#FF6B35",  4),
    ("Parrilla & Pollo",         "🍗",   "#FF8C00",  5),
    ("Menú del Día",             "🍱",   "#9C27B0",  6),
    ("Postres",                  "🍰",   "#E91E63",  7),
    ("Bebidas",                  "🥤",   "#03A9F4",  8),
    ("Desayunos Colombianos",    "🍳",   "#F4B400",  9),
    ("Almuerzos Corrientes",     "🍛",   "#8E44AD", 10),
    ("Cenas Colombianas",        "🌙",   "#34495E", 11),
]


def seed_database(db):
    """Crea solo la estructura base. El menú se agrega desde el Admin."""

    if db.query(ConfigRestaurante).count() == 0:
        for clave, valor, desc in CONFIG_INICIAL:
            db.add(ConfigRestaurante(clave=clave, valor=valor, descripcion=desc))
        db.flush()

    if db.query(Categoria).count() == 0:
        for nombre, emoji, color, orden in CATEGORIAS:
            db.add(Categoria(nombre=nombre, emoji=emoji, color=color, orden=orden, activo=True))
        db.flush()

    if db.query(Mesa).count() == 0:
        for num in range(1, 17):
            capacidad = 8 if num == 15 else (10 if num == 16 else 4)
            db.add(Mesa(numero=num, capacidad=capacidad))

    db.commit()
