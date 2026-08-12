import fs from "node:fs/promises";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const WORKSPACE = path.resolve(__dirname, "..");
const ROOT = path.resolve(WORKSPACE, "..");
const OUT_DIR = path.join(WORKSPACE, "output");
const SCRATCH = path.join(WORKSPACE, "scratch");
const PREVIEW_DIR = path.join(SCRATCH, "previews");
const LAYOUT_DIR = path.join(SCRATCH, "layouts");
const ASSET_DIR = path.join(SCRATCH, "assets");

const W = 1920;
const H = 1080;
const M = 96;

const C = {
  ink: "#101820",
  ink2: "#172231",
  ink3: "#243247",
  paper: "#FAF7F0",
  paper2: "#F1EBDD",
  line: "#D7CEBC",
  muted: "#657283",
  orange: "#FF6B35",
  teal: "#00D4A1",
  blue: "#4FC3F7",
  purple: "#7C3AED",
  yellow: "#FFB800",
  red: "#F43F5E",
  white: "#FFFFFF",
};

const FONT = {
  display: "Aptos Display",
  body: "Aptos",
  mono: "Cascadia Mono",
};

const NO = { type: "none" };

async function ensureDirs() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(LAYOUT_DIR, { recursive: true });
}

async function saveBlob(blob, target) {
  await fs.writeFile(target, Buffer.from(await blob.arrayBuffer()));
}

function solid(color) {
  return { type: "solid", color };
}

function addRect(slide, x, y, w, h, fill, name = "rect", line = NO) {
  const s = slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: solid(fill),
    line: { fill: line },
  });
  s.name = name;
  return s;
}

function addText(slide, text, x, y, w, h, opts = {}) {
  const s = slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: NO,
    line: { fill: NO },
  });
  s.name = opts.name || "text";
  s.text.style = {
    typeface: opts.typeface || FONT.body,
    fontSize: opts.size || 28,
    bold: !!opts.bold,
    italic: !!opts.italic,
    color: opts.color || C.ink,
    alignment: opts.align || "left",
    verticalAlignment: opts.valign || "top",
  };
  s.text = text;
  return s;
}

function addLabel(slide, text, x, y, w, h, fill, color = C.white, name = "label") {
  const s = addRect(slide, x, y, w, h, fill, name, NO);
  s.text.style = {
    typeface: FONT.body,
    fontSize: 20,
    bold: true,
    color,
    alignment: "center",
    verticalAlignment: "middle",
  };
  s.text = text;
  return s;
}

function addRule(slide, x, y, w, color = C.orange, h = 5, name = "rule") {
  return addRect(slide, x, y, w, h, color, name, NO);
}

function addFooter(slide, n, dark = false) {
  addText(
    slide,
    `GourmetPOS ERP | construccion explicada por capas | ${String(n).padStart(2, "0")}`,
    M,
    H - 56,
    W - 2 * M,
    28,
    {
      name: `footer-${n}`,
      size: 15,
      color: dark ? "#9FB0C5" : C.muted,
    },
  );
}

function addHeader(slide, title, subtitle, n, opts = {}) {
  const dark = !!opts.dark;
  const color = dark ? C.white : C.ink;
  const muted = dark ? "#B9C6D6" : C.muted;
  addText(slide, title, M, 58, 1300, 74, {
    name: `slide-${n}-title`,
    typeface: FONT.display,
    size: 50,
    bold: true,
    color,
  });
  if (subtitle) {
    addText(slide, subtitle, M, 130, 1370, 46, {
      name: `slide-${n}-subtitle`,
      size: 24,
      color: muted,
    });
  }
  addLabel(slide, String(n).padStart(2, "0"), W - 170, 70, 74, 42, opts.accent || C.orange, C.white, `num-${n}`);
  addRule(slide, M, 190, W - 2 * M, opts.accent || C.orange, 4, `title-rule-${n}`);
  addFooter(slide, n, dark);
}

function addChip(slide, text, x, y, w, color, opts = {}) {
  const s = addRect(slide, x, y, w, opts.h || 44, color, opts.name || "chip", NO);
  s.text.style = {
    typeface: FONT.body,
    fontSize: opts.size || 20,
    bold: true,
    color: opts.textColor || C.white,
    alignment: "center",
    verticalAlignment: "middle",
  };
  s.text = text;
  return s;
}

function addCard(slide, x, y, w, h, title, body, accent = C.orange, opts = {}) {
  addRect(slide, x, y, w, h, opts.fill || C.white, opts.name || "card", solid(opts.stroke || C.line));
  addRect(slide, x, y, 10, h, accent, `${opts.name || "card"}-accent`, NO);
  addText(slide, title, x + 34, y + 24, w - 58, 34, {
    name: `${opts.name || "card"}-title`,
    size: opts.titleSize || 25,
    bold: true,
    color: opts.titleColor || C.ink,
  });
  addText(slide, body, x + 34, y + 66, w - 58, h - 90, {
    name: `${opts.name || "card"}-body`,
    size: opts.bodySize || 20,
    color: opts.bodyColor || C.muted,
  });
}

function addSmallStat(slide, value, label, x, y, w, color, name) {
  addText(slide, value, x, y, w, 76, {
    name: `${name}-value`,
    typeface: FONT.display,
    size: 58,
    bold: true,
    color,
    align: "center",
    valign: "middle",
  });
  addText(slide, label, x, y + 76, w, 54, {
    name: `${name}-label`,
    size: 20,
    bold: true,
    color: C.muted,
    align: "center",
  });
}

