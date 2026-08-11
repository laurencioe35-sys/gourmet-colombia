"""
WhatsApp Business Cloud API — Motor de Mensajes Interactivos.

TIPOS DE MENSAJES SOPORTADOS:
  1. Texto plano
  2. Imagen con caption
  3. Botones interactivos (máx 3)
  4. Lista de opciones (máx 10 por sección)
  5. Template de proactivo
  6. Ubicación

FUENTE DE DATOS:
  - Menú       → tablas Categoria + Producto (DB)
  - Contactos  → tabla Cliente + ConversacionWhatsApp (DB)
  - Config     → tabla ConfigRestaurante (DB)
"""
import httpx
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import (
    ConversacionWhatsApp, Cliente, Pedido, DetallePedido,
    Producto, Categoria, EstadoPedido, CanalPedido, ConfigRestaurante
)


# ══════════════════════════════════════════════════════════════════════════════
#   BUILDERS — Constructores de payload JSON para la API de Meta
# ══════════════════════════════════════════════════════════════════════════════

def _build_text(to: str, body: str) -> dict:
    """Mensaje de texto plano."""
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body}
    }


def _build_image(to: str, image_url: str, caption: str = "") -> dict:
    """Mensaje con imagen y caption. image_url debe ser https:// público."""
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "image",
        "image": {"link": image_url, "caption": caption}
    }


def _build_buttons(to: str, body: str, buttons: list, header: str = None, footer: str = None) -> dict:
    """
    Botones interactivos — máximo 3 botones.
    buttons = [{"id": "btn_id", "title": "Texto"}, ...]
    """
    interactive: dict = {
        "type": "button",
        "body": {"text": body},
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": b["id"], "title": b["title"][:20]}}
                for b in buttons[:3]
            ]
        }
    }
    if header:
        interactive["header"] = {"type": "text", "text": header}
    if footer:
        interactive["footer"] = {"text": footer}
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": interactive
    }


def _build_list(to: str, body: str, button_label: str, sections: list,
                header: str = None, footer: str = None) -> dict:
    """
    Mensaje tipo lista — hasta 10 filas por sección, múltiples secciones.
    sections = [{"title": "...", "rows": [{"id":"..","title":"..","description":".."}]}]
    """
    interactive: dict = {
        "type": "list",
        "body": {"text": body},
        "action": {"button": button_label[:20], "sections": sections}
    }
    if header:
        interactive["header"] = {"type": "text", "text": header}
    if footer:
        interactive["footer"] = {"text": footer}
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": interactive
    }


def _build_template(to: str, template_name: str, lang: str = "es",
                    components: list = None) -> dict:
    """
    Mensaje de plantilla (template) — para mensajes proactivos pre-aprobados.
    Requiere aprobación previa en Meta Business Manager.
    """
    payload: dict = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang}
        }
    }
    if components:
        payload["template"]["components"] = components
    return payload


def _build_location(to: str, lat: float, lon: float, name: str, address: str) -> dict:
    """Envía la ubicación del restaurante."""
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "location",
        "location": {"latitude": lat, "longitude": lon, "name": name, "address": address}
    }


