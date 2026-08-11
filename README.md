# 🍽️ GourmetPOS ERP v2.0 — Sistema Profesional para Restaurantes

**Backend FastAPI + Frontend Web + Bot WhatsApp con 10 Prompts IA**

---

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias (solo la primera vez)
instalar_dependencias.bat

# 2. Iniciar el sistema
start.bat
```

El sistema abre automáticamente en `http://localhost:8000`

---

## 🏗️ Arquitectura del Sistema

```
GORMET POS/
├── backend/                    ← API REST (FastAPI + SQLite)
│   ├── main.py                 ← Servidor principal + WebSocket
│   ├── database.py             ← Conexión base de datos
│   ├── models.py               ← Modelos SQLAlchemy
│   ├── schemas.py              ← Validación Pydantic
│   ├── seed_data.py            ← Datos iniciales
│   ├── routes/
│   │   ├── mesas.py            ← API Mesas
│   │   ├── menu.py             ← API Menú/Carta
│   │   ├── pedidos.py          ← API Pedidos + Cocina
│   │   ├── caja.py             ← API Caja Registradora
│   │   ├── clientes.py         ← API CRM Clientes
│   │   ├── reportes.py         ← API Reportes/Analytics
│   │   ├── whatsapp_webhook.py ← API WhatsApp Meta
│   │   └── config.py           ← API Configuración
│   └── services/
│       └── whatsapp_service.py ← Servicio Bot WhatsApp
│
├── frontend/                   ← Interfaz Web (HTML/CSS/JS)
│   ├── index.html              ← Dashboard principal
│   ├── pos.html                ← Terminal POS + Mesas
│   ├── cocina.html             ← Pantalla Cocina (TV)
│   ├── reportes.html           ← Reportes y Analytics
│   ├── clientes.html           ← CRM Clientes
│   ├── whatsapp.html           ← Centro WhatsApp
│   ├── admin.html              ← Configuración del sistema
│   └── assets/
│       ├── css/style.css       ← Estilos globales (tema oscuro)
│       └── js/api.js           ← Cliente API global
│
├── whatsapp_bot/               ← Bot WhatsApp + IA
│   ├── bot.py                  ← Bot principal + demo CLI
│   ├── pipeline.py             ← Pipeline Johnson (IA)
│   └── prompts.py              ← Los 10 Prompts IA
│
├── requirements.txt            ← Dependencias Python
├── .env.example                ← Configuración de ejemplo
├── start.bat                   ← Iniciador (Windows)
└── instalar_dependencias.bat   ← Instalador de librerías
```

---

## 📋 Módulos del ERP

| Módulo | URL | Descripción |
|--------|-----|-------------|
| 📊 Dashboard | `/` | KPIs en tiempo real, gráficos, pedidos recientes |
| 🛒 POS/Mesas | `/pos.html` | Terminal de punto de venta, gestión de mesas |
| 👨‍🍳 Cocina | `/cocina.html` | Pantalla para TV en cocina, urgencias por color |
| 👥 Clientes | `/clientes.html` | CRM, historial, puntos de fidelidad |
| 📈 Reportes | `/reportes.html` | Analytics, exportar Excel |
| 💬 WhatsApp | `/whatsapp.html` | Centro de conversaciones, simulador |
| ⚙️ Admin | `/admin.html` | Configurar menú, mesas, pagos, API keys |
| 📚 API Docs | `/docs` | Documentación interactiva (Swagger UI) |

---

## 🤖 Los 10 Prompts IA para WhatsApp

Todos los prompts usan **Google Gemini** y están en `whatsapp_bot/prompts.py`

| # | Nombre | Función |
|---|--------|---------|
| 1 | 👋 Bienvenida Inteligente | Saludo personalizado según historial del cliente |
| 2 | 🧠 Clasificador de Intención | Detecta qué quiere el cliente automáticamente |
| 3 | ⭐ Recomendador Personal | Sugiere platos según preferencias y pedidos anteriores |
| 4 | 📝 Descriptor de Platos | Describe ingredientes y preparación de forma irresistible |
| 5 | 🚨 Gestor de Alergias | Detecta y maneja restricciones alimentarias |
| 6 | 🛒 Confirmación de Orden | Resume el pedido con upselling sutil integrado |
| 7 | 💳 Guía de Pagos | Guía paso a paso para Yape, Plin, efectivo |
| 8 | 📍 Rastreador de Pedido | Estado en tiempo real con barra de progreso |
| 9 | 🎯 Manejador de Quejas | Convierte problemas en oportunidades de fidelización |
| 10 | 🎁 Promotor de Fidelización | Upselling inteligente + programa de puntos |

### Probar los Prompts IA

```bash
# Demo completo de los 10 prompts en consola
python -m whatsapp_bot.bot --demo

# Simular flujo completo de WhatsApp
python -m whatsapp_bot.bot --flujo

# Verificar conexión al backend
python -m whatsapp_bot.bot --test
```

