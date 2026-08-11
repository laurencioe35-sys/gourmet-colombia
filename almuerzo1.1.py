#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          RESTAURANTE ERP — Sistema de Gestión Completo           ║
║   Versión 2.0 | POS + Cocina + Reportes + Administración         ║
╚══════════════════════════════════════════════════════════════════╝

Dependencias:
    pip install Pillow requests matplotlib pandas openpyxl

Características:
  • Dashboard con KPIs en tiempo real
  • Mapa visual de mesas (hasta 20 mesas)
  • Carta con imágenes y categorías
  • Caja: Efectivo, Tarjeta, Yape, Plin, Nequi, Daviplata
  • WhatsApp al cliente con resumen de pedido
  • Impresión de ticket (ESC/POS o TXT)
  • Display de cocina
  • Reportes y exportación a Excel
  • Administración de carta y configuración
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import N LAS ETIQUETA
import time
import datetime
import json
import os
import sys
import math
import subprocess
import webbrowser
import urllib.parse
from collections import defaultdict

# ── Importaciones opcionales ──────────────────────────────────────
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL_OK = True
except ImportError:
    MPL_OK = False

try:
    import pandas as pd
    import openpyxl
    EXCEL_OK = True
except ImportError:
    EXCEL_OK = False

# ══════════════════════════════════════════════════════════════════
#  PALETA DE COLORES Y CONSTANTES
# ══════════════════════════════════════════════════════════════════
C = {
    "bg":          "#0F1117",
    "surface":     "#1A1D27",
    "surface2":    "#22263A",
    "surface3":    "#2A2F45",
    "border":      "#333752",
    "accent":      "#FF6B35",
    "accent2":     "#FFB800",
    "accent3":     "#00D4A1",
    "blue":        "#4C9BE8",
    "purple":      "#9B59B6",
    "red":         "#E74C3C",
    "green":       "#27AE60",
    "yellow":      "#F39C12",
    "text":        "#F0F2FF",
    "text2":       "#A8AECA",
    "text3":       "#6B7399",
    "sidebar":     "#13161F",
    "card":        "#1E2235",
    "hover":       "#252940",
    "white":       "#FFFFFF",
}

FONTS = {
    "title":   ("Segoe UI", 20, "bold"),
    "h1":      ("Segoe UI", 16, "bold"),
    "h2":      ("Segoe UI", 13, "bold"),
    "body":    ("Segoe UI", 11),
    "small":   ("Segoe UI", 9),
    "mono":    ("Courier New", 10),
    "price":   ("Segoe UI", 14, "bold"),
    "kpi":     ("Segoe UI", 26, "bold"),
    "nav":     ("Segoe UI", 11),
}

# ══════════════════════════════════════════════════════════════════
#  DATOS DE CONFIGURACIÓN DEL RESTAURANTE
# ══════════════════════════════════════════════════════════════════
CONFIG = {
    "nombre":    "El Buen Sabor",
    "ruc":       "20512345678",
    "direccion": "Av. España 123, Trujillo, La Libertad",
    "telefono":  "+51 044 123456",
    "moneda":    "S/",
    "igv":       0.18,
    "mesas":     16,
    # Pagos digitales
    "yape":      "944 123 456",
    "plin":      "944 123 456",
    "nequi":     "311 123 4567",
    "daviplata": "311 123 4567",
    "whatsapp":  "51944123456",
}

MENU_DATA = {
    "🥗 Entradas": [
        {"nombre": "Ceviche Clásico",       "precio": 22.0, "desc": "Pescado, limón, cebolla, ají limo",       "emoji": "🐟"},
        {"nombre": "Causa Limeña",           "precio": 16.0, "desc": "Papa amarilla, pollo, palta",             "emoji": "🥔"},
        {"nombre": "Tequeños de Queso",      "precio": 14.0, "desc": "Masa wantán, queso gouda, ají rocoto",    "emoji": "🧀"},
        {"nombre": "Croquetas de Mariscos",  "precio": 18.0, "desc": "Camarones, conchas, crema bechamel",      "emoji": "🦐"},
        {"nombre": "Ensalada César",         "precio": 15.0, "desc": "Lechuga romana, pollo, aderezo césar",    "emoji": "🥬"},
        {"nombre": "Anticuchos",             "precio": 16.0, "desc": "Corazón de res a la parrilla, papas",     "emoji": "🍢"},
    ],
    "🍽️ Fondos": [
        {"nombre": "Lomo Saltado",           "precio": 32.0, "desc": "Res, tomate, cebolla, papas fritas",      "emoji": "🥩"},
        {"nombre": "Ají de Gallina",         "precio": 26.0, "desc": "Pollo en crema ají amarillo, arroz",      "emoji": "🍗"},
        {"nombre": "Seco de Res",            "precio": 28.0, "desc": "Res guisada en cilantro, frijoles",       "emoji": "🫘"},
        {"nombre": "Arroz con Mariscos",     "precio": 34.0, "desc": "Arroz, conchas, camarones, langostinos",  "emoji": "🦞"},
        {"nombre": "Chaufa Especial",        "precio": 24.0, "desc": "Arroz frito, pollo, huevo, verduras",     "emoji": "🍳"},
        {"nombre": "Filete de Merluza",      "precio": 29.0, "desc": "Al limón con papas y ensalada",           "emoji": "🐠"},
        {"nombre": "Costillas BBQ",          "precio": 38.0, "desc": "Costillas de cerdo, salsa BBQ, puré",     "emoji": "🍖"},
        {"nombre": "Pollo a la Brasa",       "precio": 45.0, "desc": "Entero, papas fritas, ensalada, cremas",  "emoji": "🍗"},
    ],
    "🍕 Ejecutivo": [
        {"nombre": "Menú Ejecutivo A",       "precio": 18.0, "desc": "Sopa + Segundo + Refresco",               "emoji": "🍱"},
        {"nombre": "Menú Ejecutivo B",       "precio": 22.0, "desc": "Entrada + Segundo + Postre + Refresco",   "emoji": "🥡"},
        {"nombre": "Combo Familiar",         "precio": 75.0, "desc": "2 fondos + 2 entradas + 4 bebidas",       "emoji": "👨‍👩‍👧‍👦"},
    ],
    "🍰 Postres": [
        {"nombre": "Suspiro Limeño",         "precio": 10.0, "desc": "Manjar, merengue de oporto",              "emoji": "🍮"},
        {"nombre": "Picarones",              "precio": 9.0,  "desc": "Masa de camote y zapallo, miel chancaca",  "emoji": "🍩"},
        {"nombre": "Crème Brûlée",           "precio": 12.0, "desc": "Vainilla, azúcar caramelizado",            "emoji": "🍮"},
        {"nombre": "Torta de Chocolate",     "precio": 11.0, "desc": "3 capas, ganache, frutos del bosque",      "emoji": "🎂"},
    ],
    "🥤 Bebidas": [
        {"nombre": "Chicha Morada",          "precio": 7.0,  "desc": "Natural, receta tradicional",             "emoji": "🍇"},
        {"nombre": "Limonada Frozen",        "precio": 8.0,  "desc": "Limón, hielo, jarabe de goma",            "emoji": "🍋"},
        {"nombre": "Jugo de Maracuyá",       "precio": 7.0,  "desc": "Natural, azúcar, hielo",                  "emoji": "🥭"},
        {"nombre": "Inca Kola",              "precio": 5.0,  "desc": "Botella 600 ml",                          "emoji": "🥤"},
        {"nombre": "Agua Mineral",           "precio": 4.0,  "desc": "Botella 625 ml",                          "emoji": "💧"},
        {"nombre": "Cerveza Pilsen",         "precio": 9.0,  "desc": "Botella 620 ml fría",                     "emoji": "🍺"},
        {"nombre": "Vino de la Casa",        "precio": 18.0, "desc": "Copa 150 ml, tinto o blanco",             "emoji": "🍷"},
        {"nombre": "Pisco Sour",             "precio": 14.0, "desc": "Pisco quebranta, limón, clara huevo",     "emoji": "🍸"},
    ],
}

# Colores por categoría
CAT_COLORS = {
    "🥗 Entradas":   C["accent3"],
    "🍽️ Fondos":     C["accent"],
    "🍕 Ejecutivo":  C["accent2"],
    "🍰 Postres":    C["purple"],
    "🥤 Bebidas":    C["blue"],
}

# ══════════════════════════════════════════════════════════════════
#  ESTADO GLOBAL
# ══════════════════════════════════════════════════════════════════
class AppState:
    def __init__(self):
        self.mesas = {}
        for i in range(1, CONFIG["mesas"] + 1):
            self.mesas[i] = {
                "estado":    "libre",   # libre | ocupada | cuenta
                "pedido":    [],        # [{nombre, precio, cant, nota}]
                "inicio":    None,
                "personas":  0,
                "mozo":      "—",
            }
        self.historial = []   # órdenes cerradas
        self.mesa_activa = None
        self.vista_actual = "dashboard"
        self.menu_data = {k: list(v) for k, v in MENU_DATA.items()}

STATE = AppState()

# ══════════════════════════════════════════════════════════════════
#  HELPERS DE UI
# ══════════════════════════════════════════════════════════════════
def _style_btn(btn, bg=C["accent"], fg=C["white"], hover=None):
    hover_c = hover or _darken(bg)
    btn.config(bg=bg, fg=fg, activebackground=hover_c, activeforeground=fg,
               relief="flat", cursor="hand2")
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_c))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))

