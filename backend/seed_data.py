"""
Inicialización mínima de la base de datos.
Crea la configuración base, las categorías y una carta inicial útil para que
el POS y el menú del día funcionen desde el primer uso.
"""
from .models import Categoria, Producto, Mesa, ConfigRestaurante, SaludoVoz, ClienteSaludoVoz

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

SALUDOS_VOZ = [
    "Hola, qué alegría atenderte hoy. ¿Qué se te ofrece?",
    "Muy buenos días, bienvenida tu visita. ¿Qué vamos preparando?",
    "Hola, con mucho gusto te ayudo a pedir tu almuerzo.",
    "Qué gusto escucharte. Vamos a armar tu pedido con calma.",
    "Bienvenido, aquí estoy para atenderte. ¿Qué deseas disfrutar?",
    "Hola, será un placer servirte algo delicioso hoy.",
    "Muy buenos días, cuéntame qué se te antoja.",
    "Hola, vamos a escoger juntos una opción bien sabrosa.",
    "Qué bueno tenerte por aquí. ¿Comenzamos con el almuerzo?",
    "Bienvenido, te atiendo con mucho gusto y paciencia.",
    "Hola, dime qué deseas y yo te voy guiando paso a paso.",
    "Un saludo muy especial. ¿Te provoca un almuerzo corriente?",
    "Hola, qué gusto atenderte. Tenemos opciones deliciosas para ti.",
    "Bienvenido, revisemos primero nuestros almuerzos del día.",
    "Hola, aquí estoy lista para ayudarte a elegir.",
    "Muy buenos días, tomémonos el tiempo para preparar tu pedido.",
    "Qué alegría recibir tu pedido. ¿Qué te gustaría comer?",
    "Hola, con cariño vamos a preparar algo a tu gusto.",
    "Bienvenido a la casa. ¿Quieres que te ofrezca el almuerzo corriente?",
    "Hola, no hay afán. Te cuento nuestras opciones una por una.",
    "Qué gusto saludarte. Empecemos por lo más pedido de hoy.",
    "Bienvenido, estoy pendiente de cada detalle de tu pedido.",
    "Hola, vamos a encontrar una opción perfecta para ti.",
    "Muy buenos días, gracias por visitarnos. ¿Qué deseas ordenar?",
    "Hola, será un placer atenderte. Escoge con toda tranquilidad.",
    "Qué bueno escucharte. Primero tenemos almuerzos corrientes con complementos.",
    "Bienvenido, dime si prefieres algo casero, ejecutivo o especial.",
    "Hola, te acompaño con gusto mientras eliges tu comida.",
    "Un gusto atenderte. ¿Empezamos con sopa y plato fuerte?",
    "Hola, tenemos opciones para todos los gustos. ¿Qué deseas?",
    "Bienvenido, tu pedido merece toda nuestra atención.",
    "Qué alegría atenderte. Voy a leerte las opciones disponibles.",
    "Hola, aquí tienes una atención cercana y sin afanes.",
    "Muy buenos días, ¿te ofrezco primero nuestro almuerzo corriente?",
    "Bienvenido, puedes decirme o tocar la opción que prefieras.",
    "Hola, gracias por elegirnos. Vamos a preparar tu pedido.",
    "Qué gusto tenerte aquí. ¿Deseas algo ligero o un plato completo?",
    "Hola, estoy lista para ayudarte a escoger algo delicioso.",
    "Bienvenido, revisemos el menú en el orden que más te convenga.",
    "Un saludo con mucho cariño. ¿Qué te gustaría agregar?",
    "Hola, primero te presento nuestros almuerzos corrientes de hoy.",
    "Qué bueno verte por aquí. Puedes elegir con tranquilidad.",
    "Bienvenido, te escucho y ajustamos el pedido a tu gusto.",
    "Hola, vamos a preparar una comida rica y completa para ti.",
    "Muy buenos días, dime si deseas sopa, arroz y tus complementos.",
    "Hola, será un gusto tomar tu pedido de principio a fin.",
    "Bienvenido, yo te voy contando el precio de cada elección.",
    "Qué alegría saludarte. ¿Listo para escoger algo delicioso?",
    "Hola, gracias por venir. Comenzamos por los almuerzos corrientes.",
    "Bienvenido, no te preocupes, vamos paso a paso con tu pedido.",
]


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

    SaludoVoz.__table__.create(bind=db.bind, checkfirst=True)
    ClienteSaludoVoz.__table__.create(bind=db.bind, checkfirst=True)

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

    saludos_existentes = {saludo.texto for saludo in db.query(SaludoVoz).all()}
    for orden, texto in enumerate(SALUDOS_VOZ, start=1):
        if texto not in saludos_existentes:
            db.add(SaludoVoz(texto=texto, orden=orden, activo=True))

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