function addTable(slide, x, y, cols, rows, opts = {}) {
  const headerH = opts.headerH || 48;
  const rowH = opts.rowH || 48;
  const widths = cols.map((c) => c.w);
  const totalW = widths.reduce((a, b) => a + b, 0);
  addRect(slide, x, y, totalW, headerH + rows.length * rowH, opts.bg || C.white, opts.name || "table", solid(opts.stroke || C.line));
  addRect(slide, x, y, totalW, headerH, opts.headerFill || C.ink, `${opts.name || "table"}-header`, NO);

  let cx = x;
  cols.forEach((c, i) => {
    addText(slide, c.label, cx + 14, y + 12, widths[i] - 28, headerH - 16, {
      name: `${opts.name || "table"}-h-${i}`,
      size: opts.headerSize || 18,
      bold: true,
      color: opts.headerColor || C.white,
    });
    cx += widths[i];
  });

  rows.forEach((r, ri) => {
    const ry = y + headerH + ri * rowH;
    if (ri % 2 === 1) addRect(slide, x, ry, totalW, rowH, opts.altFill || C.paper2, `${opts.name || "table"}-alt-${ri}`, NO);
    addRule(slide, x, ry, totalW, opts.rule || C.line, 2, `${opts.name || "table"}-rule-${ri}`);
    let tx = x;
    cols.forEach((c, ci) => {
      addText(slide, r[ci] || "", tx + 14, ry + 10, widths[ci] - 28, rowH - 12, {
        name: `${opts.name || "table"}-r${ri}-c${ci}`,
        size: opts.size || 17,
        bold: ci === 0,
        color: ci === 0 ? C.ink : C.muted,
      });
      tx += widths[ci];
    });
  });
}

function addArrow(slide, x1, y, x2, color = C.orange, name = "arrow") {
  const w = x2 - x1;
  addRect(slide, x1, y, w - 32, 5, color, `${name}-line`, NO);
  addText(slide, ">", x2 - 42, y - 21, 42, 45, {
    name: `${name}-head`,
    size: 34,
    bold: true,
    color,
    align: "center",
    valign: "middle",
  });
}

function addImage(slide, filename, x, y, w, h, opts = {}) {
  const imgPath = path.join(ASSET_DIR, filename);
  const data = readFileSync(imgPath).toString("base64");
  const img = slide.images.add({
    dataUrl: `data:image/png;base64,${data}`,
    alt: opts.alt || filename,
    position: { left: x, top: y, width: w, height: h },
    fit: opts.fit || "cover",
  });
  img.name = opts.name || filename;
  return img;
}

function addSlide(presentation, bg = C.paper) {
  const slide = presentation.slides.add();
  addRect(slide, 0, 0, W, H, bg, "slide-background", NO);
  return slide;
}

function slide1(p, n) {
  const s = addSlide(p, C.ink);
  addRect(s, 0, 0, W, H, C.ink, "cover-bg", NO);
  addRect(s, 0, 0, 520, H, C.orange, "cover-orange", NO);
  addRect(s, 520, 0, 120, H, C.teal, "cover-teal", NO);
  addText(s, "GourmetPOS\nERP", 118, 130, 470, 230, {
    name: "cover-brand",
    typeface: FONT.display,
    size: 78,
    bold: true,
    color: C.white,
  });
  addText(s, "Como la IA construyo\neste programa", 720, 168, 1020, 250, {
    name: "cover-title",
    typeface: FONT.display,
    size: 76,
    bold: true,
    color: C.white,
  });
  addText(s, "Lectura tecnica del repositorio: cada archivo, su funcion y el flujo que une backend, frontend, base de datos y WhatsApp con IA.", 724, 450, 1010, 120, {
    name: "cover-promise",
    size: 31,
    color: "#C9D5E4",
  });
  addChip(s, "FastAPI", 724, 625, 170, C.blue, { name: "cover-chip-api" });
  addChip(s, "SQLite/PostgreSQL", 914, 625, 270, C.teal, { name: "cover-chip-db", textColor: C.ink });
  addChip(s, "WhatsApp + Gemini", 1204, 625, 290, C.orange, { name: "cover-chip-ai" });
  addText(s, "Presentacion profesional PDF + PPTX editable", 724, 900, 900, 36, {
    name: "cover-meta",
    size: 22,
    color: "#9FB0C5",
  });
  addText(s, "2026", 1650, 900, 150, 36, {
    name: "cover-year",
    size: 22,
    color: "#9FB0C5",
    align: "right",
  });
  addFooter(s, n, true);
}

