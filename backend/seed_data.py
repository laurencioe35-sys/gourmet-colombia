"""
Inicialización mínima de la base de datos.
Crea la configuración base, las categorías y una carta inicial útil para que
el POS y el menú del día funcionen desde el primer uso.
"""
from .models import Categoria, Producto, Mesa, ConfigRestaurante

DEFAULT_PRODUCTS = {
    "Entradas": [
        ("Ensalada Mixta", "Ensalada fresca con tomate, aguacate y queso", 12000, "🥗", 15),
        ("Tequeños", "6 tequeños con queso derretido", 13000, "🧀", 12),
    ],
    "Sopas & Caldos": [
        ("Sopa de Pollo", "Sopa casera con pollo, papa y vegetales", 15000, "🍲", 15),
        ("Ajiaco", "Ajiaco tradicional con pollo, papa, maíz y guascas", 18000, "🍛", 18),
    ],
    "Arepas & Antojos": [
        ("Arepa con Queso", "Arepa gratinada con queso fresco", 9000, "🫓", 10),
        ("Patacones", "Patacon con hogao y queso", 11000, "🥑", 12),
    ],
    "Platos Típicos": [
        ("Bandeja Paisa", "Carne, arroz, frijoles, huevo, arepa y aguacate", 28000, "🍽️", 25),
        ("Montería", "Grill de carne con yuca y ensalada", 30000, "🥩", 25),
    ],
    "Parrilla & Pollo": [
        ("Pollo Asado", "Pollo asado con papas y ensalada", 24000, "🍗", 20),
        ("Costilla BBQ", "Costilla a la parrilla con salsa barbecue", 32000, "🔥", 22),
    ],
    "Menú del Día": [
        ("Menú del Día Ejecutivo", "Plato del día del almuerzo con bebida", 16000, "🍱", 15),
        ("Menú Light", "Opción ligera con proteína y ensalada", 17000, "🥗", 15),
    ],
    "Postres": [
        ("Flan Casero", "Flan de leche con arequipe", 9000, "🍰", 8),
        ("Chocohelado", "Helado de chocolate con topping", 8000, "🍫", 7),
    ],
    "Bebidas": [
        ("Limonada Natural", "Limonada fresca con hielo", 5000, "🥤", 3),
        ("Gaseosa", "Vaso de gaseosa 400 ml", 4000, "🥤", 2),
    ],
    "Desayunos Colombianos": [
        ("Huevos con Arepa", "Huevos revueltos acompañados de arepa", 12000, "🍳", 12),
    ],
    "Almuerzos Corrientes": [
        ("Almuerzo Corriente", "Plato corriente de la casa", 18000, "🍛", 18),
    ],
    "Cenas Colombianas": [
        ("Cena Colombiana", "Cena típica del día con guarnición", 22000, "🌙", 18),
    ],
}


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
    """Crea la estructura base y un menú inicial funcional si aún no hay productos."""

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

    if db.query(Producto).count() == 0:
        categorias = {cat.nombre: cat for cat in db.query(Categoria).all()}
        for cat_name, products in DEFAULT_PRODUCTS.items():
            cat = categorias.get(cat_name)
            if not cat:
                continue
            for nombre, descripcion, precio, emoji, tiempo in products:
                db.add(Producto(
                    categoria_id=cat.id,
                    nombre=nombre,
                    descripcion=descripcion,
                    precio=float(precio),
                    emoji=emoji,
                    disponible=True,
                    destacado=False,
                    tiempo_prep=tiempo,
                ))

    db.commit()
