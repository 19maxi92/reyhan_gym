"""
Panel de Administración — Monitor de la notebook.
Secciones: Dashboard · Socios · Pagos · Planes · Puerta · Backup
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import db.database as db
from core.puerta import puerta, listar_dispositivos_hid, guardar_config

# ─── TEMAS ─────────────────────────────────────────────────────────────────────
TEMAS = {
    "dark": {
        "BG":            "#1a1a1a",
        "SIDEBAR_BG":    "#2e2e2e",
        "CARD_BG":       "#252525",
        "ENTRADA_BG":    "#2a2a2a",
        "ACENTO":        "#f4812e",
        "TEXT":          "#f5f5f5",
        "TEXT_DIM":      "#aaaaaa",
        "SEP":           "#2a2a2a",
        "TREE_BG":       "#1e1e1e",
        "TREE_HEAD":     "#0d0d0d",
        "SIDEBAR_ACT":   "#3a3a3a",
        "BTN_CANCEL":    "#333333",
        "BTN_CANCEL_FG": "#f5f5f5",
    },
    "claro": {
        "BG":            "#f5f5f5",
        "SIDEBAR_BG":    "#e8e8e8",
        "CARD_BG":       "#ffffff",
        "ENTRADA_BG":    "#ffffff",
        "ACENTO":        "#d96818",
        "TEXT":          "#1a1a1a",
        "TEXT_DIM":      "#555555",
        "SEP":           "#cccccc",
        "TREE_BG":       "#ffffff",
        "TREE_HEAD":     "#d0d0d0",
        "SIDEBAR_ACT":   "#cccccc",
        "BTN_CANCEL":    "#cccccc",
        "BTN_CANCEL_FG": "#1a1a1a",
    },
}

OK    = "#2ecc71"
ERROR = "#e74c3c"
WARN  = "#f39c12"

FONT_TITULO  = ("Georgia", 18, "bold")
FONT_LABEL   = ("Segoe UI", 10)
FONT_BOLD    = ("Segoe UI", 10, "bold")
FONT_SMALL   = ("Segoe UI", 9)
FONT_SIDEBAR = ("Segoe UI", 11)

_tema = {"actual": "dark"}


def T(key):
    return TEMAS[_tema["actual"]][key]


def entrada(parent, textvariable=None, width=30, **kw):
    return tk.Entry(
        parent, textvariable=textvariable, width=width,
        bg=T("ENTRADA_BG"), fg=T("TEXT"), insertbackground=T("TEXT"),
        relief="flat", font=FONT_LABEL,
        highlightthickness=1,
        highlightbackground=T("SEP"),
        highlightcolor=T("ACENTO"), **kw
    )


def boton(parent, text, command, color=None, fg=None, **kw):
    c  = color or T("ACENTO")
    fg = fg or ("#000000" if _tema["actual"] == "dark" else "#ffffff")
    return tk.Button(
        parent, text=text, command=command,
        bg=c, fg=fg, font=FONT_BOLD,
        relief="flat", cursor="hand2",
        activebackground=c, activeforeground=fg,
        padx=12, pady=6, **kw
    )


# ══════════════════════════════════════════════════════════════════════════════
class PanelAdmin(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T("BG"))
        self.pack(fill="both", expand=True)
        self._seccion_actual = None
        self._build()
        self.mostrar_dashboard()

    # ─── SIDEBAR ──────────────────────────────────────────────────────────────
    def _build(self):
        self.sidebar = tk.Frame(self, bg=T("SIDEBAR_BG"), width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        self.lbl_gym = tk.Label(
            self.sidebar, text="REYHAN", font=("Georgia", 22, "bold"),
            fg=T("ACENTO"), bg=T("SIDEBAR_BG")
        )
        self.lbl_gym.pack(pady=(24, 2))
        self.lbl_sub = tk.Label(
            self.sidebar, text="Centro de Entrenamiento",
            font=FONT_SMALL, fg=T("TEXT_DIM"), bg=T("SIDEBAR_BG")
        )
        self.lbl_sub.pack(pady=(0, 12))

        self.sep_top = tk.Frame(self.sidebar, bg=T("SEP"), height=1)
        self.sep_top.pack(fill="x", padx=16, pady=(0, 8))

        # Botones de navegación
        self._btns_sidebar = {}
        secciones = [
            ("📊 Dashboard",  self.mostrar_dashboard),
            ("👥 Socios",     self.mostrar_socios),
            ("💰 Pagos",      self.mostrar_pagos),
            ("📋 Planes",     self.mostrar_planes),
            ("🚪 Puerta",     self.mostrar_puerta),
            ("💾 Backup",     self.hacer_backup),
        ]
        for nombre, cmd in secciones:
            b = tk.Button(
                self.sidebar, text=nombre, command=cmd,
                bg=T("SIDEBAR_BG"), fg=T("TEXT"),
                font=FONT_SIDEBAR, relief="flat",
                anchor="w", padx=20, pady=10,
                activebackground=T("SIDEBAR_ACT"),
                activeforeground=T("ACENTO"),
                cursor="hand2"
            )
            b.pack(fill="x")
            self._btns_sidebar[nombre] = b

        # Separador inferior + toggle tema al fondo del sidebar
        self.sep_bot = tk.Frame(self.sidebar, bg=T("SEP"), height=1)
        self.sep_bot.pack(side="bottom", fill="x", padx=16, pady=4)

        self.btn_tema = tk.Button(
            self.sidebar, text="☀  Modo Claro",
            command=self._toggle_tema,
            bg=T("SIDEBAR_BG"), fg=T("TEXT_DIM"),
            font=("Segoe UI", 9), relief="flat",
            cursor="hand2", pady=8,
            activebackground=T("SIDEBAR_ACT"),
            activeforeground=T("ACENTO")
        )
        self.btn_tema.pack(side="bottom", fill="x")

        # Área de contenido
        self.contenido = tk.Frame(self, bg=T("BG"))
        self.contenido.pack(side="left", fill="both", expand=True)

    # ─── TEMA ─────────────────────────────────────────────────────────────────
    def _toggle_tema(self):
        _tema["actual"] = "claro" if _tema["actual"] == "dark" else "dark"
        self._aplicar_tema()
        if self._seccion_actual:
            self._seccion_actual()
        else:
            self.mostrar_dashboard()

    def _aplicar_tema(self):
        self.configure(bg=T("BG"))
        self.sidebar.configure(bg=T("SIDEBAR_BG"))
        self.contenido.configure(bg=T("BG"))
        self.lbl_gym.configure(fg=T("ACENTO"), bg=T("SIDEBAR_BG"))
        self.lbl_sub.configure(fg=T("TEXT_DIM"), bg=T("SIDEBAR_BG"))
        self.sep_top.configure(bg=T("SEP"))
        self.sep_bot.configure(bg=T("SEP"))
        icono = "🌙  Modo Oscuro" if _tema["actual"] == "claro" else "☀  Modo Claro"
        self.btn_tema.configure(
            text=icono, bg=T("SIDEBAR_BG"), fg=T("TEXT_DIM"),
            activebackground=T("SIDEBAR_ACT"), activeforeground=T("ACENTO")
        )
        for b in self._btns_sidebar.values():
            b.configure(
                bg=T("SIDEBAR_BG"), fg=T("TEXT"),
                activebackground=T("SIDEBAR_ACT"), activeforeground=T("ACENTO")
            )
        try:
            self.winfo_toplevel().configure(bg=T("BG"))
        except Exception:
            pass

    # ─── HELPERS ──────────────────────────────────────────────────────────────
    def _limpiar(self):
        for w in self.contenido.winfo_children():
            w.destroy()

    def _titulo(self, texto):
        tk.Label(
            self.contenido, text=texto, font=FONT_TITULO,
            fg=T("ACENTO"), bg=T("BG")
        ).pack(anchor="w", padx=24, pady=(20, 4))
        tk.Frame(self.contenido, bg=T("ACENTO"), height=2).pack(
            fill="x", padx=24, pady=(0, 16)
        )

    def _tabla(self, parent, cols):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Gym.Treeview",
            background=T("TREE_BG"), foreground=T("TEXT"),
            rowheight=28, fieldbackground=T("TREE_BG"),
            borderwidth=0, font=FONT_SMALL)
        style.configure("Gym.Treeview.Heading",
            background=T("TREE_HEAD"), foreground=T("ACENTO"),
            font=FONT_BOLD, relief="flat")
        style.map("Gym.Treeview", background=[("selected", T("ENTRADA_BG"))])

        frame = tk.Frame(parent, bg=T("BG"))
        tree  = ttk.Treeview(frame, columns=cols, show="headings",
                              style="Gym.Treeview", height=14)
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="w")
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return frame, tree

    # ══════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    def mostrar_dashboard(self):
        self._seccion_actual = self.mostrar_dashboard
        self._limpiar()
        self._titulo("📊 Dashboard")
        data = db.get_dashboard()

        frame_cards = tk.Frame(self.contenido, bg=T("BG"))
        frame_cards.pack(fill="x", padx=24, pady=8)
        cards = [
            ("Socios Activos",      str(data["total_activos"]),          T("ACENTO")),
            ("Cuotas Vencidas",     str(data["vencidos"]),                ERROR),
            ("Vencen en 7 días",    str(len(data["proximos_a_vencer"])), WARN),
            ("Cumpleaños este mes", str(len(data["cumples_mes"])),         OK),
        ]
        for titulo, valor, color in cards:
            c = tk.Frame(frame_cards, bg=T("CARD_BG"), padx=20, pady=16)
            c.pack(side="left", padx=8, ipadx=10)
            tk.Label(c, text=valor, font=("Georgia", 32, "bold"),
                     fg=color, bg=T("CARD_BG")).pack()
            tk.Label(c, text=titulo, font=FONT_SMALL,
                     fg=T("TEXT_DIM"), bg=T("CARD_BG")).pack()

        # Próximos a vencer
        fp = tk.Frame(self.contenido, bg=T("BG"))
        fp.pack(fill="both", expand=True, padx=24, pady=8)
        tk.Label(fp, text="⏰ Vencen próximamente",
                 font=FONT_BOLD, fg=WARN, bg=T("BG")).pack(anchor="w", pady=(8, 4))
        if data["proximos_a_vencer"]:
            ft, tree = self._tabla(fp, ("Apellido", "Nombre", "Celular", "Vence"))
            for s in data["proximos_a_vencer"]:
                tree.insert("", "end", values=(
                    s["apellido"], s["nombre"],
                    s["celular"] or "-", s["fecha_vencimiento"]
                ))
            ft.pack(fill="x", pady=4)
        else:
            tk.Label(fp, text="No hay socios próximos a vencer.",
                     fg=T("TEXT_DIM"), bg=T("BG"), font=FONT_SMALL).pack(anchor="w")

        # Cumpleaños
        fc = tk.Frame(self.contenido, bg=T("BG"))
        fc.pack(fill="x", padx=24, pady=8)
        tk.Label(fc, text="🎂 Cumpleaños del mes",
                 font=FONT_BOLD, fg=OK, bg=T("BG")).pack(anchor="w", pady=(8, 4))
        if data["cumples_mes"]:
            for s in data["cumples_mes"]:
                dia = s["fecha_nacimiento"][8:10] if s["fecha_nacimiento"] else "?"
                tk.Label(fc,
                    text=f"  {dia} — {s['apellido']}, {s['nombre']}  📱 {s['celular'] or '-'}",
                    fg=T("TEXT"), bg=T("BG"), font=FONT_SMALL).pack(anchor="w")
        else:
            tk.Label(fc, text="No hay cumpleaños este mes.",
                     fg=T("TEXT_DIM"), bg=T("BG"), font=FONT_SMALL).pack(anchor="w")

    # ══════════════════════════════════════════════════════════════════════════
    # SOCIOS
    # ══════════════════════════════════════════════════════════════════════════
    def mostrar_socios(self):
        self._seccion_actual = self.mostrar_socios
        self._limpiar()
        self._titulo("👥 Socios")

        bar = tk.Frame(self.contenido, bg=T("BG"))
        bar.pack(fill="x", padx=24, pady=4)
        self.var_buscar = tk.StringVar()
        self.var_buscar.trace("w", lambda *a: self._actualizar_lista())
        entrada(bar, textvariable=self.var_buscar, width=36).pack(side="left", ipady=4)
        tk.Label(bar, text="  🔍 Nombre, DNI, celular...",
                 fg=T("TEXT_DIM"), bg=T("BG"), font=FONT_SMALL).pack(side="left")
        boton(bar, "+ Nuevo Socio", self._form_nuevo_socio).pack(side="right")

        cols = ("DNI", "Apellido", "Nombre", "Celular", "Plan", "Estado")
        ft, self.tree_socios = self._tabla(self.contenido, cols)
        ft.pack(fill="both", expand=True, padx=24, pady=8)
        self.tree_socios.bind("<Double-1>", lambda e: self._abrir_socio())
        tk.Label(self.contenido, text="Doble click para editar",
                 fg=T("TEXT_DIM"), bg=T("BG"), font=FONT_SMALL).pack(pady=4)
        self._actualizar_lista()

    def _actualizar_lista(self):
        texto  = self.var_buscar.get() if hasattr(self, "var_buscar") else ""
        socios = db.buscar_socios(texto)
        self.tree_socios.delete(*self.tree_socios.get_children())
        for s in socios:
            vigente = db.cuota_vigente(s["id"])
            self.tree_socios.insert("", "end", iid=s["id"], values=(
                s["dni"], s["apellido"], s["nombre"],
                s["celular"] or "-", s["plan_nombre"] or "-",
                "✅ Al día" if vigente else "❌ Vencida"
            ))

    def _abrir_socio(self):
        sel = self.tree_socios.selection()
        if not sel:
            return
        socio = db.get_socio_por_id(int(sel[0]))
        if socio:
            self._form_socio(socio)

    def _form_nuevo_socio(self):
        self._form_socio(None)

    def _form_socio(self, socio=None):
        win = tk.Toplevel(self)
        win.title("Nuevo Socio" if not socio
                  else f"Editar — {socio['apellido']}, {socio['nombre']}")
        win.configure(bg=T("BG"))
        win.resizable(False, False)
        win.grab_set()

        planes       = db.get_planes()
        plan_nombres = [f"{p['nombre']}  (${p['precio']:.0f})" for p in planes]
        plan_ids     = [p["id"] for p in planes]
        campos       = {}

        def fila(label, key, valor="", obligatorio=False):
            f = tk.Frame(win, bg=T("BG"))
            f.pack(fill="x", padx=20, pady=3)
            tk.Label(f, text=label + (" *" if obligatorio else ""),
                     fg=T("TEXT") if obligatorio else T("TEXT_DIM"),
                     bg=T("BG"), font=FONT_SMALL, width=18, anchor="w").pack(side="left")
            v = tk.StringVar(value=valor or "")
            entrada(f, textvariable=v, width=32).pack(side="left", ipady=3)
            campos[key] = v

        tk.Label(win, text="Datos del Socio", font=FONT_TITULO,
                 fg=T("ACENTO"), bg=T("BG")).pack(pady=(16, 8))

        fila("DNI",           "dni",              socio["dni"]                      if socio else "", True)
        fila("Nombre",        "nombre",           socio["nombre"]                   if socio else "", True)
        fila("Apellido",      "apellido",         socio["apellido"]                 if socio else "", True)
        fila("Celular",       "celular",          socio["celular"]                  if socio else "", True)
        fila("Fecha Nac.",    "fecha_nacimiento", socio.get("fecha_nacimiento", "") if socio else "")
        fila("Email",         "email",            socio.get("email", "")            if socio else "")
        fila("Observaciones", "observaciones",    socio.get("observaciones", "")    if socio else "")

        fp = tk.Frame(win, bg=T("BG"))
        fp.pack(fill="x", padx=20, pady=3)
        fp.columnconfigure(1, weight=1)
        tk.Label(fp, text="Plan *", fg=T("TEXT"), bg=T("BG"),
                 font=FONT_SMALL, anchor="w", width=16).grid(row=0, column=0, sticky="w", padx=(0,10))
        var_plan = tk.StringVar()
        combo = ttk.Combobox(fp, textvariable=var_plan,
                             values=plan_nombres, state="readonly", width=30)
        if socio and socio.get("plan_id"):
            idx = next((i for i, pid in enumerate(plan_ids) if pid == socio["plan_id"]), 0)
            combo.current(idx)
        elif plan_nombres:
            combo.current(0)
        combo.grid(row=0, column=1, sticky="ew")

        def guardar():
            dni      = campos["dni"].get().strip()
            nombre   = campos["nombre"].get().strip()
            apellido = campos["apellido"].get().strip()
            celular  = campos["celular"].get().strip()
            if not all([dni, nombre, apellido, celular]):
                messagebox.showerror("Faltan datos",
                    "DNI, Nombre, Apellido y Celular son obligatorios.", parent=win)
                return
            plan_idx = combo.current()
            plan_id  = plan_ids[plan_idx] if plan_idx >= 0 else None
            fn   = campos["fecha_nacimiento"].get().strip() or None
            mail = campos["email"].get().strip() or None
            obs  = campos["observaciones"].get().strip() or None
            if socio:
                db.editar_socio(socio["id"], nombre, apellido, celular, plan_id, fn, mail, obs)
                messagebox.showinfo("Guardado", "Socio actualizado.", parent=win)
            else:
                ok, msg = db.alta_socio(dni, nombre, apellido, celular, plan_id, fn, mail, obs)
                if not ok:
                    messagebox.showerror("Error", msg, parent=win)
                    return
                messagebox.showinfo("Guardado", msg, parent=win)
            win.destroy()
            self._actualizar_lista()

        def dar_baja():
            if messagebox.askyesno("Baja",
                f"¿Dar de baja a {socio['nombre']} {socio['apellido']}?", parent=win):
                db.baja_socio(socio["id"])
                win.destroy()
                self._actualizar_lista()

        # Historial de pagos
        if socio:
            pagos = db.get_pagos_socio(socio["id"])
            tk.Label(win, text="Últimos pagos", font=FONT_BOLD,
                     fg=T("ACENTO"), bg=T("BG")).pack(pady=(10, 2))
            for p in pagos[:4]:
                tk.Label(win,
                    text=f"  Pago: {p['fecha_pago']}  |  Vence: {p['fecha_vencimiento']}  |  {p['meses']} mes(es)",
                    fg=T("TEXT_DIM"), bg=T("BG"), font=FONT_SMALL).pack(anchor="w", padx=20)

        fb = tk.Frame(win, bg=T("BG"))
        fb.pack(pady=14, padx=20, fill="x")
        boton(fb, "💾 Guardar", guardar).pack(side="left", padx=4)
        if socio:
            boton(fb, "🗑 Dar de baja", dar_baja,
                  color=ERROR, fg="white").pack(side="left", padx=4)
        boton(fb, "Cancelar", win.destroy,
              color=T("BTN_CANCEL"), fg=T("BTN_CANCEL_FG")).pack(side="right", padx=4)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGOS
    # ══════════════════════════════════════════════════════════════════════════
    def mostrar_pagos(self):
        self._seccion_actual = self.mostrar_pagos
        self._limpiar()
        self._titulo("💰 Registrar Pago")

        tk.Label(self.contenido, text="Buscá al socio y hacé doble click para registrar el pago:",
                 fg=T("TEXT_DIM"), bg=T("BG"), font=FONT_SMALL).pack(anchor="w", padx=24)

        bar = tk.Frame(self.contenido, bg=T("BG"))
        bar.pack(fill="x", padx=24, pady=4)
        self.var_buscar_pago = tk.StringVar()
        self.var_buscar_pago.trace("w", lambda *a: self._actualizar_lista_pagos())
        entrada(bar, textvariable=self.var_buscar_pago, width=36).pack(side="left", ipady=4)

        cols = ("DNI", "Apellido", "Nombre", "Último pago", "Vence", "Estado")
        ft, self.tree_pagos = self._tabla(self.contenido, cols)
        ft.pack(fill="both", expand=True, padx=24, pady=8)
        self.tree_pagos.bind("<Double-1>", lambda e: self._registrar_pago_seleccionado())
        tk.Label(self.contenido, text="Doble click para registrar pago",
                 fg=T("TEXT_DIM"), bg=T("BG"), font=FONT_SMALL).pack(pady=4)
        self._actualizar_lista_pagos()

    def _actualizar_lista_pagos(self):
        texto  = self.var_buscar_pago.get() if hasattr(self, "var_buscar_pago") else ""
        socios = db.buscar_socios(texto)
        self.tree_pagos.delete(*self.tree_pagos.get_children())
        for s in socios:
            pagos   = db.get_pagos_socio(s["id"])
            ultimo  = pagos[0] if pagos else None
            vigente = db.cuota_vigente(s["id"])
            self.tree_pagos.insert("", "end", iid=s["id"], values=(
                s["dni"], s["apellido"], s["nombre"],
                ultimo["fecha_pago"]        if ultimo else "—",
                ultimo["fecha_vencimiento"] if ultimo else "—",
                "✅ Al día" if vigente else "❌ Vencida"
            ))

    def _registrar_pago_seleccionado(self):
        sel = self.tree_pagos.selection()
        if not sel:
            return
        socio = db.get_socio_por_id(int(sel[0]))
        if not socio:
            return

        win = tk.Toplevel(self)
        win.title(f"Pago — {socio['apellido']}, {socio['nombre']}")
        win.configure(bg=T("BG"))
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text=f"{socio['apellido']}, {socio['nombre']}",
                 font=FONT_TITULO, fg=T("ACENTO"), bg=T("BG")).pack(pady=(16, 4), padx=20)
        tk.Label(win, text=f"DNI: {socio['dni']}  |  Plan: {socio['plan_nombre'] or '-'}",
                 fg=T("TEXT_DIM"), bg=T("BG"), font=FONT_SMALL).pack(pady=(0, 10))

        f1 = tk.Frame(win, bg=T("BG"))
        f1.pack(fill="x", padx=20, pady=4)
        tk.Label(f1, text="Fecha de pago:", fg=T("TEXT"), bg=T("BG"),
                 font=FONT_SMALL, width=18, anchor="w").pack(side="left")
        var_fecha = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        entrada(f1, textvariable=var_fecha, width=16).pack(side="left", ipady=3)
        tk.Label(f1, text="  (AAAA-MM-DD)", fg=T("TEXT_DIM"), bg=T("BG"),
                 font=FONT_SMALL).pack(side="left")

        f2 = tk.Frame(win, bg=T("BG"))
        f2.pack(fill="x", padx=20, pady=4)
        tk.Label(f2, text="Cantidad de meses:", fg=T("TEXT"), bg=T("BG"),
                 font=FONT_SMALL, width=18, anchor="w").pack(side="left")
        var_meses = tk.IntVar(value=1)
        tk.Spinbox(f2, from_=1, to=12, textvariable=var_meses,
                   width=4, bg=T("ENTRADA_BG"), fg=T("TEXT"),
                   font=FONT_LABEL, relief="flat",
                   buttonbackground=T("SEP")).pack(side="left")

        lbl_vence = tk.Label(win, text="", fg=OK, bg=T("BG"), font=FONT_BOLD)
        lbl_vence.pack(pady=6)

        def preview(*a):
            try:
                v = db.calcular_vencimiento(var_fecha.get(), var_meses.get())
                lbl_vence.config(text=f"Vencimiento calculado: {v}", fg=OK)
            except Exception:
                lbl_vence.config(text="Fecha inválida", fg=ERROR)

        var_fecha.trace("w", preview)
        var_meses.trace("w", preview)
        preview()

        def confirmar():
            try:
                vence = db.registrar_pago(socio["id"], var_fecha.get(), var_meses.get())
                messagebox.showinfo("Listo", f"Pago registrado.\nVence: {vence}", parent=win)
                win.destroy()
                self._actualizar_lista_pagos()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        fb = tk.Frame(win, bg=T("BG"))
        fb.pack(pady=14, padx=20, fill="x")
        boton(fb, "✅ Confirmar Pago", confirmar).pack(side="left", padx=4)
        boton(fb, "Cancelar", win.destroy,
              color=T("BTN_CANCEL"), fg=T("BTN_CANCEL_FG")).pack(side="right", padx=4)

    # ══════════════════════════════════════════════════════════════════════════
    # PLANES
    # ══════════════════════════════════════════════════════════════════════════
    def mostrar_planes(self):
        self._seccion_actual = self.mostrar_planes
        self._limpiar()
        self._titulo("📋 Planes y Precios")

        tk.Label(self.contenido,
                 text="Doble click para editar. Un plan desactivado no aparece en nuevas altas pero no se pierde.",
                 fg=T("TEXT_DIM"), bg=T("BG"), font=FONT_SMALL
                 ).pack(anchor="w", padx=24, pady=(0, 6))

        cols = ("ID", "Nombre", "Precio", "Estado")
        ft, self.tree_planes = self._tabla(self.contenido, cols)
        self.tree_planes.column("ID",     width=40,  anchor="center")
        self.tree_planes.column("Nombre", width=360, anchor="w")
        self.tree_planes.column("Precio", width=100, anchor="center")
        self.tree_planes.column("Estado", width=100, anchor="center")
        ft.pack(fill="x", padx=24, pady=8)
        self.tree_planes.bind("<Double-1>", lambda e: self._editar_plan_sel())

        fb = tk.Frame(self.contenido, bg=T("BG"))
        fb.pack(fill="x", padx=24, pady=4)
        boton(fb, "+ Agregar Plan",        self._agregar_plan).pack(side="left", padx=4)
        boton(fb, "✅ Activar",             self._activar_plan_sel,
              color=OK, fg="white").pack(side="left", padx=4)
        boton(fb, "⏸ Desactivar",          self._desactivar_plan_sel,
              color="#555", fg="white").pack(side="left", padx=4)
        boton(fb, "🗑 Borrar definitivo",   self._borrar_plan_sel,
              color=ERROR, fg="white").pack(side="left", padx=4)

        self._actualizar_planes()

    def _actualizar_planes(self):
        self.tree_planes.delete(*self.tree_planes.get_children())
        for p in db.get_planes(solo_activos=False):
            estado = "✅ Activo" if p["activo"] else "⏸ Inactivo"
            self.tree_planes.insert("", "end", iid=p["id"],
                values=(p["id"], p["nombre"], f"${p['precio']:.2f}", estado))

    def _agregar_plan(self):
        self._ventana_plan()

    def _editar_plan_sel(self):
        sel = self.tree_planes.selection()
        if not sel:
            return
        planes = {p["id"]: p for p in db.get_planes(solo_activos=False)}
        plan   = planes.get(int(sel[0]))
        if plan:
            self._ventana_plan(plan)

    def _ventana_plan(self, plan=None):
        win = tk.Toplevel(self)
        win.title("Nuevo Plan" if not plan else "Editar Plan")
        win.configure(bg=T("BG"))
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Nombre del plan:", fg=T("TEXT"), bg=T("BG"),
                 font=FONT_SMALL).pack(anchor="w", padx=20, pady=(16, 2))
        var_nombre = tk.StringVar(value=plan["nombre"] if plan else "")
        entrada(win, textvariable=var_nombre, width=36).pack(padx=20, ipady=4)

        tk.Label(win, text="Precio ($):", fg=T("TEXT"), bg=T("BG"),
                 font=FONT_SMALL).pack(anchor="w", padx=20, pady=(10, 2))
        var_precio = tk.StringVar(value=str(plan["precio"]) if plan else "0")
        entrada(win, textvariable=var_precio, width=16).pack(padx=20, ipady=4, anchor="w")

        def guardar():
            nombre = var_nombre.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre no puede estar vacío.", parent=win)
                return
            try:
                precio = float(var_precio.get().replace(",", "."))
            except ValueError:
                messagebox.showerror("Error", "Precio inválido.", parent=win)
                return
            if plan:
                db.editar_plan(plan["id"], nombre, precio)
            else:
                db.agregar_plan(nombre, precio)
            win.destroy()
            self._actualizar_planes()

        fb = tk.Frame(win, bg=T("BG"))
        fb.pack(pady=14, padx=20, fill="x")
        boton(fb, "💾 Guardar", guardar).pack(side="left", padx=4)
        boton(fb, "Cancelar", win.destroy,
              color=T("BTN_CANCEL"), fg=T("BTN_CANCEL_FG")).pack(side="right", padx=4)

    def _activar_plan_sel(self):
        sel = self.tree_planes.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un plan primero.")
            return
        db.activar_plan(int(sel[0]))
        self._actualizar_planes()

    def _desactivar_plan_sel(self):
        sel = self.tree_planes.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un plan primero.")
            return
        if messagebox.askyesno("Desactivar",
                "¿Desactivar este plan?\nNo aparecerá en nuevas altas pero los socios que lo tienen no se ven afectados."):
            db.desactivar_plan(int(sel[0]))
            self._actualizar_planes()

    def _borrar_plan_sel(self):
        sel = self.tree_planes.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un plan primero.")
            return
        plan_id = int(sel[0])
        ok, msg = db.borrar_plan(plan_id)
        if not ok:
            messagebox.showerror("No se puede borrar", msg)
            return
        if messagebox.askyesno("Borrar definitivo",
                "⚠️ Esto borra el plan permanentemente.\n¿Confirmar?"):
            db.borrar_plan_definitivo(plan_id)
            self._actualizar_planes()

    # ══════════════════════════════════════════════════════════════════════════
    # PUERTA
    # ══════════════════════════════════════════════════════════════════════════
    def mostrar_puerta(self):
        self._seccion_actual = self.mostrar_puerta
        self._limpiar()
        self._titulo("🚪 Configuración de Puerta")

        cfg = puerta.cfg
        self._hid_devices = []  # se llena al presionar Detectar

        # ── Estado actual ─────────────────────────────────────────────────────
        fc = tk.Frame(self.contenido, bg=T("CARD_BG"), padx=20, pady=16)
        fc.pack(fill="x", padx=24, pady=8)
        tk.Label(fc, text="Estado del servicio de acceso",
                 font=FONT_BOLD, fg=T("ACENTO"), bg=T("CARD_BG")).pack(anchor="w")
        self.lbl_estado_puerta = tk.Label(
            fc, text="● Activo — escuchando DNI",
            font=FONT_LABEL, fg=OK, bg=T("CARD_BG")
        )
        self.lbl_estado_puerta.pack(anchor="w", pady=4)

        # ── Selección de dispositivo HID ──────────────────────────────────────
        tk.Label(self.contenido, text="Dispositivo Relé USB HID",
                 font=FONT_BOLD, fg=T("TEXT"), bg=T("BG")).pack(anchor="w", padx=24, pady=(12, 4))

        f1 = tk.Frame(self.contenido, bg=T("BG"))
        f1.pack(fill="x", padx=24, pady=4)
        boton(f1, "🔍 Detectar dispositivos", self._detectar_hid,
              color="#3a7bd5", fg="white").pack(side="left", padx=(0, 8))

        saved = cfg.get("device_path", "")
        initial = "✅ Dispositivo configurado — pulsá Detectar para ver detalles" if saved \
                  else "— Pulsá Detectar para buscar el relé —"
        self.var_device = tk.StringVar(value=initial)
        self.combo_device = ttk.Combobox(f1, textvariable=self.var_device,
                                         state="readonly", width=52)
        self.combo_device.pack(side="left")

        # ── Tiempo de apertura ────────────────────────────────────────────────
        f4 = tk.Frame(self.contenido, bg=T("BG"))
        f4.pack(fill="x", padx=24, pady=4)
        tk.Label(f4, text="Tiempo apertura (seg):", fg=T("TEXT"), bg=T("BG"),
                 font=FONT_SMALL, width=20, anchor="w").pack(side="left")
        self.var_tiempo = tk.IntVar(value=cfg.get("tiempo_apertura", 3))
        tk.Spinbox(f4, from_=1, to=10, textvariable=self.var_tiempo,
                   width=4, bg=T("ENTRADA_BG"), fg=T("TEXT"),
                   font=FONT_LABEL, relief="flat",
                   buttonbackground=T("SEP")).pack(side="left")

        # ── Modo simulación ───────────────────────────────────────────────────
        f5 = tk.Frame(self.contenido, bg=T("BG"))
        f5.pack(fill="x", padx=24, pady=4)
        self.var_sim = tk.BooleanVar(value=cfg.get("simulacion", False))
        tk.Checkbutton(f5, text="Modo simulación (sin hardware real)",
                       variable=self.var_sim,
                       bg=T("BG"), fg=T("TEXT"), selectcolor=T("ENTRADA_BG"),
                       activebackground=T("BG"), activeforeground=T("TEXT"),
                       font=FONT_SMALL).pack(side="left")

        # ── Botones de acción ─────────────────────────────────────────────────
        tk.Frame(self.contenido, bg=T("SEP"), height=1).pack(
            fill="x", padx=24, pady=12)

        fb = tk.Frame(self.contenido, bg=T("BG"))
        fb.pack(fill="x", padx=24, pady=4)
        boton(fb, "💾 Guardar configuración", self._guardar_config_puerta
              ).pack(side="left", padx=4)
        boton(fb, "🔌 Test de conexión", self._test_conexion_puerta,
              color="#3a7bd5", fg="white").pack(side="left", padx=4)
        boton(fb, "🚪 Test apertura (2 seg)", self._test_apertura_puerta,
              color="#555", fg="white").pack(side="left", padx=4)

        self.lbl_test = tk.Label(self.contenido, text="",
                                  font=FONT_BOLD, bg=T("BG"))
        self.lbl_test.pack(anchor="w", padx=24, pady=(8, 0))

        # ── Simulación de carteles ─────────────────────────────────────────────
        tk.Frame(self.contenido, bg=T("SEP"), height=1).pack(
            fill="x", padx=24, pady=10)
        tk.Label(self.contenido, text="Simulación de carteles (sin DNI real)",
                 font=FONT_BOLD, fg=T("TEXT"), bg=T("BG")).pack(anchor="w", padx=24, pady=(0, 6))

        fb2 = tk.Frame(self.contenido, bg=T("BG"))
        fb2.pack(fill="x", padx=24, pady=4)
        boton(fb2, "✅ Simular acceso OK",
              lambda: self._simular_cartel("ok"),
              color=OK, fg="white").pack(side="left", padx=4)
        boton(fb2, "❌ Simular cuota vencida",
              lambda: self._simular_cartel("vencida"),
              color=ERROR, fg="white").pack(side="left", padx=4)
        boton(fb2, "⚠️ Simular no encontrado",
              lambda: self._simular_cartel("no_encontrado"),
              color=WARN, fg="white").pack(side="left", padx=4)

        tk.Label(self.contenido,
                 text="Los carteles se muestran en el monitor externo igual que cuando llega un socio.",
                 fg=T("TEXT_DIM"), bg=T("BG"), font=FONT_SMALL).pack(anchor="w", padx=24, pady=(4, 0))

    def _simular_cartel(self, tipo):
        """Dispara el cartel en la ventana de acceso como si llegara un socio real."""
        # Busca la ventana de acceso entre los Toplevel activos
        ventana = None
        try:
            for w in self.winfo_toplevel().winfo_children():
                if hasattr(w, '_estado_ok'):
                    ventana = w
                    break
            # También buscar en el master raíz
            if not ventana:
                root = self.winfo_toplevel().master
                if root:
                    for w in root.winfo_children():
                        if hasattr(w, '_estado_ok'):
                            ventana = w
                            break
        except Exception:
            pass

        if not ventana:
            messagebox.showwarning("Sin pantalla de acceso",
                "No se detectó la ventana de acceso activa.\nAsegurate de que el monitor externo esté conectado y el sistema iniciado.",
                parent=self)
            return

        socio_demo = {"nombre": "Demo", "apellido": "Test"}
        if tipo == "ok":
            ventana._estado_ok(socio_demo)
        elif tipo == "vencida":
            ventana._estado_vencida(socio_demo)
        else:
            ventana._estado_no_encontrado()

    def _detectar_hid(self):
        dispositivos = listar_dispositivos_hid()
        self._hid_devices = dispositivos
        if not dispositivos:
            self.combo_device.configure(values=["— No se encontraron dispositivos HID —"])
            self.combo_device.current(0)
            self.lbl_test.config(text="No se encontraron dispositivos HID.", fg=ERROR)
            return

        def label(d):
            desc = d.get("product_string") or d.get("manufacturer_string") or "Desconocido"
            return f"VID:{d['vendor_id']:#06x}  PID:{d['product_id']:#06x}  —  {desc}"

        labels = [label(d) for d in dispositivos]
        self.combo_device.configure(values=labels)

        # Preseleccionar el dispositivo ya configurado si sigue conectado
        saved = puerta.cfg.get("device_path", "")
        for i, d in enumerate(dispositivos):
            p = d.get("path", b"")
            if isinstance(p, bytes):
                p = p.decode("utf-8", errors="replace")
            if p == saved:
                self.combo_device.current(i)
                self.lbl_test.config(
                    text=f"{len(dispositivos)} dispositivo(s) encontrado(s) — dispositivo guardado preseleccionado.",
                    fg=OK)
                return

        self.combo_device.current(0)
        self.lbl_test.config(
            text=f"{len(dispositivos)} dispositivo(s) encontrado(s) — seleccioná el relé y guardá.",
            fg=WARN)

    def _guardar_config_puerta(self):
        idx = self.combo_device.current()
        if self._hid_devices and 0 <= idx < len(self._hid_devices):
            raw = self._hid_devices[idx].get("path", b"")
            device_path = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        else:
            # No se detectó todavía: conservar el path guardado
            device_path = puerta.cfg.get("device_path", "")

        nueva_cfg = {
            "device_path":    device_path,
            "tiempo_apertura": self.var_tiempo.get(),
            "simulacion":      self.var_sim.get(),
        }
        puerta.actualizar_config(nueva_cfg)
        messagebox.showinfo("Guardado", "Configuración de puerta guardada.")

    def _test_conexion_puerta(self):
        # Aplicar config actual antes de testear
        self._guardar_config_puerta()
        ok, msg = puerta.test_conexion()
        color = OK if ok else ERROR
        self.lbl_test.config(text=msg, fg=color)

    def _test_apertura_puerta(self):
        self._guardar_config_puerta()
        puerta.test_apertura()
        self.lbl_test.config(
            text="Señal de apertura enviada (2 seg). ¿Se abrió la puerta?",
            fg=WARN
        )

    # ══════════════════════════════════════════════════════════════════════════
    # BACKUP
    # ══════════════════════════════════════════════════════════════════════════
    def hacer_backup(self):
        ok, resultado = db.hacer_backup()
        if ok:
            messagebox.showinfo("Backup", f"Backup guardado en:\n{resultado}")
        else:
            messagebox.showerror("Error en Backup", resultado)
        if self._seccion_actual and self._seccion_actual != self.hacer_backup:
            self._seccion_actual()
        else:
            self.mostrar_dashboard()