function slide2(p, n) {
  const s = addSlide(p);
  addHeader(s, "La construccion se entiende por capas", "La IA separo el problema en decisiones pequenas: datos, API, pantallas, automatizacion y despliegue.", n);
  const steps = [
    ["01", "Objetivo", "Un ERP para restaurante: ventas, mesas, cocina, clientes y WhatsApp."],
    ["02", "Datos", "Modelos SQLAlchemy y schemas Pydantic para validar contratos."],
    ["03", "API", "Routers FastAPI por dominio: mesas, menu, pedidos, caja, reportes."],
    ["04", "Interfaz", "HTML/CSS/JS vanilla servido por el mismo backend."],
    ["05", "IA/WhatsApp", "Servicio conversacional, prompts y estados de pedido."],
    ["06", "Deploy", "Railway, Procfile, runtime y variables de entorno."],
  ];
  const x0 = 150;
  const y = 330;
  const gap = 36;
  const w = 250;
  steps.forEach((st, i) => {
    const x = x0 + i * (w + gap);
    addChip(s, st[0], x, y, 72, i % 2 ? C.teal : C.orange, { name: `step-${i}-num`, textColor: i % 2 ? C.ink : C.white });
    addText(s, st[1], x, y + 70, w, 42, { name: `step-${i}-title`, typeface: FONT.display, size: 29, bold: true });
    addText(s, st[2], x, y + 118, w, 130, { name: `step-${i}-body`, size: 19, color: C.muted });
    if (i < steps.length - 1) addArrow(s, x + 88, y + 22, x + w + 18, i % 2 ? C.teal : C.orange, `step-${i}-arrow`);
  });
  addCard(s, 230, 760, 1460, 130, "Idea central", "El programa no es una sola pieza grande: es una cadena de archivos especializados que se comunican por modelos, endpoints y llamadas HTTP.", C.purple, {
    name: "central-idea",
    bodySize: 25,
    titleSize: 28,
  });
}

function slide3(p, n) {
  const s = addSlide(p);
  addHeader(s, "Inventario real del proyecto", "41 archivos fuente/configuracion mas una base SQLite local; los caches Python se ignoran.", n, { accent: C.teal });
  const stats = [
    ["10", "raiz y operacion", C.orange],
    ["17", "backend Python", C.teal],
    ["10", "frontend web", C.blue],
    ["05", "bot WhatsApp", C.purple],
  ];
  stats.forEach((it, i) => addSmallStat(s, it[0], it[1], 170 + i * 405, 270, 300, it[2], `stat-${i}`));
  const cols = [
    { label: "Capa", w: 330 },
    { label: "Archivos clave", w: 700 },
    { label: "Responsabilidad", w: 570 },
  ];
  const rows = [
    ["Raiz", "README, requirements, .env, start, Railway", "Instalar, configurar, arrancar y desplegar."],
    ["Backend", "main, database, models, schemas, seed", "API, datos, reglas y vida del servidor."],
    ["Routes", "mesas, menu, pedidos, caja, clientes...", "Endpoints por modulo del negocio."],
    ["Frontend", "8 paginas + style.css + api.js", "Experiencia del usuario y llamadas al API."],
    ["WhatsApp IA", "bot, pipeline, prompts, service", "Conversacion, prompts y pedidos por chat."],
  ];
  addTable(s, 160, 520, cols, rows, { name: "inventory-table", rowH: 58, size: 19, headerFill: C.ink2 });
}

function slide4(p, n) {
  const s = addSlide(p);
  addHeader(s, "Arquitectura general", "El backend sirve la API y el frontend; WhatsApp entra por webhook y termina registrando pedidos.", n, { accent: C.blue });
  const layers = [
    ["Frontend HTML", "index, POS, cocina, clientes, reportes, WhatsApp, admin", C.blue],
    ["API FastAPI", "routers + schemas + servicios", C.orange],
    ["Dominio", "mesas, menu, pedidos, caja, clientes, conversaciones", C.purple],
    ["Persistencia", "SQLAlchemy + SQLite local / PostgreSQL produccion", C.teal],
  ];
  layers.forEach((l, i) => {
    const y = 260 + i * 150;
    addRect(s, 230, y, 1460, 96, i % 2 ? C.white : C.paper2, `arch-layer-${i}`, solid(C.line));
    addRect(s, 230, y, 16, 96, l[2], `arch-layer-${i}-accent`, NO);
    addText(s, l[0], 280, y + 18, 360, 36, { name: `arch-title-${i}`, size: 30, bold: true });
    addText(s, l[1], 700, y + 26, 850, 34, { name: `arch-body-${i}`, size: 24, color: C.muted });
    if (i < layers.length - 1) {
      addText(s, "v", 945, y + 104, 40, 38, { name: `arch-down-${i}`, size: 34, bold: true, color: l[2], align: "center" });
    }
  });
  addChip(s, "Webhook Meta", 280, 880, 210, C.ink2, { name: "webhook-chip" });
  addArrow(s, 500, 901, 750, C.orange, "webhook-arrow");
  addChip(s, "WhatsAppService", 775, 880, 260, C.orange, { name: "service-chip" });
  addArrow(s, 1050, 901, 1300, C.teal, "service-arrow");
  addChip(s, "Pedido en BD", 1325, 880, 220, C.teal, { name: "pedido-chip", textColor: C.ink });
}

function slide5(p, n) {
  const s = addSlide(p);
  addHeader(s, "Arranque del sistema", "`start.bat` prepara entorno; `uvicorn` abre FastAPI; `main.py` crea tablas y monta pantallas.", n);
  const flow = [
    ["start.bat", "detecta Python, crea .env, instala basicos, elige puerto"],
    ["uvicorn", "ejecuta backend.main:app con recarga local"],
    ["lifespan", "create_all + seed_database + scheduler"],
    ["routers", "incluye /api/mesas, /menu, /pedidos..."],
    ["frontend", "monta /frontend como sitio estatico"],
  ];
  flow.forEach((f, i) => {
    const x = 140 + i * 350;
    addCard(s, x, 315, 285, 250, f[0], f[1], [C.orange, C.blue, C.teal, C.purple, C.yellow][i], { name: `boot-${i}`, bodySize: 20 });
    if (i < flow.length - 1) addArrow(s, x + 292, 430, x + 345, [C.orange, C.blue, C.teal, C.purple][i], `boot-arrow-${i}`);
  });
  addImage(s, "code_main.png", 300, 650, 1320, 250, { name: "main-code-image", fit: "cover", alt: "Fragmento de backend main.py" });
}