---

## 💬 Flujo de WhatsApp (como en la imagen)

```
Cliente escribe "hola"
       ↓
[1] Bot saluda con nombre (Prompt 1 - Bienvenida Inteligente)
       ↓
[2] Cliente elige categoría (Ver Almuerzos / Ver Bebidas / etc.)
       ↓
[3] Bot muestra productos con precios
       ↓
[4] Cliente selecciona producto y cantidad (1 / 2 / 3)
       ↓
[5] Bot pregunta complementos (Bebidas)
       ↓
[6] Bot muestra resumen del pedido (Prompt 6 - Confirmación)
       ↓
[7] Cliente elige pago: Yape / Plin / Efectivo (Prompt 7 - Pagos)
       ↓
[8] Bot confirma pago y avisa tiempo de entrega
       ↓
[9] Cocina recibe el pedido en pantalla automáticamente
       ↓
[10] ERP registra pedido, cliente y estadísticas
```

---

## 🔑 Configuración

### 1. Variables de entorno (.env)

```env
# IA para los 10 prompts
GEMINI_API_KEY=AIzaSyXXXXX        # Google AI Studio

# WhatsApp Business Cloud API
WA_TOKEN=EAAxxxxxxx               # Meta Developers
WA_PHONE_ID=12345678901234
WA_VERIFY_TOKEN=gormetpos2024
```

### 2. Configurar WhatsApp en la aplicación

1. Abre `http://localhost:8000/admin.html`
2. Ve a la pestaña **WhatsApp API**
3. Ingresa tu Token y Phone ID de Meta
4. Ingresa tu Gemini API Key
5. Guarda la configuración

### 3. Configurar webhook en Meta

URL del webhook: `https://tu-dominio.com/api/whatsapp/webhook`
Token de verificación: `gormetpos2024`

---

## 💳 Métodos de Pago Soportados

- 💵 Efectivo (con cálculo de vuelto)
- 💜 Yape
- 🔵 Plin
- 💳 Tarjeta de crédito/débito
- 🟢 Nequi
- 🟠 Daviplata

---

## 📊 API Endpoints Principales

```
GET  /api/mesas/              → Listar mesas con estado
POST /api/pedidos/            → Crear pedido
POST /api/pedidos/{id}/items  → Agregar item al pedido
POST /api/pedidos/{id}/pagar  → Procesar pago
GET  /api/pedidos/cocina      → Ver pedidos en cocina
GET  /api/reportes/dashboard  → KPIs en tiempo real
GET  /api/menu/completo       → Menú organizado por categorías
POST /api/whatsapp/simular    → Simular mensaje WhatsApp (pruebas)
POST /api/whatsapp/webhook    → Webhook Meta Cloud API
```

Documentación completa: `http://localhost:8000/docs`

---

## 🗄️ Base de Datos

- **SQLite** por defecto (archivo `gormet_pos.db`)
- **PostgreSQL** para producción (configura `DATABASE_URL` en `.env`)
- La base de datos se inicializa automáticamente al arrancar
- Datos de ejemplo incluidos (16 mesas, menú peruano completo)

---

## 🎨 Tecnologías

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.10+ · FastAPI · SQLAlchemy · Pydantic |
| Base de Datos | SQLite (dev) · PostgreSQL (prod) |
| Frontend | HTML5 · CSS3 · JavaScript Vanilla · Chart.js |
| IA | Google Gemini 1.5 Flash |
| WhatsApp | Meta Cloud API · Webhook |
| Tiempo Real | WebSocket nativo |
| Exportación | Pandas · OpenPyXL |

---

## 🛠️ Credenciales por Defecto

El sistema no tiene login por defecto (para agregar auth, configura python-jose).

**Datos de menú inicial incluidos:**
- 🥗 Entradas: Ceviche, Causa, Tequeños, Anticuchos
- 🍽️ Platos: Lomo Saltado, Ají de Gallina, Arroz con Mariscos...
- 🍕 Menús Ejecutivos: A, B y Familiar
- 🍰 Postres: Suspiro, Tres Leches, Picarones
- 🥤 Bebidas: Inca Kola, Chicha Morada, Limonada...

---

## 📞 Soporte

- Email: edwinsumaran3@gmail.com
- Reporte de bugs: GitHub Issues

---

*GourmetPOS ERP v2.0 — Sistema profesional para restaurantes peruanos*

---

## 📦 Publicar en GitHub

Si quieres crear el repositorio en GitHub y subir el código, aquí tienes dos opciones.

1) Usando GitHub CLI (`gh`) — más sencillo si ya estás autenticado:

```bash
gh repo create USERNAME/gourmet-pos --public --source . --remote origin --push
```

2) Manual (sin `gh`):

```bash
git remote add origin https://github.com/USERNAME/gourmet-pos.git
git branch -M main
git push -u origin main
```

Reemplaza `USERNAME` por tu usuario u organización en GitHub.
