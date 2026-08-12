"""
GourmetPOS ERP - Backend FastAPI
Versión 2.0 Profesional
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
from typing import List
import asyncio
import json
import os

from datetime import datetime
from .database import engine, Base, SessionLocal
from .models import MensajeProgramado, ConfigRestaurante
from .models import *  # noqa: F401,F403
from .seed_data import seed_database
from .routes import mesas, menu, pedidos, caja, clientes, reportes, whatsapp_webhook, config, suscripciones
from .services.whatsapp_service import WhatsAppService


# ── SCHEDULER DE MENSAJES PROGRAMADOS ────────────────────────────────────────

DIAS_SEMANA = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]

async def _ejecutar_scheduler():
    """Revisa cada minuto si hay mensajes programados que enviar."""
    import json as _json
    while True:
        await asyncio.sleep(60)
        try:
            ahora   = datetime.now()
            hora_hm = ahora.strftime("%H:%M")
            dia_hoy = DIAS_SEMANA[ahora.weekday()]

            db = SessionLocal()
            try:
                msgs = db.query(MensajeProgramado).filter(
                    MensajeProgramado.activo == True,
                    MensajeProgramado.hora   == hora_hm,
                ).all()

                for m in msgs:
                    dias_config = [d.strip().lower() for d in (m.dias or "").split(",")]
                    if dia_hoy not in dias_config:
                        continue
                    # Evitar doble envío en el mismo minuto
                    if m.ultimo_envio and m.ultimo_envio.strftime("%Y-%m-%d %H:%M") == ahora.strftime("%Y-%m-%d %H:%M"):
                        continue

                    tk  = db.query(ConfigRestaurante).filter(ConfigRestaurante.clave == "whatsapp_token").first()
                    pid = db.query(ConfigRestaurante).filter(ConfigRestaurante.clave == "whatsapp_phone_id").first()
                    svc = WhatsAppService(
                        token    = (tk.valor  if tk  else None) or os.getenv("WA_TOKEN",    ""),
                        phone_id = (pid.valor if pid else None) or os.getenv("WA_PHONE_ID", ""),
                        db       = db,
                    )
                    botones = _json.loads(m.botones_json or "[]")
                    if m.tipo == "botones" and botones:
                        await svc.envio_masivo_botones(m.mensaje, botones)
                    else:
                        await svc.envio_masivo_texto(m.mensaje)

                    m.ultimo_envio = ahora
                    db.commit()
                    print(f"[SCHEDULER] Enviado: '{m.nombre}' a las {hora_hm}")

            finally:
                db.close()
        except Exception as e:
            print(f"[SCHEDULER ERROR] {e}")


# ── LIFESPAN ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    # Iniciar scheduler de mensajes programados
    asyncio.create_task(_ejecutar_scheduler())
    yield


# ── APP ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GourmetPOS ERP",
    description="Sistema ERP completo para restaurantes con WhatsApp integrado",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── WEBSOCKET MANAGER ─────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await manager.broadcast({"tipo": "ping", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ── RUTAS API ──────────────────────────────────────────────────────────────────

app.include_router(mesas.router,               prefix="/api/mesas",      tags=["Mesas"])
app.include_router(menu.router,                prefix="/api/menu",       tags=["Menu"])
app.include_router(pedidos.router,             prefix="/api/pedidos",    tags=["Pedidos"])
app.include_router(caja.router,                prefix="/api/caja",       tags=["Caja"])
app.include_router(clientes.router,            prefix="/api/clientes",   tags=["Clientes"])
app.include_router(reportes.router,            prefix="/api/reportes",   tags=["Reportes"])
app.include_router(whatsapp_webhook.router,    prefix="/api/whatsapp",   tags=["WhatsApp"])
app.include_router(config.router,              prefix="/api/config",     tags=["Config"])
app.include_router(suscripciones.router,       prefix="/api/suscripciones", tags=["Suscripciones"])


# ── HEALTH CHECK ──────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0", "app": "GourmetPOS ERP"}


# ── SERVIR FRONTEND ────────────────────────────────────────────────────────────

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