function slide6(p, n) {
  const s = addSlide(p);
  addHeader(s, "Archivos raiz: operacion y despliegue", "Estos archivos hacen que el sistema sea instalable, configurable y desplegable.", n, { accent: C.teal });
  const cols = [
    { label: "Archivo", w: 370 },
    { label: "Paso de construccion", w: 570 },
    { label: "Por que existe", w: 690 },
  ];
  const rows = [
    ["README.md", "Documentar arquitectura y uso", "Guia rapida, endpoints, tecnologias y flujo WhatsApp."],
    ["requirements.txt", "Fijar dependencias", "FastAPI, SQLAlchemy, Gemini, pandas, openpyxl."],
    [".env.example", "Separar secretos", "DATABASE_URL, Gemini, WhatsApp y servidor."],
    ["start.bat", "Arranque Windows", "Crea .env, detecta puerto y lanza Uvicorn."],
    ["instalar_dependencias.bat", "Instalacion guiada", "Instala librerias por grupos funcionales."],
    ["Procfile / railway.toml", "Deploy Railway", "Comando web, healthcheck y politica de reinicio."],
    ["runtime.txt / .gitignore", "Higiene del repo", "Python 3.12, ignora .env, DB, caches y logs."],
    ["gormet_pos.db", "Persistencia local", "SQLite generado para desarrollo; produccion usa PostgreSQL."],
  ];
  addTable(s, 145, 245, cols, rows, { name: "root-files", rowH: 62, size: 18, headerFill: C.ink2 });
}

function slide7(p, n) {
  const s = addSlide(p);
  addHeader(s, "Backend nucleo: datos, contratos y vida del servidor", "La IA primero definio el corazon del sistema antes de pintar pantallas.", n, { accent: C.orange });
  const rows = [
    ["backend/__init__.py", "Convierte backend en paquete importable."],
    ["database.py", "Crea engine, SessionLocal y get_db para inyeccion."],
    ["models.py", "Define tablas y relaciones SQLAlchemy del negocio."],
    ["schemas.py", "Define contratos Pydantic de entrada/salida."],
    ["seed_data.py", "Siembra config, categorias base y 16 mesas."],
    ["main.py", "Crea app, CORS, WebSocket, scheduler, routers y frontend."],
  ];
  addTable(s, 150, 280, [{ label: "Archivo", w: 470 }, { label: "Rol exacto", w: 1090 }], rows, {
    name: "backend-core",
    rowH: 68,
    size: 22,
    headerFill: C.orange,
  });
  addCard(s, 270, 815, 1380, 110, "Decision tecnica", "FastAPI queda como centro: valida por schemas, persiste por SQLAlchemy y sirve el frontend estatico.", C.teal, {
    name: "backend-decision",
    bodySize: 25,
  });
}

function slide8(p, n) {
  const s = addSlide(p);
  addHeader(s, "Modelo de datos: el negocio convertido en tablas", "`models.py` convierte mesas, productos, pedidos, pagos y conversaciones en entidades conectadas.", n, { accent: C.purple });
  const nodes = [
    ["Categoria", 160, 280, C.orange],
    ["Producto", 430, 280, C.orange],
    ["Mesa", 160, 470, C.blue],
    ["Cliente", 430, 470, C.blue],
    ["Pedido", 730, 375, C.purple],
    ["DetallePedido", 1050, 280, C.teal],
    ["Pago", 1050, 470, C.teal],
    ["SesionCaja", 1350, 375, C.yellow],
    ["ConversacionWhatsApp", 430, 675, C.red],
    ["ConfigRestaurante", 820, 675, C.ink3],
    ["MensajeProgramado", 1230, 675, C.ink3],
  ];
  nodes.forEach(([label, x, y, color], i) => {
    addRect(s, x, y, 230, 78, C.white, `model-${i}`, solid(color));
    addText(s, label, x + 12, y + 22, 206, 34, { name: `model-${i}-label`, size: 22, bold: true, color: C.ink, align: "center" });
  });
  const rels = [
    [390, 319, 430], [660, 319, 730], [390, 509, 730], [660, 509, 730],
    [960, 414, 1050], [960, 414, 1050], [1280, 414, 1350], [660, 714, 730],
  ];
  rels.forEach((r, i) => addArrow(s, r[0], r[1], r[2], [C.orange, C.blue, C.purple, C.teal][i % 4], `rel-${i}`));
  addText(s, "Relaciones principales: categoria -> producto; mesa/cliente -> pedido; pedido -> detalle/pago; cliente -> conversacion.", 190, 870, 1540, 48, {
    name: "model-note",
    size: 25,
    color: C.muted,
    align: "center",
  });
}