def _darken(hex_color, factor=0.8):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return "#{:02x}{:02x}{:02x}".format(int(r*factor), int(g*factor), int(b*factor))

def _lighten(hex_color, factor=1.2):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return "#{:02x}{:02x}{:02x}".format(min(255,int(r*factor)), min(255,int(g*factor)), min(255,int(b*factor)))

def _fmt(amount):
    return f"{CONFIG['moneda']} {amount:,.2f}"

def _now_str():
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

def _time_elapsed(start):
    if not start:
        return "—"
    diff = (datetime.datetime.now() - start).total_seconds()
    m = int(diff // 60)
    s = int(diff % 60)
    return f"{m:02d}:{s:02d}"

def _scrollable(parent, **kwargs):
    """Returns (outer_frame, canvas, inner_frame)"""
    outer = tk.Frame(parent, bg=kwargs.get("bg", C["bg"]))
    canvas = tk.Canvas(outer, bg=kwargs.get("bg", C["bg"]), highlightthickness=0,
                       bd=0)
    vsb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(canvas, bg=kwargs.get("bg", C["bg"]))
    win_id = canvas.create_window((0,0), window=inner, anchor="nw")
    def _resize(e):
        canvas.itemconfig(win_id, width=canvas.winfo_width())
    canvas.bind("<Configure>", _resize)
    inner.bind("<Configure>", lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")))
    def _scroll(e):
        canvas.yview_scroll(int(-1*(e.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _scroll)
    return outer, canvas, inner

def _card(parent, **kwargs):
    return tk.Frame(parent, bg=kwargs.get("bg", C["card"]),
                    highlightbackground=kwargs.get("border", C["border"]),
                    highlightthickness=1)

def _label(parent, text, font=None, fg=None, bg=None, **kwargs):
    return tk.Label(parent, text=text,
                    font=font or FONTS["body"],
                    fg=fg or C["text"],
                    bg=bg or C["bg"],
                    **kwargs)

# ══════════════════════════════════════════════════════════════════
#  APLICACIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════════
class RestauranteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"🍽️  {CONFIG['nombre']}  |  ERP Sistema de Gestión")
        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.configure(bg=C["bg"])
        self._setup_style()
        self._build_layout()
        self._nav("dashboard")
        # Reloj y actualización periódica
        self._tick()

    # ── Estilo ttk ───────────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=C["bg"], foreground=C["text"],
                    fieldbackground=C["surface2"], font=FONTS["body"])
        s.configure("TCombobox", fieldbackground=C["surface2"],
                    background=C["surface2"], foreground=C["text"],
                    arrowcolor=C["accent"])
        s.map("TCombobox", fieldbackground=[("readonly", C["surface2"])])
        s.configure("TScrollbar", background=C["surface3"],
                    troughcolor=C["surface"], arrowcolor=C["text3"])
        s.configure("Treeview", background=C["surface"],
                    foreground=C["text"], fieldbackground=C["surface"],
                    rowheight=30)
        s.configure("Treeview.Heading", background=C["surface3"],
                    foreground=C["accent"], font=FONTS["h2"])
        s.map("Treeview", background=[("selected", C["accent"])])
        s.configure("TEntry", fieldbackground=C["surface2"],
                    foreground=C["text"])

    # ── Layout raíz ──────────────────────────────────────────────
    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        # Área de contenido
        self.content = tk.Frame(self, bg=C["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.current_frame = None

    # ── Sidebar ──────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = tk.Frame(self, bg=C["sidebar"], width=200)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        # Logo
        logo_f = tk.Frame(sb, bg=C["sidebar"])
        logo_f.pack(fill="x", padx=16, pady=(24,16))
        tk.Label(logo_f, text="🍽️", font=("Segoe UI", 28),
                 bg=C["sidebar"], fg=C["accent"]).pack()
        tk.Label(logo_f, text=CONFIG["nombre"], font=("Segoe UI", 11, "bold"),
                 bg=C["sidebar"], fg=C["text"], wraplength=160).pack()
        tk.Label(logo_f, text="Sistema ERP", font=FONTS["small"],
                 bg=C["sidebar"], fg=C["text3"]).pack()

        tk.Frame(sb, bg=C["border"], height=1).pack(fill="x", padx=16, pady=8)

        # Navegación
        self.nav_btns = {}
        nav_items = [
            ("dashboard",   "📊", "Dashboard"),
            ("mesas",       "🪑", "Mesas"),
            ("cocina",      "👨‍🍳", "Cocina"),
            ("reportes",    "📈", "Reportes"),
            ("admin",       "⚙️",  "Administrar"),
        ]
        for key, icon, label in nav_items:
            btn = tk.Button(sb, text=f"  {icon}  {label}",
                            font=FONTS["nav"], fg=C["text2"],
                            bg=C["sidebar"], anchor="w",
                            relief="flat", bd=0, padx=16, pady=10,
                            cursor="hand2",
                            command=lambda k=key: self._nav(k))
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=C["hover"]))
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.config(
                bg=C["accent"] if STATE.vista_actual==k else C["sidebar"]))
            self.nav_btns[key] = btn

        # Bottom info
        info = tk.Frame(sb, bg=C["sidebar"])
        info.pack(side="bottom", fill="x", padx=12, pady=16)
        self.lbl_clock = tk.Label(info, text="", font=FONTS["small"],
                                  bg=C["sidebar"], fg=C["text3"])
        self.lbl_clock.pack()
        tk.Label(info, text=f"v2.0  |  {CONFIG['ruc']}", font=FONTS["small"],
                 bg=C["sidebar"], fg=C["text3"]).pack()

    def _tick(self):
        self.lbl_clock.config(text=datetime.datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
        # Solo refrescar cocina automáticamente; dashboard se actualiza al navegar
        if STATE.vista_actual == "cocina":
            self._refresh_view()
        self.after(1000, self._tick)

    def _nav(self, key):
        # Resaltar botón activo
        for k, b in self.nav_btns.items():
            b.config(bg=C["accent"] if k==key else C["sidebar"],
                     fg=C["white"] if k==key else C["text2"])
        STATE.vista_actual = key
        self._show_view(key)

    def _show_view(self, key):
        if self.current_frame:
            self.current_frame.destroy()
        builders = {
            "dashboard": self._view_dashboard,
            "mesas":     self._view_mesas,
            "cocina":    self._view_cocina,
            "reportes":  self._view_reportes,
            "admin":     self._view_admin,
        }
        frame = builders[key]()
        frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = frame

    def _refresh_view(self):
        if self.current_frame and STATE.vista_actual in ("cocina","dashboard"):
            self._show_view(STATE.vista_actual)

    # ══════════════════════════════════════════════════════════════
    #  VISTA: DASHBOARD
    # ══════════════════════════════════════════════════════════════
    def _view_dashboard(self):
        root = tk.Frame(self.content, bg=C["bg"])
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        # Header
        hdr = tk.Frame(root, bg=C["bg"])
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20,12))
        _label(hdr, f"Dashboard — {CONFIG['nombre']}", FONTS["title"],
               fg=C["text"]).pack(side="left")
        _label(hdr, _now_str(), FONTS["body"], fg=C["text3"]).pack(side="right",pady=6)

        outer, _, inner = _scrollable(root, bg=C["bg"])
        outer.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)

        # KPIs
        kpis_f = tk.Frame(inner, bg=C["bg"])
        kpis_f.pack(fill="x", padx=12, pady=8)
        kpis_f.grid_columnconfigure((0,1,2,3), weight=1)

        ocupadas = sum(1 for m in STATE.mesas.values() if m["estado"] != "libre")
        total_dia = sum(h["total"] for h in STATE.historial
                        if h["fecha"].startswith(datetime.date.today().strftime("%d/%m")))
        ventas_dia = sum(1 for h in STATE.historial
                         if h["fecha"].startswith(datetime.date.today().strftime("%d/%m")))
        pendientes = sum(1 for m in STATE.mesas.values()
                         if len(m["pedido"]) > 0 and m["estado"] != "libre")

        kpi_data = [
            ("Mesas Ocupadas",   f"{ocupadas}/{CONFIG['mesas']}", C["accent"],   "🪑"),
            ("Ventas Hoy",       _fmt(total_dia),                  C["accent3"],  "💰"),
            ("Pedidos Hoy",      str(ventas_dia),                  C["blue"],     "📋"),
            ("En Cocina",        str(pendientes),                  C["accent2"],  "👨‍🍳"),
        ]
        for col, (title, val, color, icon) in enumerate(kpi_data):
            c = _card(kpis_f, bg=C["card"])
            c.grid(row=0, column=col, padx=6, pady=4, sticky="ew")
            tk.Label(c, text=icon, font=("Segoe UI",22), bg=C["card"],
                     fg=color).pack(pady=(12,2))
            tk.Label(c, text=val, font=FONTS["kpi"], bg=C["card"],
                     fg=color).pack()
            tk.Label(c, text=title, font=FONTS["small"], bg=C["card"],
                     fg=C["text3"]).pack(pady=(0,12))

        # Mesas rápidas
        mesas_f = _card(inner, bg=C["card"])
        mesas_f.pack(fill="x", padx=12, pady=8)
        tk.Label(mesas_f, text="Estado de Mesas", font=FONTS["h2"],
                 bg=C["card"], fg=C["text"]).pack(anchor="w", padx=16, pady=(12,8))
        grid_m = tk.Frame(mesas_f, bg=C["card"])
        grid_m.pack(fill="x", padx=12, pady=(0,12))
        cols = 8
        for i, (num, mesa) in enumerate(STATE.mesas.items()):
            color = {"libre": C["accent3"], "ocupada": C["accent"], "cuenta": C["accent2"]}[mesa["estado"]]
            btn = tk.Button(grid_m, text=f"M{num}", font=FONTS["small"],
                            bg=color, fg=C["white"], relief="flat",
                            width=4, height=2, cursor="hand2",
                            command=lambda n=num: [self._nav("mesas"), self._abrir_mesa(n)])
            btn.grid(row=i//cols, column=i%cols, padx=3, pady=3)

        # Leyenda
        leg = tk.Frame(mesas_f, bg=C["card"])
        leg.pack(pady=(0,8))
        for txt, col in [("Libre", C["accent3"]),("Ocupada", C["accent"]),("Cuenta",C["accent2"])]:
            tk.Frame(leg, bg=col, width=12, height=12).pack(side="left", padx=(12,3))
            tk.Label(leg, text=txt, font=FONTS["small"], bg=C["card"], fg=C["text2"]).pack(side="left", padx=(0,8))

        # Últimas ventas
        if STATE.historial:
            hist_f = _card(inner, bg=C["card"])
            hist_f.pack(fill="x", padx=12, pady=8)
            tk.Label(hist_f, text="Últimas Ventas", font=FONTS["h2"],
                     bg=C["card"], fg=C["text"]).pack(anchor="w", padx=16, pady=(12,4))
            cols_t = ("Mesa","Hora","Items","Total","Pago")
            tree = ttk.Treeview(hist_f, columns=cols_t, show="headings", height=6)
            for c in cols_t:
                tree.heading(c, text=c)
                tree.column(c, width=120, anchor="center")
            for h in reversed(STATE.historial[-10:]):
                tree.insert("", "end", values=(
                    f"Mesa {h['mesa']}", h['fecha'],
                    str(h['items']), _fmt(h['total']), h['metodo_pago']))
            tree.pack(fill="x", padx=12, pady=(0,12))

        # Gráfico de ventas del día (si matplotlib disponible)
        if MPL_OK and STATE.historial:
            self._dash_chart(inner)

        return root

    def _dash_chart(self, parent):
        conteo = defaultdict(float)
        hoy = datetime.date.today().strftime("%d/%m")
        for h in STATE.historial:
            if h["fecha"].startswith(hoy):
                for it in h.get("detalle", []):
                    conteo[it["nombre"]] += it["precio"] * it["cant"]
        if not conteo:
            return
        chart_f = _card(parent, bg=C["card"])
        chart_f.pack(fill="x", padx=12, pady=8)
        tk.Label(chart_f, text="Top Ventas del Día", font=FONTS["h2"],
                 bg=C["card"], fg=C["text"]).pack(anchor="w", padx=16, pady=(12,4))
        items = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:8]
        labels = [x[0][:15] for x in items]
        values = [x[1] for x in items]
        fig, ax = plt.subplots(figsize=(8, 2.5), facecolor=C["card"])
        bars = ax.barh(labels, values, color=C["accent"], edgecolor="none")
        ax.set_facecolor(C["card"])
        ax.tick_params(colors=C["text2"], labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(C["border"])
        ax.xaxis.label.set_color(C["text2"])
        for bar, val in zip(bars, values):
            ax.text(bar.get_width()+0.5, bar.get_y()+bar.get_height()/2,
                    _fmt(val), va="center", ha="left", fontsize=8, color=C["text2"])
        plt.tight_layout(pad=0.5)
        canvas = FigureCanvasTkAgg(fig, master=chart_f)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=12, pady=(0,12))
        plt.close(fig)

    # ══════════════════════════════════════════════════════════════
    #  VISTA: MESAS
    # ══════════════════════════════════════════════════════════════
    def _view_mesas(self):
        root = tk.Frame(self.content, bg=C["bg"])
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        hdr = tk.Frame(root, bg=C["bg"])
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20,8))
        _label(hdr, "🪑  Gestión de Mesas", FONTS["title"], fg=C["text"]).pack(side="left")

        # Resumen
        for estado, col, lbl in [("libre",C["accent3"],"Libres"),
                                   ("ocupada",C["accent"],"Ocupadas"),
                                   ("cuenta",C["accent2"],"Con Cuenta")]:
            n = sum(1 for m in STATE.mesas.values() if m["estado"]==estado)
            pill = tk.Frame(hdr, bg=col)
            pill.pack(side="right", padx=4)
            tk.Label(pill, text=f"  {lbl}: {n}  ", font=FONTS["small"],
                     bg=col, fg=C["white"]).pack(padx=4, pady=2)

        outer, _, inner = _scrollable(root, bg=C["bg"])
        outer.grid(row=1, column=0, sticky="nsew")

        grid_f = tk.Frame(inner, bg=C["bg"])
        grid_f.pack(fill="both", expand=True, padx=16, pady=8)
        cols = 4
        for i, (num, mesa) in enumerate(STATE.mesas.items()):
            self._mesa_card(grid_f, num, mesa, i, cols)

        return root

    def _mesa_card(self, parent, num, mesa, idx, cols):
        color = {"libre":C["accent3"],"ocupada":C["accent"],"cuenta":C["accent2"]}[mesa["estado"]]
        c = tk.Frame(parent, bg=C["card"],
                     highlightbackground=color, highlightthickness=2,
                     cursor="hand2")
        c.grid(row=idx//cols, column=idx%cols, padx=8, pady=8, sticky="ew")
        parent.grid_columnconfigure(idx%cols, weight=1)

        tk.Label(c, text=f"Mesa {num}", font=FONTS["h2"],
                 bg=C["card"], fg=color).pack(pady=(12,2))

        estado_txt = {"libre":"● Libre","ocupada":"● Ocupada","cuenta":"● Cuenta"}[mesa["estado"]]
        tk.Label(c, text=estado_txt, font=FONTS["small"],
                 bg=C["card"], fg=color).pack()

        if mesa["estado"] != "libre":
            total = sum(it["precio"]*it["cant"] for it in mesa["pedido"])
            tk.Label(c, text=_fmt(total), font=FONTS["price"],
                     bg=C["card"], fg=C["text"]).pack(pady=2)
            tk.Label(c, text=f"⏱ {_time_elapsed(mesa['inicio'])}",
                     font=FONTS["small"], bg=C["card"], fg=C["text3"]).pack()
            tk.Label(c, text=f"{len(mesa['pedido'])} item(s)",
                     font=FONTS["small"], bg=C["card"], fg=C["text2"]).pack()
        else:
            tk.Label(c, text="Disponible", font=FONTS["small"],
                     bg=C["card"], fg=C["text3"]).pack(pady=8)

        btn_txt = "Ver Pedido" if mesa["estado"]!="libre" else "Abrir Mesa"
        btn = tk.Button(c, text=btn_txt, font=FONTS["small"],
                        relief="flat", padx=12, pady=6, cursor="hand2",
                        command=lambda n=num: self._abrir_mesa(n))
        _style_btn(btn, bg=color)
        btn.pack(pady=(8,12))

        # Hover
        for w in [c] + c.winfo_children():
            w.bind("<Button-1>", lambda e, n=num: self._abrir_mesa(n))

    def _abrir_mesa(self, num):
        """Abre la ventana de pedido para la mesa num"""
        win = tk.Toplevel(self)
        win.title(f"Mesa {num} — Pedido")
        win.geometry("1100x720")
        win.configure(bg=C["bg"])
        win.grab_set()

        mesa = STATE.mesas[num]
        if mesa["estado"] == "libre":
            mesa["estado"] = "ocupada"
            mesa["inicio"] = datetime.datetime.now()

        win.grid_columnconfigure(0, weight=1)
        win.grid_columnconfigure(1, weight=0)
        win.grid_rowconfigure(0, weight=1)

        # Panel izquierdo — carta
        left = tk.Frame(win, bg=C["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(12,4), pady=12)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # Tabs de categoría
        cats = list(STATE.menu_data.keys())
        self._cat_sel = tk.StringVar(value=cats[0])
        tab_f = tk.Frame(left, bg=C["bg"])
        tab_f.grid(row=0, column=0, sticky="ew", pady=(0,8))
        self._cat_tabs = {}
        for cat in cats:
            color = CAT_COLORS.get(cat, C["accent"])
            b = tk.Button(tab_f, text=cat, font=FONTS["small"],
                          relief="flat", padx=8, pady=6, cursor="hand2",
                          command=lambda c=cat: self._switch_cat(c, menu_area, num, win))
            _style_btn(b, bg=C["surface3"] if cat!=cats[0] else color)
            b.pack(side="left", padx=2)
            self._cat_tabs[cat] = b

        # Área de menú scrollable
        menu_outer, _, menu_area = _scrollable(left, bg=C["bg"])
        menu_outer.grid(row=1, column=0, sticky="nsew")
        self._fill_menu(menu_area, cats[0], num, win)

        # Panel derecho — carrito
        right = tk.Frame(win, bg=C["surface"], width=320)
        right.grid(row=0, column=1, sticky="nsew", padx=(4,12), pady=12)
        right.grid_propagate(False)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_cart(right, num, win)

    def _switch_cat(self, cat, menu_area, num=1, win=None):
        self._cat_sel.set(cat)
        for w in menu_area.winfo_children():
            w.destroy()
        self._fill_menu(menu_area, cat, num, win)
        color = CAT_COLORS.get(cat, C["accent"])
        for c, b in self._cat_tabs.items():
            _style_btn(b, bg=color if c==cat else C["surface3"])

    def _fill_menu(self, area, cat, num, win):
        items = STATE.menu_data.get(cat, [])
        color = CAT_COLORS.get(cat, C["accent"])
        cols = 3
        for i, item in enumerate(items):
            self._item_card(area, item, num, color, i, cols, win)
        area.update_idletasks()

    def _item_card(self, parent, item, num, color, idx, cols, win):
        c = _card(parent, bg=C["card"], border=C["border"])
        c.grid(row=idx//cols, column=idx%cols, padx=6, pady=6, sticky="ew")
        parent.grid_columnconfigure(idx%cols, weight=1)

        # Emoji grande
        tk.Label(c, text=item.get("emoji","🍽️"), font=("Segoe UI",30),
                 bg=C["card"]).pack(pady=(12,2))
        tk.Label(c, text=item["nombre"], font=FONTS["h2"],
                 bg=C["card"], fg=C["text"], wraplength=150).pack(padx=8)
        tk.Label(c, text=item.get("desc",""), font=FONTS["small"],
                 bg=C["card"], fg=C["text3"], wraplength=150).pack(padx=8, pady=2)
        tk.Label(c, text=_fmt(item["precio"]), font=FONTS["price"],
                 bg=C["card"], fg=color).pack(pady=4)

        # Nota
        nota_var = tk.StringVar()
        nota_e = tk.Entry(c, textvariable=nota_var, font=FONTS["small"],
                          bg=C["surface2"], fg=C["text3"], relief="flat",
                          insertbackground=C["text"])
        nota_e.insert(0, "Nota...")
        nota_e.bind("<FocusIn>", lambda e, w=nota_e: w.delete(0,"end") if nota_e.get()=="Nota..." else None)
        nota_e.pack(fill="x", padx=8, pady=2)

        # Cantidad
        qty_var = tk.IntVar(value=1)
        qty_f = tk.Frame(c, bg=C["card"])
        qty_f.pack(pady=4)
        tk.Button(qty_f, text="−", font=FONTS["h2"], bg=C["surface3"],
                  fg=C["text"], relief="flat", width=2, cursor="hand2",
                  command=lambda: qty_var.set(max(1, qty_var.get()-1))).pack(side="left")
        tk.Label(qty_f, textvariable=qty_var, font=FONTS["body"],
                 bg=C["card"], fg=C["text"], width=3).pack(side="left")
        tk.Button(qty_f, text="+", font=FONTS["h2"], bg=C["surface3"],
                  fg=C["text"], relief="flat", width=2, cursor="hand2",
                  command=lambda: qty_var.set(qty_var.get()+1)).pack(side="left")

        def agregar():
            nota = nota_var.get() if nota_var.get() != "Nota..." else ""
            STATE.mesas[num]["pedido"].append({
                "nombre": item["nombre"],
                "precio": item["precio"],
                "cant":   qty_var.get(),
                "nota":   nota,
            })
            qty_var.set(1)
            if win:
                for w in win.winfo_children():
                    if isinstance(w, tk.Frame) and w.grid_info().get("column")==1:
                        for child in w.winfo_children(): child.destroy()
                        self._build_cart(w, num, win)
                        break

        btn = tk.Button(c, text="+ Agregar", font=FONTS["small"],
                        relief="flat", padx=8, pady=6, cursor="hand2",
                        command=agregar)
        _style_btn(btn, bg=color)
        btn.pack(pady=(4,12))

    def _build_cart(self, parent, num, win):
        mesa = STATE.mesas[num]
        tk.Label(parent, text=f"🛒  Mesa {num}", font=FONTS["h2"],
                 bg=C["surface"], fg=C["text"]).grid(row=0, column=0,
                 sticky="ew", padx=12, pady=(12,4))

        outer, _, inner = _scrollable(parent, bg=C["surface"])
        outer.grid(row=1, column=0, sticky="nsew", padx=4)

        if not mesa["pedido"]:
            tk.Label(inner, text="Carrito vacío\nAgrega platos desde la carta",
                     font=FONTS["small"], bg=C["surface"], fg=C["text3"],
                     justify="center").pack(pady=40)
        else:
            for i, item in enumerate(mesa["pedido"]):
                row = tk.Frame(inner, bg=C["surface"])
                row.pack(fill="x", padx=8, pady=2)
                tk.Label(row, text=item["emoji"] if "emoji" in item else "•",
                         font=("Segoe UI",14), bg=C["surface"],
                         fg=C["accent"]).pack(side="left", padx=(0,4))
                info = tk.Frame(row, bg=C["surface"])
                info.pack(side="left", fill="x", expand=True)
                tk.Label(info, text=item["nombre"], font=FONTS["small"],
                         bg=C["surface"], fg=C["text"], anchor="w").pack(fill="x")
                tk.Label(info, text=f"{item['cant']} × {_fmt(item['precio'])}",
                         font=FONTS["small"], bg=C["surface"],
                         fg=C["text3"], anchor="w").pack(fill="x")
                if item.get("nota"):
                    tk.Label(info, text=f"📝 {item['nota']}", font=FONTS["small"],
                             bg=C["surface"], fg=C["text3"], anchor="w").pack(fill="x")
                tk.Label(row, text=_fmt(item["precio"]*item["cant"]),
                         font=FONTS["small"], bg=C["surface"],
                         fg=C["accent3"]).pack(side="right", padx=4)
                tk.Button(row, text="✕", font=FONTS["small"],
                          bg=C["surface"], fg=C["red"], relief="flat",
                          cursor="hand2",
                          command=lambda idx=i: self._del_item(num, idx, parent, win)
                          ).pack(side="right")

        # Totales
        bottom = tk.Frame(parent, bg=C["surface"])
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=8)

        sub = sum(it["precio"]*it["cant"] for it in mesa["pedido"])
        igv = sub * CONFIG["igv"]
        total = sub + igv

        for lbl, val in [("Subtotal", sub), (f"IGV ({int(CONFIG['igv']*100)}%)", igv), ("TOTAL", total)]:
            row = tk.Frame(bottom, bg=C["surface"])
            row.pack(fill="x", pady=1)
            bold = "bold" if lbl=="TOTAL" else "normal"
            col = C["accent"] if lbl=="TOTAL" else C["text2"]
            tk.Label(row, text=lbl, font=("Segoe UI",10,bold),
                     bg=C["surface"], fg=col).pack(side="left")
            tk.Label(row, text=_fmt(val), font=("Segoe UI",10,bold),
                     bg=C["surface"], fg=col).pack(side="right")

        tk.Frame(bottom, bg=C["border"], height=1).pack(fill="x", pady=4)

        # Botón cobrar
        if mesa["pedido"]:
            btn_cobrar = tk.Button(bottom, text="💳  Cobrar",
                                   font=FONTS["h2"], relief="flat",
                                   padx=12, pady=10, cursor="hand2",
                                   command=lambda: self._ventana_pago(num, win))
            _style_btn(btn_cobrar, bg=C["accent3"])
            btn_cobrar.pack(fill="x", pady=4)

        btn_cancel = tk.Button(bottom, text="🗑  Cancelar Mesa",
                               font=FONTS["small"], relief="flat",
                               padx=8, pady=6, cursor="hand2",
                               command=lambda: self._cancelar_mesa(num, win))
        _style_btn(btn_cancel, bg=C["red"])
        btn_cancel.pack(fill="x", pady=2)

    def _del_item(self, num, idx, cart_frame, win):
        if 0 <= idx < len(STATE.mesas[num]["pedido"]):
            STATE.mesas[num]["pedido"].pop(idx)
        for w in cart_frame.winfo_children(): w.destroy()
        self._build_cart(cart_frame, num, win)

    def _cancelar_mesa(self, num, win):
        if messagebox.askyesno("Cancelar", f"¿Cancelar mesa {num} y borrar pedido?"):
            STATE.mesas[num] = {"estado":"libre","pedido":[],"inicio":None,
                                "personas":0,"mozo":"—"}
            win.destroy()
            self._nav("mesas")

    # ══════════════════════════════════════════════════════════════
    #  VENTANA DE PAGO
    # ══════════════════════════════════════════════════════════════
    def _ventana_pago(self, num, parent_win):
        mesa = STATE.mesas[num]
        sub   = sum(it["precio"]*it["cant"] for it in mesa["pedido"])
        igv   = sub * CONFIG["igv"]
        total = sub + igv

        win = tk.Toplevel(self)
        win.title(f"Cobrar Mesa {num}")
        win.geometry("520x700")
        win.configure(bg=C["bg"])
        win.grab_set()

        tk.Label(win, text=f"💳  Cobrar Mesa {num}", font=FONTS["title"],
                 bg=C["bg"], fg=C["text"]).pack(pady=(20,4))
        tk.Label(win, text=f"Total a cobrar: {_fmt(total)}", font=FONTS["kpi"],
                 bg=C["bg"], fg=C["accent3"]).pack()

        # Resumen rápido
        res_f = _card(win, bg=C["card"])
        res_f.pack(fill="x", padx=20, pady=8)
        for it in mesa["pedido"]:
            row = tk.Frame(res_f, bg=C["card"])
            row.pack(fill="x", padx=12, pady=1)
            tk.Label(row, text=f"{it['cant']}× {it['nombre']}", font=FONTS["small"],
                     bg=C["card"], fg=C["text2"]).pack(side="left")
            tk.Label(row, text=_fmt(it["precio"]*it["cant"]), font=FONTS["small"],
                     bg=C["card"], fg=C["text3"]).pack(side="right")

        # Datos cliente
        client_f = _card(win, bg=C["card"])
        client_f.pack(fill="x", padx=20, pady=4)
        tk.Label(client_f, text="Datos del Cliente (opcional)", font=FONTS["h2"],
                 bg=C["card"], fg=C["text"]).pack(anchor="w", padx=12, pady=(8,4))
        for lbl, attr in [("Nombre:", "cli_nombre"), ("Teléfono (WhatsApp):", "cli_tel")]:
            row = tk.Frame(client_f, bg=C["card"])
            row.pack(fill="x", padx=12, pady=2)
            tk.Label(row, text=lbl, font=FONTS["small"], bg=C["card"],
                     fg=C["text2"], width=22, anchor="w").pack(side="left")
            var = tk.StringVar()
            setattr(self, attr, var)
            tk.Entry(row, textvariable=var, font=FONTS["small"],
                     bg=C["surface2"], fg=C["text"], relief="flat",
                     insertbackground=C["text"]).pack(side="left", fill="x", expand=True, padx=(4,12))

        # Método de pago
        pay_f = _card(win, bg=C["card"])
        pay_f.pack(fill="x", padx=20, pady=4)
        tk.Label(pay_f, text="Método de Pago", font=FONTS["h2"],
                 bg=C["card"], fg=C["text"]).pack(anchor="w", padx=12, pady=(8,4))

        pay_var = tk.StringVar(value="Efectivo")
        methods = [
            ("💵 Efectivo",   "Efectivo",   C["accent3"]),
            ("💳 Tarjeta",    "Tarjeta",    C["blue"]),
            ("🟣 Yape",       "Yape",       C["purple"]),
            ("🔵 Plin",       "Plin",       C["blue"]),
            ("🟡 Nequi",      "Nequi",      C["accent2"]),
            ("🟠 Daviplata",  "Daviplata",  C["accent"]),
        ]
        grid_p = tk.Frame(pay_f, bg=C["card"])
        grid_p.pack(fill="x", padx=12, pady=(0,8))
        self._pay_btns = {}
        for idx, (txt, val, col) in enumerate(methods):
            btn = tk.Button(grid_p, text=txt, font=FONTS["small"],
                            relief="flat", padx=6, pady=8, cursor="hand2",
                            command=lambda v=val: self._sel_pay(v, pay_var))
            _style_btn(btn, bg=col if val=="Efectivo" else C["surface3"],
                       fg=C["white"])
            btn.grid(row=idx//3, column=idx%3, padx=4, pady=4, sticky="ew")
            grid_p.grid_columnconfigure(idx%3, weight=1)
            self._pay_btns[val] = (btn, col)

        # Info digital
        self.pay_info_lbl = tk.Label(pay_f, text=f"Yape/Plin: {CONFIG['yape']}",
                                     font=FONTS["small"], bg=C["card"], fg=C["text3"])
        self.pay_info_lbl.pack(pady=(0,8))

        pay_var.trace("w", lambda *a: self._update_pay_info(pay_var))

        # Efectivo recibido
        efe_f = tk.Frame(win, bg=C["bg"])
        efe_f.pack(fill="x", padx=20, pady=4)
        tk.Label(efe_f, text="Efectivo recibido:", font=FONTS["small"],
                 bg=C["bg"], fg=C["text2"]).pack(side="left")
        self.efe_var = tk.StringVar(value=str(math.ceil(total)))
        tk.Entry(efe_f, textvariable=self.efe_var, font=FONTS["body"],
                 bg=C["surface2"], fg=C["text"], relief="flat", width=12,
                 insertbackground=C["text"]).pack(side="left", padx=8)
        self.vuelto_lbl = tk.Label(efe_f, text="", font=FONTS["small"],
                                   bg=C["bg"], fg=C["accent3"])
        self.vuelto_lbl.pack(side="left")
        self.efe_var.trace("w", lambda *a: self._calc_vuelto(total))

        # Botón confirmar
        btn_ok = tk.Button(win, text="✅  Confirmar Pago y Generar Ticket",
                           font=FONTS["h2"], relief="flat", padx=16, pady=12,
                           cursor="hand2",
                           command=lambda: self._confirmar_pago(num, total, sub, igv,
                                                                pay_var.get(), win, parent_win))
        _style_btn(btn_ok, bg=C["accent3"])
        btn_ok.pack(fill="x", padx=20, pady=8)

    def _sel_pay(self, val, var):
        var.set(val)
        for v, (btn, col) in self._pay_btns.items():
            _style_btn(btn, bg=col if v==val else C["surface3"])

    def _update_pay_info(self, var):
        v = var.get()
        info = {
            "Yape":      f"Yape: {CONFIG['yape']}",
            "Plin":      f"Plin: {CONFIG['plin']}",
            "Nequi":     f"Nequi: {CONFIG['nequi']}",
            "Daviplata": f"Daviplata: {CONFIG['daviplata']}",
        }
        self.pay_info_lbl.config(text=info.get(v, ""))

    def _calc_vuelto(self, total):
        try:
            recibido = float(self.efe_var.get())
            vuelto = recibido - total
            self.vuelto_lbl.config(text=f"Vuelto: {_fmt(vuelto)}" if vuelto>=0 else "⚠ Insuficiente",
                                   fg=C["accent3"] if vuelto>=0 else C["red"])
        except:
            self.vuelto_lbl.config(text="")

    def _confirmar_pago(self, num, total, sub, igv, metodo, pago_win, mesa_win):
        mesa = STATE.mesas[num]
        nombre_cli = getattr(self, "cli_nombre", tk.StringVar()).get()
        tel_cli    = getattr(self, "cli_tel",    tk.StringVar()).get()

        # Registrar en historial
        registro = {
            "mesa":        num,
            "fecha":       _now_str(),
            "total":       total,
            "subtotal":    sub,
            "igv":         igv,
            "items":       len(mesa["pedido"]),
            "metodo_pago": metodo,
            "cliente":     nombre_cli,
            "telefono":    tel_cli,
            "detalle":     [dict(it) for it in mesa["pedido"]],
        }
        STATE.historial.append(registro)

        # Generar ticket
        ticket_txt = self._gen_ticket(registro)
        path = self._guardar_ticket(ticket_txt, num)
        self._imprimir_ticket(path, ticket_txt)

        # WhatsApp al cliente
        if tel_cli:
            self._enviar_whatsapp(tel_cli, registro, ticket_txt)

        # Limpiar mesa
        STATE.mesas[num] = {"estado":"libre","pedido":[],"inicio":None,
                            "personas":0,"mozo":"—"}
        pago_win.destroy()
        mesa_win.destroy()
        self._nav("mesas")
        messagebox.showinfo("✅ Pago registrado",
                            f"Mesa {num} cobrada exitosamente.\nTotal: {_fmt(total)}\nPago: {metodo}")

    # ══════════════════════════════════════════════════════════════
    #  TICKETS Y IMPRESIÓN
    # ══════════════════════════════════════════════════════════════
    def _gen_ticket(self, reg):
        sep = "─" * 38
        lines = [
            "=" * 38,
            CONFIG["nombre"].center(38),
            CONFIG["ruc"].center(38),
            CONFIG["direccion"][:38].center(38),
            CONFIG["telefono"].center(38),
            "=" * 38,
            f"  Mesa: {reg['mesa']}".ljust(20) + f"Fecha: {reg['fecha'][:10]}".rjust(18),
            f"  Hora: {reg['fecha'][11:]}".ljust(20) + f"Ticket #{len(STATE.historial):04d}".rjust(18),
            sep,
            f"  {'DESCRIPCIÓN':<22} {'CANT':>3} {'P.UNIT':>6} {'TOTAL':>6}",
            sep,
        ]
        for it in reg["detalle"]:
            nom = it["nombre"][:22]
            lines.append(f"  {nom:<22} {it['cant']:>3} {it['precio']:>6.2f} {it['precio']*it['cant']:>6.2f}")
            if it.get("nota"):
                lines.append(f"    > {it['nota']}")
        lines += [
            sep,
            f"  {'Subtotal':<28} {reg['subtotal']:>8.2f}",
            f"  {'IGV (18%)':<28} {reg['igv']:>8.2f}",
            "=" * 38,
            f"  {'TOTAL':<28} {reg['total']:>8.2f}",
            "=" * 38,
            f"  Forma de pago: {reg['metodo_pago']}",
        ]
        if reg.get("cliente"):
            lines.append(f"  Cliente: {reg['cliente']}")
        lines += [
            sep,
            "  ¡Gracias por su visita!".center(38),
            "  Vuelva pronto 🙏".center(38),
            "",
        ]
        return "\n".join(lines)

    def _guardar_ticket(self, text, num):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.path.expanduser("~"), f"ticket_mesa{num}_{ts}.txt")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass
        return path

    def _imprimir_ticket(self, path, text):
        """Intenta ESC/POS; si falla, abre notepad/gedit"""
        try:
            import usb.core  # type: ignore
            # ESC/POS básico
            ESC = b"\x1b"
            printer_data = (ESC + b"@" +      # init
                            text.encode("cp437", errors="replace") +
                            b"\n\n\n\n" +      # avance
                            ESC + b"d\x04")    # corte
            dev = usb.core.find(idVendor=0x04b8)  # Epson, ajustar
            if dev:
                dev.write(1, printer_data)
                return
        except Exception:
            pass
        # Fallback: abrir el archivo de texto
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _enviar_whatsapp(self, tel, reg, ticket_txt):
        tel_clean = "".join(c for c in tel if c.isdigit())
        if not tel_clean.startswith("51") and len(tel_clean)==9:
            tel_clean = "51" + tel_clean
        items_txt = "\n".join(
            f"  • {it['cant']}× {it['nombre']} — {_fmt(it['precio']*it['cant'])}"
            for it in reg["detalle"]
        )
        msg = (f"🍽️ *{CONFIG['nombre']}*\n"
               f"Mesa {reg['mesa']} | {reg['fecha']}\n\n"
               f"*Su pedido:*\n{items_txt}\n\n"
               f"*Total: {_fmt(reg['total'])}*\n"
               f"Pago: {reg['metodo_pago']}\n\n"
               f"¡Gracias por visitarnos! 🙏")
        url = f"https://wa.me/{tel_clean}?text={urllib.parse.quote(msg)}"
        webbrowser.open(url)

    # ══════════════════════════════════════════════════════════════
    #  VISTA: COCINA
    # ══════════════════════════════════════════════════════════════
    def _view_cocina(self):
        root = tk.Frame(self.content, bg=C["bg"])
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        hdr = tk.Frame(root, bg=C["bg"])
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20,8))
        _label(hdr, "👨‍🍳  Display de Cocina", FONTS["title"], fg=C["text"]).pack(side="left")
        _label(hdr, "Actualización automática cada segundo", FONTS["small"],
               fg=C["text3"]).pack(side="right", pady=6)

        outer, _, inner = _scrollable(root, bg=C["bg"])
        outer.grid(row=1, column=0, sticky="nsew")

        ocupadas = [(num, m) for num, m in STATE.mesas.items()
                    if m["estado"] != "libre" and m["pedido"]]

        if not ocupadas:
            tk.Label(inner, text="🍳  Sin pedidos pendientes",
                     font=FONTS["h1"], bg=C["bg"], fg=C["text3"]).pack(pady=60)
        else:
            cols = 3
            for i, (num, mesa) in enumerate(ocupadas):
                self._cocina_card(inner, num, mesa, i, cols)

        return root

    def _cocina_card(self, parent, num, mesa, idx, cols):
        elapsed = _time_elapsed(mesa["inicio"])
        mins = 0
        if mesa["inicio"]:
            mins = int((datetime.datetime.now()-mesa["inicio"]).total_seconds()/60)

        urgency_color = C["accent3"] if mins<15 else C["accent2"] if mins<30 else C["red"]

        c = tk.Frame(parent, bg=C["card"],
                     highlightbackground=urgency_color, highlightthickness=2)
        c.grid(row=idx//cols, column=idx%cols, padx=8, pady=8, sticky="nsew")
        parent.grid_columnconfigure(idx%cols, weight=1)

        # Header
        h = tk.Frame(c, bg=urgency_color)
        h.pack(fill="x")
        tk.Label(h, text=f"Mesa {num}", font=FONTS["h2"],
                 bg=urgency_color, fg=C["white"]).pack(side="left", padx=10, pady=6)
        tk.Label(h, text=f"⏱ {elapsed}", font=FONTS["body"],
                 bg=urgency_color, fg=C["white"]).pack(side="right", padx=10)

        for it in mesa["pedido"]:
            row = tk.Frame(c, bg=C["card"])
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=f"  {it['cant']}×", font=FONTS["h2"],
                     bg=C["card"], fg=urgency_color, width=4).pack(side="left")
            txt = tk.Frame(row, bg=C["card"])
            txt.pack(side="left", fill="x", expand=True)
            tk.Label(txt, text=it["nombre"], font=FONTS["body"],
                     bg=C["card"], fg=C["text"], anchor="w").pack(fill="x")
            if it.get("nota"):
                tk.Label(txt, text=f"📝 {it['nota']}", font=FONTS["small"],
                         bg=C["card"], fg=C["accent2"], anchor="w").pack(fill="x")

        # Botón listo
        btn = tk.Button(c, text="✅  Marcar Listo",
                        font=FONTS["small"], relief="flat", pady=6,
                        cursor="hand2",
                        command=lambda n=num: self._mesa_lista(n))
        _style_btn(btn, bg=C["accent3"])
        btn.pack(fill="x", padx=10, pady=(6,10))

    def _mesa_lista(self, num):
        STATE.mesas[num]["estado"] = "cuenta"
        self._nav("cocina")

    # ══════════════════════════════════════════════════════════════
    #  VISTA: REPORTES
    # ══════════════════════════════════════════════════════════════
    def _view_reportes(self):
        root = tk.Frame(self.content, bg=C["bg"])
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        hdr = tk.Frame(root, bg=C["bg"])
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20,8))
        _label(hdr, "📈  Reportes y Estadísticas", FONTS["title"], fg=C["text"]).pack(side="left")
        if EXCEL_OK:
            btn_exp = tk.Button(hdr, text="📥 Exportar Excel", font=FONTS["body"],
                                relief="flat", padx=10, pady=6, cursor="hand2",
                                command=self._exportar_excel)
            _style_btn(btn_exp, bg=C["accent3"])
            btn_exp.pack(side="right")

        outer, _, inner = _scrollable(root, bg=C["bg"])
        outer.grid(row=1, column=0, sticky="nsew")

        if not STATE.historial:
            tk.Label(inner, text="📊  Sin datos de ventas aún.\nRealiza tu primera venta.",
                     font=FONTS["h1"], bg=C["bg"], fg=C["text3"],
                     justify="center").pack(pady=60)
            return root

        # KPIs totales
        total_rev = sum(h["total"] for h in STATE.historial)
        hoy = datetime.date.today().strftime("%d/%m")
        rev_hoy = sum(h["total"] for h in STATE.historial if h["fecha"].startswith(hoy))
        n_sales = len(STATE.historial)
        avg_ticket = total_rev / n_sales if n_sales else 0

        kpi_f = tk.Frame(inner, bg=C["bg"])
        kpi_f.pack(fill="x", padx=12, pady=8)
        kpi_f.grid_columnconfigure((0,1,2,3), weight=1)
        for col, (lbl, val, col_c) in enumerate([
            ("Ventas Totales",   _fmt(total_rev), C["accent3"]),
            ("Ventas Hoy",       _fmt(rev_hoy),   C["accent"]),
            ("N° Transacciones", str(n_sales),     C["blue"]),
            ("Ticket Promedio",  _fmt(avg_ticket), C["accent2"]),
        ]):
            c = _card(kpi_f, bg=C["card"])
            c.grid(row=0, column=col, padx=6, sticky="ew")
            tk.Label(c, text=val, font=FONTS["kpi"], bg=C["card"],
                     fg=col_c).pack(pady=(12,2))
            tk.Label(c, text=lbl, font=FONTS["small"], bg=C["card"],
                     fg=C["text3"]).pack(pady=(0,12))

        # Gráfico platos más vendidos
        if MPL_OK:
            conteo = defaultdict(int)
            for h in STATE.historial:
                for it in h.get("detalle", []):
                    conteo[it["nombre"]] += it["cant"]
            items = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:10]
            if items:
                chart_f = _card(inner, bg=C["card"])
                chart_f.pack(fill="x", padx=12, pady=8)
                tk.Label(chart_f, text="Top 10 Platos Más Pedidos",
                         font=FONTS["h2"], bg=C["card"], fg=C["text"]).pack(
                         anchor="w", padx=16, pady=(12,4))
                labels = [x[0][:18] for x in items]
                values = [x[1] for x in items]
                colors = [CAT_COLORS.get(next((cat for cat, its in STATE.menu_data.items()
                          for i in its if i["nombre"]==x[0]), None), C["accent"])
                          for x in items]
                fig, ax = plt.subplots(figsize=(9, 3), facecolor=C["card"])
                bars = ax.bar(range(len(labels)), values, color=colors, edgecolor="none")
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=7)
                ax.set_facecolor(C["card"])
                ax.tick_params(colors=C["text2"])
                for spine in ax.spines.values():
                    spine.set_edgecolor(C["border"])
                for bar, val in zip(bars, values):
                    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
                            str(val), ha="center", va="bottom", fontsize=8,
                            color=C["text2"])
                plt.tight_layout(pad=0.8)
                canvas = FigureCanvasTkAgg(fig, master=chart_f)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="x", padx=12, pady=(0,12))
                plt.close(fig)

            # Gráfico métodos de pago
            pay_conteo = defaultdict(float)
            for h in STATE.historial:
                pay_conteo[h["metodo_pago"]] += h["total"]
            if pay_conteo:
                pie_f = _card(inner, bg=C["card"])
                pie_f.pack(fill="x", padx=12, pady=8)
                tk.Label(pie_f, text="Distribución por Método de Pago",
                         font=FONTS["h2"], bg=C["card"], fg=C["text"]).pack(
                         anchor="w", padx=16, pady=(12,4))
                pie_labels = list(pay_conteo.keys())
                pie_vals   = list(pay_conteo.values())
                pie_colors = [C["accent3"],C["blue"],C["purple"],C["accent2"],C["accent"],C["red"]]
                fig2, ax2 = plt.subplots(figsize=(5, 2.5), facecolor=C["card"])
                wedges, texts, autotexts = ax2.pie(
                    pie_vals, labels=pie_labels, autopct="%1.1f%%",
                    colors=pie_colors[:len(pie_vals)], startangle=90,
                    textprops={"color": C["text2"], "fontsize": 8})
                for at in autotexts:
                    at.set_color(C["white"])
                ax2.set_facecolor(C["card"])
                plt.tight_layout(pad=0.3)
                canvas2 = FigureCanvasTkAgg(fig2, master=pie_f)
                canvas2.draw()
                canvas2.get_tk_widget().pack(padx=12, pady=(0,12))
                plt.close(fig2)

        # Tabla historial
        hist_f = _card(inner, bg=C["card"])
        hist_f.pack(fill="x", padx=12, pady=8)
        tk.Label(hist_f, text="Historial de Ventas", font=FONTS["h2"],
                 bg=C["card"], fg=C["text"]).pack(anchor="w", padx=16, pady=(12,4))
        cols_t = ("N°","Mesa","Fecha","Cliente","Pago","Items","Total")
        tree = ttk.Treeview(hist_f, columns=cols_t, show="headings", height=12)
        for col in cols_t:
            tree.heading(col, text=col)
            widths = {"N°":40,"Mesa":60,"Fecha":140,"Cliente":120,"Pago":100,"Items":50,"Total":90}
            tree.column(col, width=widths.get(col,90), anchor="center")
        for i, h in enumerate(reversed(STATE.historial), 1):
            tree.insert("", "end", values=(
                str(i), f"Mesa {h['mesa']}", h['fecha'],
                h.get("cliente","—"), h["metodo_pago"],
                str(h["items"]), _fmt(h["total"])))
        vsb = ttk.Scrollbar(hist_f, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="x", expand=True, padx=(12,0), pady=(0,12))
        vsb.pack(side="right", fill="y", pady=(0,12))

        return root

    def _exportar_excel(self):
        if not EXCEL_OK:
            messagebox.showerror("Error","Instala pandas y openpyxl:\npip install pandas openpyxl")
            return
        if not STATE.historial:
            messagebox.showinfo("Info","Sin datos para exportar.")
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel","*.xlsx")],
            initialfile=f"ventas_{ts}.xlsx")
        if not path:
            return
        try:
            resumen = []
            detalle = []
            for h in STATE.historial:
                resumen.append({
                    "Mesa": h["mesa"], "Fecha": h["fecha"],
                    "Cliente": h.get("cliente",""), "Pago": h["metodo_pago"],
                    "Subtotal": h["subtotal"], "IGV": h["igv"], "Total": h["total"]
                })
                for it in h.get("detalle",[]):
                    detalle.append({
                        "Mesa": h["mesa"], "Fecha": h["fecha"],
                        "Plato": it["nombre"], "Cantidad": it["cant"],
                        "P.Unit": it["precio"], "Total": it["precio"]*it["cant"]
                    })
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                pd.DataFrame(resumen).to_excel(writer, sheet_name="Resumen", index=False)
                pd.DataFrame(detalle).to_excel(writer, sheet_name="Detalle", index=False)
            messagebox.showinfo("✅ Exportado", f"Archivo guardado en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════════════
    #  VISTA: ADMINISTRACIÓN
    # ══════════════════════════════════════════════════════════════
    def _view_admin(self):
        root = tk.Frame(self.content, bg=C["bg"])
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        hdr = tk.Frame(root, bg=C["bg"])
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20,8))
        _label(hdr, "⚙️  Administración", FONTS["title"], fg=C["text"]).pack(side="left")

        # Tabs admin
        tab_bar = tk.Frame(root, bg=C["bg"])
        tab_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=0)
        self.admin_content = tk.Frame(root, bg=C["bg"])
        self.admin_content.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        root.grid_rowconfigure(2, weight=1)

        self._admin_tabs = {}
        for key, lbl in [("carta","📋 Carta"),("config","🔧 Configuración"),("mesas_cfg","🪑 Mesas")]:
            b = tk.Button(tab_bar, text=lbl, font=FONTS["body"], relief="flat",
                          padx=12, pady=8, cursor="hand2",
                          command=lambda k=key: self._admin_nav(k))
            _style_btn(b, bg=C["surface3"])
            b.pack(side="left", padx=4)
            self._admin_tabs[key] = b
        self._admin_nav("carta")
        return root

    def _admin_nav(self, key):
        for k, b in self._admin_tabs.items():
            _style_btn(b, bg=C["accent"] if k==key else C["surface3"])
        for w in self.admin_content.winfo_children(): w.destroy()
        builders = {
            "carta":      self._admin_carta,
            "config":     self._admin_config,
            "mesas_cfg":  self._admin_mesas,
        }
        builders[key](self.admin_content)

    def _admin_carta(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=2)
        parent.grid_rowconfigure(0, weight=1)

        # Panel categorías
        left = _card(parent, bg=C["card"])
        left.grid(row=0, column=0, padx=(16,4), pady=12, sticky="nsew")
        tk.Label(left, text="Categorías", font=FONTS["h2"],
                 bg=C["card"], fg=C["text"]).pack(anchor="w", padx=12, pady=(10,4))
        self.cat_listbox = tk.Listbox(left, bg=C["surface2"], fg=C["text"],
                                      selectbackground=C["accent"],
                                      font=FONTS["body"], relief="flat")
        self.cat_listbox.pack(fill="both", expand=True, padx=8, pady=4)
        for cat in STATE.menu_data.keys():
            self.cat_listbox.insert("end", cat)
        self.cat_listbox.bind("<<ListboxSelect>>",
                               lambda e: self._load_cat_items(right_items))

        btn_f = tk.Frame(left, bg=C["card"])
        btn_f.pack(fill="x", padx=8, pady=6)
        self.new_cat_var = tk.StringVar()
        tk.Entry(btn_f, textvariable=self.new_cat_var, font=FONTS["small"],
                 bg=C["surface3"], fg=C["text"], relief="flat").pack(fill="x", pady=2)
        b = tk.Button(btn_f, text="+ Nueva Categoría", font=FONTS["small"],
                      relief="flat", pady=4, cursor="hand2",
                      command=lambda: self._add_categoria(right_items))
        _style_btn(b, bg=C["accent3"])
        b.pack(fill="x", pady=2)

        # Panel items
        right = _card(parent, bg=C["card"])
        right.grid(row=0, column=1, padx=(4,16), pady=12, sticky="nsew")
        tk.Label(right, text="Platos de la Categoría", font=FONTS["h2"],
                 bg=C["card"], fg=C["text"]).pack(anchor="w", padx=12, pady=(10,4))

        cols_t = ("Emoji","Nombre","Precio","Descripción")
        right_items = ttk.Treeview(right, columns=cols_t, show="headings", height=14)
        for c in cols_t:
            right_items.heading(c, text=c)
            right_items.column(c, width={"Emoji":50,"Nombre":160,"Precio":80,"Descripción":200}.get(c,120))
        right_items.pack(fill="both", expand=True, padx=8, pady=4)

        # Form agregar ítem
        form_f = tk.Frame(right, bg=C["card"])
        form_f.pack(fill="x", padx=8, pady=4)
        self.item_vars = {}
        fields = [("emoji","Emoji"),("nombre","Nombre"),("precio","Precio"),("desc","Descripción")]
        for key, lbl in fields:
            row = tk.Frame(form_f, bg=C["card"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=lbl, font=FONTS["small"], bg=C["card"],
                     fg=C["text2"], width=12, anchor="w").pack(side="left")
            var = tk.StringVar()
            self.item_vars[key] = var
            tk.Entry(row, textvariable=var, font=FONTS["small"],
                     bg=C["surface3"], fg=C["text"], relief="flat").pack(
                     side="left", fill="x", expand=True, padx=4)

        self._editing_nombre = None

        btn_row = tk.Frame(form_f, bg=C["card"])
        btn_row.pack(fill="x", pady=4)
        b1 = tk.Button(btn_row, text="+ Agregar Plato", font=FONTS["small"],
                       relief="flat", padx=8, pady=5, cursor="hand2",
                       command=lambda: self._add_item(right_items))
        _style_btn(b1, bg=C["accent3"])
        b1.pack(side="left", padx=4)
        b3 = tk.Button(btn_row, text="✏️ Modificar", font=FONTS["small"],
                       relief="flat", padx=8, pady=5, cursor="hand2",
                       command=lambda: self._load_item_to_form(right_items))
        _style_btn(b3, bg=C["blue"])
        b3.pack(side="left", padx=4)
        b2 = tk.Button(btn_row, text="🗑 Eliminar", font=FONTS["small"],
                       relief="flat", padx=8, pady=5, cursor="hand2",
                       command=lambda: self._del_item_cat(right_items))
        _style_btn(b2, bg=C["red"])
        b2.pack(side="left", padx=4)

    def _get_sel_cat(self):
        sel = self.cat_listbox.curselection()
        if not sel: return None
        return self.cat_listbox.get(sel[0])

    def _load_cat_items(self, tree):
        cat = self._get_sel_cat()
        if not cat: return
        for row in tree.get_children(): tree.delete(row)
        for it in STATE.menu_data.get(cat, []):
            tree.insert("", "end", values=(
                it.get("emoji",""), it["nombre"],
                _fmt(it["precio"]), it.get("desc","")))

    def _add_categoria(self, tree):
        name = self.new_cat_var.get().strip()
        if not name: return
        if name not in STATE.menu_data:
            STATE.menu_data[name] = []
            self.cat_listbox.insert("end", name)
        self.new_cat_var.set("")

    def _load_item_to_form(self, tree):
        cat = self._get_sel_cat()
        if not cat:
            messagebox.showwarning("Aviso", "Selecciona una categoría primero.")
            return
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un plato para modificar.")
            return
        vals = tree.item(sel[0])["values"]
        self.item_vars["emoji"].set(vals[0] if vals[0] else "")
        self.item_vars["nombre"].set(vals[1])
        precio_str = str(vals[2]).replace(CONFIG["moneda"], "").replace(",", "").strip()
        self.item_vars["precio"].set(precio_str)
        self.item_vars["desc"].set(vals[3] if len(vals) > 3 else "")
        self._editing_nombre = vals[1]

    def _add_item(self, tree):
        cat = self._get_sel_cat()
        if not cat:
            messagebox.showwarning("Aviso","Selecciona una categoría primero.")
            return
        nom = self.item_vars["nombre"].get().strip()
        if not nom:
            messagebox.showwarning("Aviso","El nombre es obligatorio.")
            return
        try:
            precio = float(self.item_vars["precio"].get())
        except ValueError:
            messagebox.showwarning("Aviso","Precio inválido.")
            return
        it = {
            "nombre": nom,
            "precio": precio,
            "emoji":  self.item_vars["emoji"].get() or "🍽️",
            "desc":   self.item_vars["desc"].get(),
        }
        editing = getattr(self, "_editing_nombre", None)
        if editing:
            for i, existing in enumerate(STATE.menu_data[cat]):
                if existing["nombre"] == editing:
                    STATE.menu_data[cat][i] = it
                    break
            self._editing_nombre = None
        else:
            STATE.menu_data[cat].append(it)
        for k in self.item_vars: self.item_vars[k].set("")
        self._load_cat_items(tree)

    def _del_item_cat(self, tree):
        cat = self._get_sel_cat()
        if not cat: return
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0])["values"]
        nombre = vals[1]
        STATE.menu_data[cat] = [i for i in STATE.menu_data[cat] if i["nombre"]!=nombre]
        self._load_cat_items(tree)

    def _admin_config(self, parent):
        outer, _, inner = _scrollable(parent, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=16, pady=12)
        c = _card(inner, bg=C["card"])
        c.pack(fill="x", pady=8)
        tk.Label(c, text="Configuración del Restaurante", font=FONTS["h2"],
                 bg=C["card"], fg=C["text"]).pack(anchor="w", padx=16, pady=(12,8))
        self.cfg_vars = {}
        fields = [
            ("nombre",    "Nombre del Restaurante"),
            ("ruc",       "RUC / NIT"),
            ("direccion", "Dirección"),
            ("telefono",  "Teléfono"),
            ("moneda",    "Símbolo Moneda"),
            ("yape",      "Número Yape"),
            ("plin",      "Número Plin"),
            ("nequi",     "Número Nequi"),
            ("daviplata", "Número Daviplata"),
            ("whatsapp",  "WhatsApp (con código país)"),
        ]
        for key, lbl in fields:
            row = tk.Frame(c, bg=C["card"])
            row.pack(fill="x", padx=16, pady=3)
            tk.Label(row, text=lbl, font=FONTS["small"], bg=C["card"],
                     fg=C["text2"], width=28, anchor="w").pack(side="left")
            var = tk.StringVar(value=CONFIG.get(key, ""))
            self.cfg_vars[key] = var
            tk.Entry(row, textvariable=var, font=FONTS["small"],
                     bg=C["surface2"], fg=C["text"], relief="flat", width=32,
                     insertbackground=C["text"]).pack(side="left", padx=8)

        igv_row = tk.Frame(c, bg=C["card"])
        igv_row.pack(fill="x", padx=16, pady=3)
        tk.Label(igv_row, text="IGV (%)", font=FONTS["small"], bg=C["card"],
                 fg=C["text2"], width=28, anchor="w").pack(side="left")
        self.igv_var = tk.StringVar(value=str(int(CONFIG["igv"]*100)))
        tk.Entry(igv_row, textvariable=self.igv_var, font=FONTS["small"],
                 bg=C["surface2"], fg=C["text"], relief="flat", width=8,
                 insertbackground=C["text"]).pack(side="left", padx=8)

        btn = tk.Button(c, text="💾 Guardar Configuración", font=FONTS["body"],
                        relief="flat", padx=12, pady=8, cursor="hand2",
                        command=self._save_config)
        _style_btn(btn, bg=C["accent3"])
        btn.pack(pady=12)

    def _save_config(self):
        for key, var in self.cfg_vars.items():
            CONFIG[key] = var.get()
        try:
            CONFIG["igv"] = float(self.igv_var.get()) / 100
        except ValueError:
            pass
        messagebox.showinfo("✅", "Configuración guardada.")

    def _admin_mesas(self, parent):
        c = _card(parent, bg=C["card"])
        c.pack(fill="x", padx=16, pady=12)
        tk.Label(c, text="Configuración de Mesas", font=FONTS["h2"],
                 bg=C["card"], fg=C["text"]).pack(anchor="w", padx=16, pady=(12,4))
        row = tk.Frame(c, bg=C["card"])
        row.pack(fill="x", padx=16, pady=4)
        tk.Label(row, text="Número de mesas:", font=FONTS["body"],
                 bg=C["card"], fg=C["text2"]).pack(side="left")
        self.mesas_var = tk.IntVar(value=CONFIG["mesas"])
        tk.Spinbox(row, from_=1, to=50, textvariable=self.mesas_var,
                   font=FONTS["body"], bg=C["surface2"], fg=C["text"],
                   width=6).pack(side="left", padx=8)
        def apply_mesas():
            n = self.mesas_var.get()
            CONFIG["mesas"] = n
            # Añadir mesas faltantes
            for i in range(1, n+1):
                if i not in STATE.mesas:
                    STATE.mesas[i] = {"estado":"libre","pedido":[],"inicio":None,
                                      "personas":0,"mozo":"—"}
            # Quitar excedentes libres
            for i in list(STATE.mesas.keys()):
                if i > n and STATE.mesas[i]["estado"]=="libre":
                    del STATE.mesas[i]
            messagebox.showinfo("✅",f"Mesas configuradas: {n}")
            self._nav("mesas")
        btn = tk.Button(c, text="Aplicar", font=FONTS["body"], relief="flat",
                        padx=10, pady=6, cursor="hand2", command=apply_mesas)
        _style_btn(btn, bg=C["accent"])
        btn.pack(pady=8)