# ══════════════════════════════════════════════════════════════════════════════
#   WHATSAPP SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class WhatsAppService:

    META_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, token: str, phone_id: str, db: Session):
        self.token    = token
        self.phone_id = phone_id
        self.db       = db
        self._cfg_cache: dict = {}

    # ── CONFIG desde DB ────────────────────────────────────────────────────────

    def cfg(self, clave: str, default: str = "") -> str:
        if clave not in self._cfg_cache:
            row = self.db.query(ConfigRestaurante).filter(
                ConfigRestaurante.clave == clave
            ).first()
            self._cfg_cache[clave] = row.valor if row else default
        return self._cfg_cache[clave]

    # ── ENVÍO HTTP a Meta Graph API ────────────────────────────────────────────

    async def _send(self, payload: dict) -> dict:
        """Envía el payload a la API de Meta. Sin token → imprime para depuración."""
        if not self.token or not self.phone_id:
            tipo = payload.get("type", "?")
            dest = payload.get("to", "?")
            print(f"[WA-SIM] tipo={tipo} → {dest} | payload={json.dumps(payload, ensure_ascii=False)[:200]}")
            return {"simulated": True, "tipo": tipo}

        url = f"{self.META_URL}/{self.phone_id}/messages"
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
            )
            data = resp.json()
            if resp.status_code != 200:
                print(f"[WA-ERROR] {resp.status_code} → {json.dumps(data, ensure_ascii=False)}")
            return data

    # ── MÉTODOS PÚBLICOS DE ENVÍO ──────────────────────────────────────────────

    async def enviar_texto(self, to: str, body: str) -> dict:
        return await self._send(_build_text(to, body))

    async def enviar_imagen(self, to: str, image_url: str, caption: str = "") -> dict:
        return await self._send(_build_image(to, image_url, caption))

    async def enviar_botones(self, to: str, body: str, buttons: list,
                              header: str = None, footer: str = None) -> dict:
        return await self._send(_build_buttons(to, body, buttons, header, footer))

    async def enviar_lista(self, to: str, body: str, button_label: str,
                            sections: list, header: str = None, footer: str = None) -> dict:
        return await self._send(_build_list(to, body, button_label, sections, header, footer))

    async def enviar_template(self, to: str, template_name: str,
                               lang: str = "es", components: list = None) -> dict:
        return await self._send(_build_template(to, template_name, lang, components))

    async def enviar_ubicacion(self, to: str) -> dict:
        lat  = float(self.cfg("lat",  "-12.0464"))
        lon  = float(self.cfg("lon",  "-77.0428"))
        name = self.cfg("nombre", "GourmetPOS")
        addr = self.cfg("direccion", "Bogotá, Colombia")
        return await self._send(_build_location(to, lat, lon, name, addr))

    # ── CARGA DEL MENÚ DESDE LA BASE DE DATOS ─────────────────────────────────

    def cargar_menu(self) -> dict:
        """
        Lee Categoria + Producto de la BD y devuelve un dict estructurado:
        {
          cat_id: {
            "nombre": str, "emoji": str,
            "productos": [{"id", "nombre", "precio", "emoji", "descripcion", "imagen_url"}]
          }
        }
        Este dict es la FUENTE de datos de todos los mensajes interactivos del bot.
        """
        menu: dict = {}
        cats = self.db.query(Categoria).filter(Categoria.activo == True).order_by(Categoria.orden).all()
        for cat in cats:
            prods = self.db.query(Producto).filter(
                Producto.categoria_id == cat.id,
                Producto.disponible == True
            ).order_by(Producto.precio).all()
            menu[cat.id] = {
                "nombre":    cat.nombre,
                "emoji":     cat.emoji or "🍽️",
                "productos": [
                    {
                        "id":          p.id,
                        "nombre":      p.nombre,
                        "precio":      p.precio,
                        "emoji":       p.emoji or "🍽️",
                        "descripcion": p.descripcion or "",
                        "imagen_url":  getattr(p, "imagen_url", None) or "",
                        "tiempo_prep": getattr(p, "tiempo_prep", 15) or 15,
                    }
                    for p in prods
                ]
            }
        return menu

    def cargar_contactos(self) -> list:
        """
        Carga todos los números de teléfono de la BD (tabla Cliente).
        Combina con ConversacionWhatsApp para tener nombre + teléfono.
        Devuelve: [{"telefono": str, "nombre": str, "pedidos": int}]
        """
        clientes = self.db.query(Cliente).filter(
            Cliente.telefono.isnot(None),
            Cliente.telefono != ""
        ).all()
        convs = {
            c.telefono: c.nombre
            for c in self.db.query(ConversacionWhatsApp).all()
        }
        resultado = []
        telefonos_vistos = set()
        for c in clientes:
            if c.telefono and c.telefono not in telefonos_vistos:
                telefonos_vistos.add(c.telefono)
                resultado.append({
                    "telefono": c.telefono,
                    "nombre":   c.nombre or convs.get(c.telefono, "Cliente"),
                    "pedidos":  c.total_pedidos or 0,
                })
        # Agregar los que solo tienen conversación (sin cliente aún)
        for tel, nom in convs.items():
            if tel not in telefonos_vistos:
                resultado.append({"telefono": tel, "nombre": nom, "pedidos": 0})
        return resultado

    # ── ENVÍO MASIVO ───────────────────────────────────────────────────────────

    async def envio_masivo_texto(self, mensaje: str) -> dict:
        """Envía texto a todos los contactos de la BD."""
        contactos = self.cargar_contactos()
        ok, error = 0, 0
        for c in contactos:
            try:
                await self.enviar_texto(c["telefono"], mensaje)
                ok += 1
            except Exception:
                error += 1
        return {"total": len(contactos), "enviados": ok, "errores": error}

    async def envio_masivo_botones(self, body: str, buttons: list) -> dict:
        """Envía mensaje con botones a todos los contactos."""
        contactos = self.cargar_contactos()
        ok, error = 0, 0
        for c in contactos:
            try:
                await self.enviar_botones(c["telefono"], body, buttons)
                ok += 1
            except Exception:
                error += 1
        return {"total": len(contactos), "enviados": ok, "errores": error}

    async def envio_menu_del_dia(self) -> dict:
        """
        Envío masivo del menú del día:
        1. Imagen del restaurante (si hay URL configurada)
        2. Botones para ver el menú
        """
        nombre_rest = self.cfg("nombre", "Tu Restaurante")
        imagen_url  = self.cfg("imagen_menu_url", "")
        contactos   = self.cargar_contactos()
        ok, error = 0, 0

        for c in contactos:
            try:
                tel = c["telefono"]
                nom = c["nombre"]

                if imagen_url:
                    await self.enviar_imagen(
                        tel, imagen_url,
                        f"🍽️ *{nombre_rest}*\n¡Hola {nom}! Tenemos el menú del día para ti."
                    )

                await self.enviar_botones(
                    tel,
                    f"👋 ¡Hola {nom}! Hoy tenemos platos especiales.\n¿Qué deseas pedir?",
                    [
                        {"id": "ver_menu",    "title": "🍽️ Ver Menú"},
                        {"id": "mis_pedidos", "title": "📦 Mis Pedidos"},
                        {"id": "ubicacion",   "title": "📍 Ubicación"},
                    ]
                )
                ok += 1
            except Exception:
                error += 1

        return {"total": len(contactos), "enviados": ok, "errores": error}

    # ══════════════════════════════════════════════════════════════════════════
    #   FLUJO DE PEDIDO — Pipeline Johnson
    # ══════════════════════════════════════════════════════════════════════════

    async def procesar_mensaje(self, telefono: str, mensaje: str, nombre: str):
        conv  = self._get_or_create_conv(telefono, nombre)
        datos = json.loads(conv.datos_pedido_json or "{}")
        msg   = mensaje.strip().lower()

        # Comandos globales (siempre disponibles)
        if msg in ["hola", "inicio", "start", "/start", "menu", "menú", "reiniciar"]:
            nuevo_estado, nuevos_datos = await self._paso_bienvenida(telefono, msg, datos)
        elif msg == "ubicacion":
            await self.enviar_ubicacion(telefono)
            nuevo_estado, nuevos_datos = conv.estado_flujo, datos
        else:
            handler = {
                "inicio":              self._paso_bienvenida,
                "menu_categorias":     self._paso_categorias,
                "menu_productos":      self._paso_productos,
                "detalle_producto":    self._paso_detalle,
                "agregar_complemento": self._paso_complementos,
                "confirmar_pedido":    self._paso_confirmacion,
                "seleccionar_pago":    self._paso_pago,
                "pedido_enviado":      self._paso_post_pago,
            }.get(conv.estado_flujo, self._paso_bienvenida)
            nuevo_estado, nuevos_datos = await handler(telefono, msg, datos)

        conv.estado_flujo      = nuevo_estado
        conv.datos_pedido_json = json.dumps(nuevos_datos, ensure_ascii=False)
        conv.ultimo_mensaje    = mensaje
        conv.updated_at        = datetime.utcnow()
        conv.activa            = True
        self.db.commit()

    # ── PASO 1: BIENVENIDA ────────────────────────────────────────────────────

    async def _paso_bienvenida(self, tel: str, msg: str = "", datos: dict = None):
        if datos is None:
            datos = {}
        nombre_rest = self.cfg("nombre", "Tu Restaurante")
        await self.enviar_botones(
            tel,
            f"¡Hola! 😊 Bienvenido a *{nombre_rest}* 🍽️\n\n"
            "El cliente solo toca la pantalla.\n¿Qué deseas hacer?",
            [
                {"id": "ver_menu",    "title": "🍽️ Ver Menú"},
                {"id": "mis_pedidos", "title": "📦 Mis Pedidos"},
                {"id": "ubicacion",   "title": "📍 Ubicación"},
            ],
            header="PEDIDOS SIN ESCRIBIR"
        )
        return "menu_categorias", {}

    # ── PASO 2: CATEGORÍAS DEL MENÚ ───────────────────────────────────────────

    async def _paso_categorias(self, tel: str, msg: str, datos: dict):
        if msg == "mis_pedidos":
            return await self._mostrar_mis_pedidos(tel, datos)

        menu = self.cargar_menu()
        if not menu:
            await self.enviar_texto(tel, "😔 El menú no está disponible en este momento. Intenta más tarde.")
            return "inicio", {}

        # Solo categorías con productos disponibles
        rows = [
            {
                "id":          f"cat_{cat_id}",
                "title":       f"{info['emoji']} {info['nombre']}"[:24],
                "description": f"{len(info['productos'])} opciones disponibles"[:72]
            }
            for cat_id, info in menu.items()
            if info["productos"]
        ]

        # Si no hay productos en ninguna categoría, avisamos con texto
        if not rows:
            nombre_rest = self.cfg("nombre", "Tu Restaurante")
            await self.enviar_texto(
                tel,
                f"🍽️ *{nombre_rest}*\n\n"
                "El menú está siendo preparado por el restaurante.\n\n"
                "📲 Vuelve pronto o llámanos para hacer tu pedido.\n\n"
                "Escribe *hola* para volver al inicio."
            )
            return "inicio", {}

        await self.enviar_lista(
            tel,
            "🍽️ *Nuestro Menú Completo*\n\nSelecciona una categoría para ver los platos disponibles:",
            "Ver Categorías",
            [{"title": "Categorías", "rows": rows[:10]}],
            header=self.cfg("nombre", "Tu Restaurante"),
            footer="Toca una opción para continuar 👆"
        )
        return "menu_productos", {**datos, "_menu_cache": True}

    # ── PASO 3: PRODUCTOS DE CATEGORÍA ───────────────────────────────────────

    async def _paso_productos(self, tel: str, msg: str, datos: dict):
        if not msg.startswith("cat_"):
            await self.enviar_texto(tel, "👆 Por favor selecciona una categoría del menú.")
            return "menu_productos", datos

        try:
            cat_id = int(msg.replace("cat_", ""))
        except ValueError:
            return "menu_categorias", datos

        menu = self.cargar_menu()
        cat  = menu.get(cat_id)
        if not cat or not cat["productos"]:
            await self.enviar_texto(tel, "😔 No hay productos disponibles en esta categoría.")
            return "menu_categorias", datos

        moneda = self.cfg("moneda", "$")

        # Si la categoría tiene imagen configurada, enviarla primero
        img_cat = self.cfg(f"img_cat_{cat_id}", "")
        if img_cat:
            await self.enviar_imagen(tel, img_cat, f"{cat['emoji']} *{cat['nombre']}*")

        # Lista de productos (máx 10 por sección de WA)
        rows = [
            {
                "id":          f"prod_{p['id']}",
                "title":       f"{p['emoji']} {p['nombre']}"[:24],
                "description": f"{moneda} {p['precio']:.2f} · ⏱️ {p['tiempo_prep']} min"[:72]
            }
            for p in cat["productos"][:10]
        ]

        await self.enviar_lista(
            tel,
            f"{cat['emoji']} *{cat['nombre']}*\n\nElige tu plato:",
            "Ver Platos",
            [{"title": cat["nombre"], "rows": rows}],
            footer="↩ Escribe 'menú' para volver"
        )
        datos["cat_id"] = cat_id
        return "detalle_producto", datos

    # ── PASO 4: DETALLE DEL PRODUCTO ──────────────────────────────────────────

    async def _paso_detalle(self, tel: str, msg: str, datos: dict):
        if not msg.startswith("prod_"):
            await self.enviar_texto(tel, "👆 Por favor selecciona un plato de la lista.")
            return "detalle_producto", datos

        try:
            prod_id = int(msg.replace("prod_", ""))
        except ValueError:
            return "menu_productos", datos

        prod = self.db.query(Producto).filter(Producto.id == prod_id).first()
        if not prod:
            await self.enviar_texto(tel, "❌ Producto no disponible.")
            return "menu_categorias", datos

        moneda = self.cfg("moneda", "$")

        # Si el producto tiene imagen, enviarla primero
        img_url = getattr(prod, "imagen_url", None) or ""
        caption = (
            f"🍽️ *{prod.nombre}*\n"
            f"_{prod.descripcion}_\n"
            f"💰 *{moneda} {prod.precio:.2f}* · ⏱️ {getattr(prod,'tiempo_prep',15)} min"
        )
        if img_url:
            await self.enviar_imagen(tel, img_url, caption)

        await self.enviar_botones(
            tel,
            f"{'🖼️' if not img_url else ''}{caption if not img_url else ''}\n\n"
            "¿Cuántas unidades deseas?",
            [
                {"id": f"qty_1_{prod_id}", "title": "1️⃣ Una"},
                {"id": f"qty_2_{prod_id}", "title": "2️⃣ Dos"},
                {"id": f"qty_3_{prod_id}", "title": "3️⃣ Tres"},
            ],
            footer="Escribe 4, 5... para más unidades"
        )
        datos["prod_seleccionado"] = prod_id
        return "agregar_complemento", datos

    # ── PASO 5: COMPLEMENTOS (BEBIDAS) ────────────────────────────────────────

    async def _paso_complementos(self, tel: str, msg: str, datos: dict):
        # Procesar cantidad seleccionada
        if msg.startswith("qty_"):
            partes = msg.split("_")
            if len(partes) >= 3:
                cantidad = int(partes[1])
                prod_id  = int(partes[2])
                prod = self.db.query(Producto).filter(Producto.id == prod_id).first()
                if prod:
                    carrito = datos.get("carrito", [])
                    carrito.append({
                        "prod_id":  prod.id,
                        "nombre":   prod.nombre,
                        "precio":   prod.precio,
                        "cantidad": cantidad,
                        "subtotal": round(prod.precio * cantidad, 2),
                        "emoji":    prod.emoji or "🍽️",
                    })
                    datos["carrito"] = carrito
        elif msg.isdigit() and datos.get("prod_seleccionado"):
            cantidad = max(1, min(int(msg), 20))
            prod_id  = datos["prod_seleccionado"]
            prod = self.db.query(Producto).filter(Producto.id == prod_id).first()
            if prod:
                carrito = datos.get("carrito", [])
                carrito.append({
                    "prod_id":  prod.id,
                    "nombre":   prod.nombre,
                    "precio":   prod.precio,
                    "cantidad": cantidad,
                    "subtotal": round(prod.precio * cantidad, 2),
                    "emoji":    prod.emoji or "🍽️",
                })
                datos["carrito"] = carrito

        # Cargar bebidas desde la BD
        bebidas = self.db.query(Producto).join(Categoria).filter(
            Categoria.nombre.ilike("%bebida%"),
            Producto.disponible == True
        ).limit(8).all()

        moneda = self.cfg("moneda", "$")

        if bebidas:
            rows = [
                {
                    "id":          f"beb_{b.id}",
                    "title":       f"{b.emoji} {b.nombre}"[:24],
                    "description": f"{moneda} {b.precio:.2f}"[:72]
                }
                for b in bebidas
            ]
            await self.enviar_lista(
                tel,
                "🥤 *¿Deseas agregar una bebida?*\n\nSelecciona o escribe 'no' para continuar:",
                "Agregar Bebida",
                [{"title": "Bebidas Disponibles", "rows": rows}]
            )
            await self.enviar_botones(
                tel,
                "O continúa sin bebida:",
                [
                    {"id": "no_bebida", "title": "✅ Sin bebida"},
                    {"id": "ver_menu",  "title": "➕ Agregar más"},
                ]
            )
        else:
            await self._mostrar_resumen(tel, datos)
            return "seleccionar_pago", datos

        return "confirmar_pedido", datos

    # ── PASO 6: CONFIRMACIÓN / RESUMEN ───────────────────────────────────────

    async def _paso_confirmacion(self, tel: str, msg: str, datos: dict):
        if msg.startswith("beb_"):
            try:
                beb_id = int(msg.replace("beb_", ""))
                beb    = self.db.query(Producto).filter(Producto.id == beb_id).first()
                if beb:
                    carrito = datos.get("carrito", [])
                    carrito.append({
                        "prod_id":  beb.id,
                        "nombre":   beb.nombre,
                        "precio":   beb.precio,
                        "cantidad": 1,
                        "subtotal": beb.precio,
                        "emoji":    beb.emoji or "🥤",
                    })
                    datos["carrito"] = carrito
            except ValueError:
                pass

        if msg == "ver_menu":
            return await self._paso_categorias(tel, msg, datos)

        await self._mostrar_resumen(tel, datos)
        return "seleccionar_pago", datos

    async def _mostrar_resumen(self, tel: str, datos: dict):
        carrito = datos.get("carrito", [])
        if not carrito:
            await self.enviar_texto(tel, "🛒 Tu carrito está vacío. Escribe 'menú' para ver las opciones.")
            return

        moneda    = self.cfg("moneda", "$")
        igv_rate  = float(self.cfg("iva", "0.19"))
        subtotal  = sum(i["subtotal"] for i in carrito)
        igv       = round(subtotal * igv_rate, 2)
        total     = round(subtotal + igv, 2)

        lineas = "\n".join(
            f"  {i['emoji']} {i['nombre']} x{i['cantidad']} = {moneda} {i['subtotal']:.2f}"
            for i in carrito
        )
        datos.update({"subtotal": subtotal, "igv": igv, "total": total})

        await self.enviar_botones(
            tel,
            f"🧾 *Resumen de tu Pedido*\n\n{lineas}\n\n"
            f"Subtotal:  {moneda} {subtotal:.2f}\n"
            f"IVA (19%): {moneda} {igv:.2f}\n"
            f"*TOTAL:    {moneda} {total:.2f}*",
            [
                {"id": "pagar_ahora", "title": "💳 Pagar Ahora"},
                {"id": "modificar",   "title": "✏️ Modificar"},
            ],
            header="PEDIDO LISTO",
            footer="Elige cómo pagar 👆"
        )

    # ── PASO 7: PAGO ──────────────────────────────────────────────────────────

    async def _paso_pago(self, tel: str, msg: str, datos: dict):
        if msg == "modificar":
            return await self._paso_categorias(tel, msg, datos)

        moneda = self.cfg("moneda", "$")
        nequi      = self.cfg("nequi", "No configurado")
        daviplata  = self.cfg("daviplata", "No configurado")
        total  = datos.get("total", 0)

        await self.enviar_lista(
            tel,
            f"💰 Total a pagar: *{moneda} {total:.2f}*\n\n"
            f"📱 *Nequi:* {nequi}\n"
            f"📱 *Daviplata:* {daviplata}\n\n"
            "Elige tu método de pago:",
            "Ver Métodos",
            [{
                "title": "Métodos de Pago",
                "rows": [
                    {"id": "pago_nequi",      "title": "💜 Nequi",              "description": f"Enviar a {nequi}"[:72]},
                    {"id": "pago_daviplata", "title": "🔵 Daviplata",          "description": f"Enviar a {daviplata}"[:72]},
                    {"id": "pago_tarjeta",  "title": "💳 Tarjeta Visa/MC",    "description": "Visa o Mastercard"},
                    {"id": "pago_efectivo", "title": "💵 Efectivo",           "description": "Contra entrega"},
                ]
            }],
            footer="Selecciona tu método 👆"
        )
        return "pedido_enviado", datos

    # ── PASO 8: PAGO CONFIRMADO → COCINA ─────────────────────────────────────

    async def _paso_post_pago(self, tel: str, msg: str, datos: dict):
        metodo = {
            "pago_nequi":     "Nequi",
            "pago_daviplata": "Daviplata",
            "pago_tarjeta": "Tarjeta",
            "pago_efectivo":"Efectivo",
        }.get(msg, "Efectivo")
        datos["metodo_pago"] = metodo

        pedido_id = await self._registrar_pedido_en_bd(tel, datos)
        moneda    = self.cfg("moneda", "$")
        total     = datos.get("total", 0)

        await self.enviar_texto(
            tel,
            f"✅ *¡Pago Confirmado!*\n\n"
            f"🎉 Pedido *#{pedido_id}* registrado\n"
            f"💰 Total: {moneda} {total:.2f}\n"
            f"💳 Método: {metodo}\n\n"
            f"⏱️ *Tiempo estimado: 35-40 min*\n\n"
            f"👨‍🍳 Tu pedido ya está en cocina.\n"
            f"Te avisaremos cuando esté listo. 🙏"
        )
        await self.enviar_botones(
            tel,
            "¿Algo más?",
            [
                {"id": "hola",       "title": "🔄 Nuevo Pedido"},
                {"id": "mis_pedidos","title": "📦 Ver mis Pedidos"},
            ]
        )
        return "inicio", {}

    # ── MIS PEDIDOS ───────────────────────────────────────────────────────────

    async def _mostrar_mis_pedidos(self, tel: str, datos: dict):
        cliente = self.db.query(Cliente).filter(Cliente.telefono == tel).first()
        if not cliente:
            await self.enviar_texto(tel, "📭 Aún no tienes pedidos registrados.\nEscribe 'menú' para hacer tu primer pedido.")
            return "menu_categorias", datos

        pedidos = self.db.query(Pedido).filter(
            Pedido.cliente_id == cliente.id
        ).order_by(Pedido.created_at.desc()).limit(5).all()

        if not pedidos:
            await self.enviar_texto(tel, "📭 No tienes pedidos registrados aún.")
        else:
            moneda = self.cfg("moneda", "$")
            lineas = "\n".join(
                f"• Pedido #{p.id} — {moneda} {p.total:.2f} — {p.estado.value.upper()}"
                for p in pedidos
            )
            await self.enviar_texto(tel, f"📦 *Tus últimos pedidos:*\n\n{lineas}")

        return "menu_categorias", datos

    # ── REGISTRAR PEDIDO EN BD ────────────────────────────────────────────────

    async def _registrar_pedido_en_bd(self, telefono: str, datos: dict) -> int:
        # Buscar o crear cliente
        cliente = self.db.query(Cliente).filter(Cliente.telefono == telefono).first()
        if not cliente:
            conv = self.db.query(ConversacionWhatsApp).filter(
                ConversacionWhatsApp.telefono == telefono
            ).first()
            cliente = Cliente(
                nombre   = conv.nombre if conv else "Cliente WhatsApp",
                telefono = telefono,
            )
            self.db.add(cliente)
            self.db.flush()

        # Generar número de ticket
        total_pedidos = self.db.query(Pedido).count()
        ticket = f"WA-{datetime.now().strftime('%Y%m%d')}-{total_pedidos+1:04d}"

        pedido = Pedido(
            cliente_id    = cliente.id,
            canal         = CanalPedido.whatsapp,
            estado        = EstadoPedido.pendiente,
            subtotal      = datos.get("subtotal", 0),
            igv           = datos.get("igv", 0),
            total         = datos.get("total", 0),
            numero_ticket = ticket,
        )
        self.db.add(pedido)
        self.db.flush()

        for item in datos.get("carrito", []):
            self.db.add(DetallePedido(
                pedido_id      = pedido.id,
                producto_id    = item["prod_id"],
                cantidad       = item["cantidad"],
                precio_unitario= item["precio"],
                subtotal       = item["subtotal"],
            ))

        cliente.total_pedidos = (cliente.total_pedidos or 0) + 1
        self.db.commit()
        return pedido.id

    # ── HELPER: CONVERSACIÓN ──────────────────────────────────────────────────

    def _get_or_create_conv(self, telefono: str, nombre: str) -> ConversacionWhatsApp:
        conv = self.db.query(ConversacionWhatsApp).filter(
            ConversacionWhatsApp.telefono == telefono
        ).first()
        if not conv:
            conv = ConversacionWhatsApp(telefono=telefono, nombre=nombre, estado_flujo="inicio")
            self.db.add(conv)
            self.db.flush()
        elif nombre and nombre not in ("Cliente", ""):
            conv.nombre = nombre
        return conv