function slide9(p, n) {
  const s = addSlide(p);
  addHeader(s, "Routers: un archivo por modulo del restaurante", "La API se parte por responsabilidades para que cada endpoint tenga un lugar claro.", n, { accent: C.blue });
  const rows = [
    ["routes/__init__.py", "Paquete de rutas", "Permite importar routers desde `backend.routes`."],
    ["mesas.py", "Mesas", "Listar, crear, cambiar estado y configurar cantidad."],
    ["menu.py", "Carta", "Categorias, productos, menu completo y menu del dia."],
    ["pedidos.py", "Ventas", "Crear pedido, items, cocina, estados, prioridad y pago."],
    ["caja.py", "Caja", "Abrir/cerrar sesion, historial y resumen diario."],
    ["clientes.py", "CRM", "Buscar, crear, editar, historial y puntos."],
    ["reportes.py", "Analytics", "Dashboard, ventas, top productos, pagos, Excel."],
    ["config.py", "Ajustes", "Leer/actualizar configuracion individual o masiva."],
    ["whatsapp_webhook.py", "Canal WhatsApp", "Webhook Meta, simulador, conversaciones y envios."],
  ];
  addTable(s, 135, 235, [
    { label: "Archivo", w: 360 },
    { label: "Modulo", w: 270 },
    { label: "Endpoints que concentra", w: 980 },
  ], rows, { name: "routes-table", rowH: 56, size: 17, headerFill: C.blue, headerColor: C.ink });
}

function slide10(p, n) {
  const s = addSlide(p);
  addHeader(s, "Flujo de pedido: del click al ticket", "`pedidos.py` es el motor transaccional: calcula totales, cambia estados y registra pago.", n);
  const y = 330;
  const items = [
    ["Crear", "POST /pedidos", C.blue],
    ["Agregar item", "POST /{id}/items", C.orange],
    ["Cocina", "GET /cocina", C.red],
    ["Listo/estado", "PUT /estado", C.purple],
    ["Pagar", "POST /pagar", C.teal],
  ];
  items.forEach((it, i) => {
    const x = 130 + i * 352;
    addCard(s, x, y, 292, 175, it[0], it[1], it[2], { name: `pedido-flow-${i}`, bodySize: 22, titleSize: 28 });
    if (i < items.length - 1) addArrow(s, x + 300, y + 86, x + 346, it[2], `pedido-arrow-${i}`);
  });
  addRect(s, 270, 660, 1380, 130, C.ink2, "formula-band", NO);
  addText(s, "subtotal -> IGV -> descuento -> total -> metodo_pago -> ticket", 305, 695, 1310, 48, {
    name: "formula",
    typeface: FONT.mono,
    size: 34,
    bold: true,
    color: C.white,
    align: "center",
  });
  addText(s, "La mesa se libera al cobrar y el cliente suma historial/puntos cuando aplica.", 330, 830, 1260, 44, {
    name: "pedido-note",
    size: 26,
    color: C.muted,
    align: "center",
  });
}

function slide11(p, n) {
  const s = addSlide(p);
  addHeader(s, "WhatsApp: servicio conversacional completo", "`whatsapp_service.py` traduce mensajes de clientes en decisiones, respuestas y pedidos reales.", n, { accent: C.teal });
  addImage(s, "code_whatsapp_service.png", 100, 250, 820, 540, { name: "whatsapp-service-code", fit: "cover" });
  const rows = [
    ["Builders", "text, imagen, botones, listas, templates, ubicacion"],
    ["Carga de contexto", "menu activo, contactos y configuracion del restaurante"],
    ["Flujo", "bienvenida -> categorias -> productos -> detalle -> pago"],
    ["Registro", "crea cliente, pedido, detalles y conversacion"],
    ["Masivos", "envio de texto, botones y menu del dia"],
  ];
  addTable(s, 980, 285, [{ label: "Bloque", w: 260 }, { label: "Funcion", w: 570 }], rows, {
    name: "wa-service-table",
    rowH: 78,
    size: 21,
    headerFill: C.teal,
    headerColor: C.ink,
  });
  addText(s, "La IA no solo responde: conserva estado de conversacion y lo convierte en datos del ERP.", 1010, 790, 780, 70, {
    name: "wa-thesis",
    size: 28,
    bold: true,
    color: C.ink,
  });
}

function slide12(p, n) {
  const s = addSlide(p);
  addHeader(s, "Bot y prompts IA: 10 tareas especializadas", "`whatsapp_bot` separa demo CLI, pipeline Gemini y biblioteca de prompts.", n, { accent: C.purple });
  addImage(s, "code_prompts.png", 1040, 258, 740, 515, { name: "prompts-code", fit: "cover" });
  const files = [
    ["__init__.py", "Declara paquete."],
    ["handlers/__init__.py", "Reserva punto para handlers."],
    ["bot.py", "Demo CLI, prueba backend y simulacion."],
    ["pipeline.py", "PipelineJohnson: llama Gemini y fallback."],
    ["prompts.py", "10 prompts con mapa y descripciones."],
  ];
  addTable(s, 120, 260, [{ label: "Archivo", w: 300 }, { label: "Rol", w: 560 }], files, {
    name: "bot-files",
    rowH: 65,
    size: 21,
    headerFill: C.purple,
  });
  const promptNames = [
    "Bienvenida", "Clasificador", "Recomendador", "Descriptor", "Alergias",
    "Confirmacion", "Pagos", "Estado", "Quejas", "Fidelizacion",
  ];
  promptNames.forEach((name, i) => {
    const x = 140 + (i % 5) * 170;
    const y = 700 + Math.floor(i / 5) * 70;
    addChip(s, `${i + 1}. ${name}`, x, y, 150, i % 2 ? C.teal : C.orange, {
      name: `prompt-chip-${i}`,
      size: 16,
      textColor: i % 2 ? C.ink : C.white,
    });
  });
}