# ══════════════════════════════════════════════════════════════════
#  PANTALLA DE INICIO / LOGIN
# ══════════════════════════════════════════════════════════════════
class LoginScreen(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ERP Restaurante — Acceso")
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self._build()

    def _build(self):
        tk.Label(self, text="🍽️", font=("Segoe UI",56),
                 bg=C["bg"], fg=C["accent"]).pack(pady=(48,4))
        tk.Label(self, text=CONFIG["nombre"], font=FONTS["title"],
                 bg=C["bg"], fg=C["text"]).pack()
        tk.Label(self, text="Sistema de Gestión ERP", font=FONTS["body"],
                 bg=C["bg"], fg=C["text3"]).pack(pady=(0,36))

        f = _card(self, bg=C["card"])
        f.pack(padx=60, pady=4, fill="x")
        tk.Label(f, text="Usuario", font=FONTS["small"],
                 bg=C["card"], fg=C["text2"], anchor="w").pack(fill="x", padx=20, pady=(14,2))
        self.user_e = tk.Entry(f, font=FONTS["body"], bg=C["surface2"],
                               fg=C["text"], relief="flat", insertbackground=C["text"])
        self.user_e.pack(fill="x", padx=20, ipady=8)
        self.user_e.insert(0, "admin")

        tk.Label(f, text="Contraseña", font=FONTS["small"],
                 bg=C["card"], fg=C["text2"], anchor="w").pack(fill="x", padx=20, pady=(8,2))
        self.pass_e = tk.Entry(f, font=FONTS["body"], bg=C["surface2"],
                               fg=C["text"], relief="flat", insertbackground=C["text"], show="●")
        self.pass_e.pack(fill="x", padx=20, ipady=8)
        self.pass_e.insert(0, "1234")
        self.pass_e.bind("<Return>", lambda e: self._login())

        btn = tk.Button(f, text="Ingresar al Sistema",
                        font=FONTS["h2"], relief="flat",
                        padx=12, pady=12, cursor="hand2",
                        command=self._login)
        _style_btn(btn, bg=C["accent"])
        btn.pack(fill="x", padx=20, pady=(16,20))

        tk.Label(self, text=f"v2.0  ·  {CONFIG['ruc']}  ·  {CONFIG['direccion']}",
                 font=FONTS["small"], bg=C["bg"], fg=C["text3"]).pack(pady=20)

    def _login(self):
        # Validación simple — personaliza credenciales aquí
        user = self.user_e.get().strip()
        pwd  = self.pass_e.get().strip()
        if user == "admin" and pwd == "1234":
            self.destroy()
            app = RestauranteApp()
            app.mainloop()
        else:
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.\n\n(Demo: admin / 1234)")


# ══════════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Mostrar qué dependencias opcionales están presentes
    missing = []
    if not PIL_OK:       missing.append("Pillow")
    if not REQUESTS_OK:  missing.append("requests")
    if not MPL_OK:       missing.append("matplotlib")
    if not EXCEL_OK:     missing.append("pandas / openpyxl")
    if missing:
        print(f"ℹ️  Dependencias opcionales no instaladas: {', '.join(missing)}")
        print("   Instálalas con: pip install " + " ".join(missing))
        print()

    login = LoginScreen()
    login.mainloop()