function slide13(p, n) {
  const s = addSlide(p);
  addHeader(s, "Frontend: una app web modular sin framework pesado", "`api.js` centraliza llamadas y `style.css` da el sistema visual para todas las pantallas.", n, { accent: C.blue });
  addImage(s, "code_api.png", 940, 255, 820, 520, { name: "api-code", fit: "cover" });
  addCard(s, 140, 280, 700, 140, "assets/js/api.js", "API.get/post/put/delete, toast, formato de moneda/fecha, badges y WebSocket.", C.blue, { name: "api-card", bodySize: 24 });
  addCard(s, 140, 455, 700, 140, "assets/css/style.css", "Tema oscuro, sidebar, cards, tablas, botones, badges, modales, POS, cocina y responsive.", C.orange, { name: "css-card", bodySize: 24 });
  addCard(s, 140, 630, 700, 140, "HTML por pantalla", "Cada pagina contiene su markup y funciones JS de dominio, consumiendo el mismo API.", C.teal, { name: "html-card", bodySize: 24 });
}

function slide14(p, n) {
  const s = addSlide(p);
  addHeader(s, "Pantallas operativas principales", "La IA construyo cada pantalla alrededor de una tarea diaria del restaurante.", n);
  const screens = [
    ["index.html", "Dashboard", "KPIs, graficos Chart.js y ultimos pedidos.", C.blue],
    ["pos.html", "POS/Mesas", "Abrir mesa, carrito, pago, ticket y delivery.", C.orange],
    ["cocina.html", "Cocina TV", "Pedidos por urgencia, items listos y prioridad.", C.red],
    ["clientes.html", "CRM", "Busqueda, historial y puntos de fidelidad.", C.teal],
  ];
  screens.forEach((sc, i) => {
    const x = 150 + (i % 2) * 840;
    const y = 270 + Math.floor(i / 2) * 300;
    addCard(s, x, y, 700, 220, `${sc[0]} | ${sc[1]}`, sc[2], sc[3], {
      name: `screen-main-${i}`,
      bodySize: 28,
      titleSize: 28,
      fill: i % 2 ? C.white : C.paper2,
    });
    addText(s, ["API reportes", "API mesas/menu/pedidos", "API pedidos/cocina", "API clientes"][i], x + 40, y + 155, 600, 34, {
      name: `screen-api-${i}`,
      size: 20,
      bold: true,
      color: sc[3],
    });
  });
}

function slide15(p, n) {
  const s = addSlide(p);
  addHeader(s, "ERP móvil: menú del día por horario", "La experiencia empieza con las comidas corrientes seleccionadas del día, luego platos especiales y opciones acorde al momento: desayuno, almuerzo y cena.", n, { accent: C.orange });

  const schedule = [
    ["Desayuno", ["Avena o yogurt con fruta", "Huevos con arepa y café", "Tostadas + jugo natural"], C.orange],
    ["Almuerzo", ["Plato corriente del día", "Sopa o entrada del momento", "Proteína + arroz + ensalada"], C.teal],
    ["Cena", ["Especial de la casa", "Plato principal del menú", "Bebidas calientes o frías"], C.blue],
  ];

  schedule.forEach((slot, i) => {
    const x = 120 + i * 560;
    addRect(s, x, 260, 500, 500, C.white, `mobile-slot-${i}`, solid(C.line));
    addRect(s, x, 260, 500, 80, slot[2], `mobile-slot-${i}-bar`, NO);
    addText(s, slot[0], x + 30, 286, 260, 40, { name: `mobile-slot-${i}-title`, typeface: FONT.display, size: 34, bold: true, color: C.ink });
    slot[1].forEach((item, index) => {
      const y = 370 + index * 100;
      addRect(s, x + 30, y, 440, 70, index % 2 ? C.paper2 : C.white, `mobile-item-${i}-${index}`, solid(C.line));
      addText(s, item, x + 50, y + 18, 400, 34, { name: `mobile-item-${i}-${index}-label`, size: 22, bold: true, color: C.ink });
    });
  });

  addCard(s, 150, 800, 720, 150, "Platos especiales del día", "Ofertas premium, platos destacados, baja disponibilidad y descripción breve para facilitar la elección rápida desde celular.", C.purple, {
    name: "mobile-specials",
    titleSize: 30,
    bodySize: 24,
  });
  addCard(s, 930, 800, 850, 150, "Otras comidas y bebidas", "Entradas, postres, café, jugos, agua, refrescos y opciones según la hora del día para completar la compra sin saturar la pantalla.", C.teal, {
    name: "mobile-others",
    titleSize: 30,
    bodySize: 24,
  });
  addText(s, "Diseño móvil: primero lo cotidiano del día, luego lo destacado y finalmente las bebidas u otras opciones por horario.", 180, 980, 1560, 38, {
    name: "mobile-summary",
    size: 26,
    color: C.muted,
    align: "center",
  });
}

function slide16(p, n) {
  const s = addSlide(p);
  addHeader(s, "Como se conectan pantallas y endpoints", "El frontend no toca la base directamente: todo pasa por `/api`.", n, { accent: C.purple });
  const rows = [
    ["Dashboard", "index.html", "/reportes/dashboard, /productos-top, /metodos-pago, /ventas-por-hora"],
    ["POS", "pos.html", "/mesas, /menu/completo, /pedidos, /pedidos/{id}/pagar"],
    ["Cocina", "cocina.html", "/pedidos/cocina, /items/{id}/listo, /prioridad"],
    ["Clientes", "clientes.html", "/clientes, /clientes/{id}/historial, /puntos"],
    ["WhatsApp", "whatsapp.html", "/whatsapp/conversaciones, /contactos, /envio-masivo"],
    ["Admin/Menu", "admin.html + menu-dia.html", "/config, /menu/categorias, /menu/productos, /menu/activar-dia"],
  ];
  addTable(s, 115, 250, [
    { label: "Modulo visual", w: 260 },
    { label: "Archivo", w: 420 },
    { label: "Endpoints principales", w: 1060 },
  ], rows, { name: "screen-endpoints", rowH: 80, size: 19, headerFill: C.purple });
}

function slide17(p, n) {
  const s = addSlide(p);
  addHeader(s, "Persistencia y configuracion", "La base local permite probar; las variables permiten mover el mismo sistema a produccion.", n, { accent: C.teal });
  const columns = [
    ["Desarrollo", "SQLite\n`gormet_pos.db`\nse crea/usa localmente", C.blue],
    ["Produccion", "PostgreSQL\n`DATABASE_URL`\nRailway lo entrega", C.teal],
    ["Secretos", "Gemini + WhatsApp\n`.env` no se sube", C.orange],
  ];
  columns.forEach((col, i) => {
    addCard(s, 170 + i * 570, 300, 460, 260, col[0], col[1], col[2], {
      name: `persist-${i}`,
      bodySize: 30,
      titleSize: 31,
      fill: C.white,
    });
  });
  addCard(s, 250, 690, 1420, 145, "Seed inicial", "`seed_data.py` crea configuracion, categorias base y 16 mesas; el menu real se administra desde Admin/Menu del dia.", C.purple, {
    name: "seed-card",
    bodySize: 27,
  });
}

function slide18(p, n) {
  const s = addSlide(p, C.ink);
  addHeader(s, "Paso a paso de construccion IA | 1 a 4", "La lectura del repo permite reconstruir el orden logico de fabricacion.", n, { dark: true, accent: C.orange });
  const steps = [
    ["1", "Definir alcance", "Restaurante necesita ventas, mesas, cocina, clientes, reportes y WhatsApp."],
    ["2", "Modelar datos", "Enums, tablas, relaciones y schemas antes de crear pantallas."],
    ["3", "Crear API por dominio", "Cada ruta resuelve un proceso del restaurante."],
    ["4", "Agregar arranque", "FastAPI, CORS, lifespan, seed, WebSocket y frontend estatico."],
  ];
  steps.forEach((st, i) => {
    const y = 260 + i * 170;
    addChip(s, st[0], 180, y + 20, 70, i % 2 ? C.teal : C.orange, { name: `build-a-${i}-num`, textColor: i % 2 ? C.ink : C.white });
    addText(s, st[1], 300, y, 450, 50, { name: `build-a-${i}-title`, typeface: FONT.display, size: 36, bold: true, color: C.white });
    addText(s, st[2], 800, y + 5, 820, 80, { name: `build-a-${i}-body`, size: 27, color: "#C9D5E4" });
    addRule(s, 300, y + 102, 1260, i % 2 ? C.teal : C.orange, 3, `build-a-${i}-rule`);
  });
}

function slide19(p, n) {
  const s = addSlide(p, C.ink);
  addHeader(s, "Paso a paso de construccion IA | 5 a 8", "Despues del nucleo, la IA crea experiencia, automatizacion y despliegue.", n, { dark: true, accent: C.teal });
  const steps = [
    ["5", "Diseñar interfaz", "HTML por pantalla, CSS global y api.js compartido."],
    ["6", "Construir POS/cocina", "Carrito, totales, tickets, estados y prioridades."],
    ["7", "Integrar WhatsApp IA", "Webhook, servicio Meta, pipeline Gemini y 10 prompts."],
    ["8", "Preparar entrega", "README, .env.example, .bat, Procfile y railway.toml."],
  ];
  steps.forEach((st, i) => {
    const x = 150 + (i % 2) * 850;
    const y = 290 + Math.floor(i / 2) * 290;
    addRect(s, x, y, 720, 210, i % 2 ? "#132A2A" : "#2A1B15", `build-b-${i}`, solid(i % 2 ? C.teal : C.orange));
    addText(s, st[0], x + 30, y + 30, 70, 70, { name: `build-b-${i}-num`, size: 48, bold: true, color: i % 2 ? C.teal : C.orange, align: "center" });
    addText(s, st[1], x + 125, y + 35, 530, 44, { name: `build-b-${i}-title`, typeface: FONT.display, size: 34, bold: true, color: C.white });
    addText(s, st[2], x + 125, y + 95, 530, 74, { name: `build-b-${i}-body`, size: 24, color: "#C9D5E4" });
  });
}

function slide20(p, n) {
  const s = addSlide(p);
  addHeader(s, "Calidad tecnica y riesgos controlados", "El proyecto evita mezclar capas y deja puntos claros para mantenimiento.", n, { accent: C.orange });
  const good = [
    ["Separacion", "Modelos, schemas, rutas, servicios y frontend en archivos distintos."],
    ["Contratos", "Pydantic valida datos antes de llegar a la base."],
    ["Deploy", "Railway healthcheck y comando de arranque reproducible."],
    ["Tiempo real", "WebSocket centralizado para actualizaciones."],
  ];
  good.forEach((g, i) => addCard(s, 140 + (i % 2) * 840, 270 + Math.floor(i / 2) * 240, 700, 170, g[0], g[1], [C.teal, C.blue, C.orange, C.purple][i], { name: `quality-${i}`, bodySize: 25 }));
  addCard(s, 250, 805, 1420, 90, "Observacion honesta", "La base `gormet_pos.db` es local y no deberia subirse; `.gitignore` ya lo contempla. Para produccion, usar `DATABASE_URL` PostgreSQL.", C.red, {
    name: "quality-risk",
    titleSize: 24,
    bodySize: 22,
  });
}

function slide21(p, n) {
  const s = addSlide(p);
  addHeader(s, "Mapa completo de archivos por responsabilidad", "Resumen final para defender el proyecto archivo por archivo.", n, { accent: C.blue });
  const rows = [
    ["Raiz", "README.md, requirements.txt, .env.example, .gitignore"],
    ["Arranque", "start.bat, instalar_dependencias.bat"],
    ["Deploy", "Procfile, railway.toml, runtime.txt"],
    ["Base local", "gormet_pos.db"],
    ["Backend core", "__init__.py, database.py, main.py, models.py, schemas.py, seed_data.py"],
    ["Backend routes", "__init__.py, caja.py, clientes.py, config.py, menu.py, mesas.py, pedidos.py, reportes.py, whatsapp_webhook.py"],
    ["Backend service", "services/__init__.py, services/whatsapp_service.py"],
    ["Frontend pages", "admin.html, clientes.html, cocina.html, index.html, menu-dia.html, pos.html, reportes.html, whatsapp.html"],
    ["Frontend assets", "assets/css/style.css, assets/js/api.js"],
    ["WhatsApp bot", "__init__.py, bot.py, pipeline.py, prompts.py, handlers/__init__.py"],
  ];
  addTable(s, 120, 250, [{ label: "Grupo", w: 310 }, { label: "Archivos", w: 1300 }], rows, {
    name: "all-files",
    rowH: 60,
    size: 18,
    headerFill: C.blue,
    headerColor: C.ink,
  });
}

function slide22(p, n) {
  const s = addSlide(p, C.ink);
  addRect(s, 0, 0, W, H, C.ink, "final-bg", NO);
  addRect(s, 0, H - 170, W, 170, C.orange, "final-band", NO);
  addText(s, "Resultado", M, 120, 900, 85, {
    name: "final-title",
    typeface: FONT.display,
    size: 78,
    bold: true,
    color: C.white,
  });
  addText(s, "GourmetPOS queda explicado como un sistema completo: datos, API, interfaz, WhatsApp IA y despliegue.", M, 250, 1380, 120, {
    name: "final-claim",
    size: 40,
    bold: true,
    color: "#DCE7F5",
  });
  const outcomes = [
    ["Entendible", "Cada archivo tiene rol claro."],
    ["Presentable", "Arquitectura visual para exponer."],
    ["Escalable", "Capas separadas para mantener."],
  ];
  outcomes.forEach((o, i) => {
    addText(s, o[0], M + i * 560, 505, 420, 50, { name: `final-out-${i}-title`, size: 35, bold: true, color: [C.teal, C.blue, C.yellow][i] });
    addText(s, o[1], M + i * 560, 565, 420, 70, { name: `final-out-${i}-body`, size: 26, color: "#B9C6D6" });
  });
  addText(s, "PDF profesional generado desde el repositorio local", M, H - 112, 900, 42, {
    name: "final-meta",
    size: 28,
    bold: true,
    color: C.white,
  });
  addFooter(s, n, true);
}

async function build() {
  await ensureDirs();
  const p = Presentation.create({ slideSize: { width: W, height: H } });
  const slides = [
    slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8, slide9, slide10, slide11,
    slide12, slide13, slide14, slide15, slide16, slide17, slide18, slide19, slide20, slide21, slide22,
  ];
  slides.forEach((fn, idx) => fn(p, idx + 1));

  const pptxPath = path.join(OUT_DIR, "gourmetpos_ia_construccion.pptx");
  await (await PresentationFile.exportPptx(p)).save(pptxPath);

  const pptxBuffer = await fs.readFile(pptxPath);
  const imported = await PresentationFile.importPptx(pptxBuffer);
  const previewFiles = [];
  const layoutFiles = [];
  for (let i = 0; i < imported.slides.count; i += 1) {
    const slide = imported.slides.getItem(i);
    const pngPath = path.join(PREVIEW_DIR, `slide-${String(i + 1).padStart(2, "0")}.png`);
    await saveBlob(await imported.export({ slide, format: "png" }), pngPath);
    previewFiles.push(pngPath);
    try {
      const layoutPath = path.join(LAYOUT_DIR, `slide-${String(i + 1).padStart(2, "0")}.json`);
      const layoutBlob = await imported.export({ slide, format: "layout" });
      await fs.writeFile(layoutPath, await layoutBlob.text(), "utf8");
      layoutFiles.push(layoutPath);
    } catch {
      // Layout export is helpful but not required for the rendered-preview PDF.
    }
  }

  const qa = {
    generatedAt: new Date().toISOString(),
    slideCount: imported.slides.count,
    pptxPath,
    previewDir: PREVIEW_DIR,
    layoutDir: LAYOUT_DIR,
    previews: previewFiles.map((f) => path.relative(WORKSPACE, f)),
    layouts: layoutFiles.map((f) => path.relative(WORKSPACE, f)),
    importedPptxRendered: true,
    notes: [
      "Rendered previews were exported after reopening the saved PPTX buffer.",
      "PDF assembly is performed from these full-size PNG previews.",
    ],
  };
  await fs.writeFile(path.join(SCRATCH, "qa_report.json"), JSON.stringify(qa, null, 2), "utf8");
  console.log(JSON.stringify(qa, null, 2));
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
