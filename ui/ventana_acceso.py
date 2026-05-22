"""
Ventana de acceso — Monitor externo.
Ocupa toda la pantalla del monitor secundario.
El teclado numérico escribe directamente en el campo DNI.
No tiene botones ni nada que tocar; todo es automático.
"""

import tkinter as tk
import threading
import time
import sys
import os

# Estado compartido: el dashboard lee esto para mostrar el último acceso
ultimo_acceso = {"tipo": None, "nombre": "", "dni": "", "ts": 0}

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import verificar_acceso
from core.puerta import puerta

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ─── COLORES ───────────────────────────────────────────────────────────────────
COLOR_FONDO       = "#0d0d0d"
COLOR_TEXTO       = "#ffffff"
COLOR_ACENTO      = "#f4812e"       # naranja Reyhan exacto
COLOR_OK          = "#2ecc71"
COLOR_ERROR       = "#e74c3c"
COLOR_WARN        = "#f4812e"
COLOR_INPUT_BG    = "#1a1a1a"
COLOR_INPUT_BORDE = "#333333"

TIEMPO_MENSAJE = 5500  # ms que se muestra el cartel antes de volver al estado inicial


class VentanaAcceso(tk.Toplevel):
    def __init__(self, master, monitor_x=0, monitor_y=0,
                 monitor_w=1920, monitor_h=1080):
        super().__init__(master)
        self.master = master
        self._timer = None

        # ── Configuración de ventana ──────────────────────────────────────────
        self.overrideredirect(True)          # sin bordes
        self.geometry(f"{monitor_w}x{monitor_h}+{monitor_x}+{monitor_y}")
        self.configure(bg=COLOR_FONDO)
        self.resizable(False, False)

        # Bloquear Alt+F4 y clicks fuera
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self._build_ui(monitor_w, monitor_h)
        self._estado_espera()

        # Capturar teclas del numpad directamente en el Entry (no en el Toplevel)
        # para que return "break" bloquee el procesamiento nativo antes de que inserte
        self.after(100, self._tomar_foco)

    # ─── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self, w, h):
        # Fondo principal
        self.canvas = tk.Canvas(self, bg=COLOR_FONDO, highlightthickness=0)
        self.canvas.place(x=0, y=0, width=w, height=h)

        # Logo / nombre gimnasio
        logo_path = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "icon", "reyhan_icon.png")
        self._logo_img = None
        if PIL_OK and os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path).convert("RGBA")
                # Escalar manteniendo aspecto, max 200px ancho
                ratio = min(200 / pil_img.width, 90 / pil_img.height)
                nw, nh = int(pil_img.width * ratio), int(pil_img.height * ratio)
                pil_img = pil_img.resize((nw, nh), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(pil_img)
            except Exception:
                self._logo_img = None

        if self._logo_img:
            self.lbl_gym = tk.Label(self, image=self._logo_img, bg=COLOR_FONDO)
        else:
            self.lbl_gym = tk.Label(
                self, text="REYHAN", font=("Georgia", 32, "bold"),
                fg=COLOR_ACENTO, bg=COLOR_FONDO
            )
        self.lbl_gym.place(relx=0.5, rely=0.10, anchor="center")

        self.lbl_sep = tk.Label(
            self, text="─────────────────────",
            fg=COLOR_ACENTO, bg=COLOR_FONDO, font=("Courier", 12)
        )
        self.lbl_sep.place(relx=0.5, rely=0.17, anchor="center")

        # Instrucción
        self.lbl_instruccion = tk.Label(
            self, text="Ingresá tu DNI",
            font=("Georgia", 20), fg="#aaaaaa", bg=COLOR_FONDO
        )
        self.lbl_instruccion.place(relx=0.5, rely=0.26, anchor="center")

        # Campo DNI
        self.var_dni = tk.StringVar()
        self.entry_dni = tk.Entry(
            self, textvariable=self.var_dni,
            font=("Courier New", 44, "bold"),
            fg=COLOR_ACENTO, bg=COLOR_INPUT_BG,
            insertbackground=COLOR_ACENTO,
            relief="flat", justify="center",
            highlightthickness=2,
            highlightcolor=COLOR_ACENTO,
            highlightbackground=COLOR_INPUT_BORDE,
            width=12
        )
        self.entry_dni.place(relx=0.5, rely=0.38, anchor="center",
                             width=480, height=80)
        self.entry_dni.bind("<Key>", self._on_key)

        # Área de mensaje (ok / error) — posición relativa más arriba
        self.frame_msg = tk.Frame(self, bg=COLOR_FONDO)
        self.frame_msg.place(relx=0.5, rely=0.62, anchor="center",
                             width=700, height=220)

        self.lbl_icono = tk.Label(
            self.frame_msg, text="", font=("Segoe UI Emoji", 52),
            bg=COLOR_FONDO
        )
        self.lbl_icono.pack()

        self.lbl_msg = tk.Label(
            self.frame_msg, text="",
            font=("Georgia", 24, "bold"),
            bg=COLOR_FONDO, wraplength=650, justify="center"
        )
        self.lbl_msg.pack()

        self.lbl_submsg = tk.Label(
            self.frame_msg, text="",
            font=("Georgia", 14),
            bg=COLOR_FONDO, wraplength=600, justify="center"
        )
        self.lbl_submsg.pack(pady=(4, 0))

    # ─── ESTADOS ──────────────────────────────────────────────────────────────

    def _estado_espera(self):
        """Limpia todo y queda esperando DNI."""
        self._cancelar_timer()
        self.var_dni.set("")
        self.lbl_instruccion.config(text="Ingresá tu DNI", fg="#aaaaaa")
        self.lbl_icono.config(text="", fg=COLOR_FONDO)
        self.lbl_msg.config(text="", fg=COLOR_FONDO)
        self.lbl_submsg.config(text="", fg=COLOR_FONDO)
        self.entry_dni.config(
            fg=COLOR_ACENTO,
            highlightbackground=COLOR_INPUT_BORDE
        )
        self._tomar_foco()

    def _estado_ok(self, socio):
        self.var_dni.set("")  # limpiar ya para evitar re-procesamiento
        nombre = f"{socio['nombre']} {socio['apellido']}"
        self.lbl_instruccion.config(text="¡Bienvenido!", fg=COLOR_OK)
        self.lbl_icono.config(text="✅", fg=COLOR_OK)
        self.lbl_msg.config(text=nombre, fg=COLOR_OK)
        self.lbl_submsg.config(text="Acceso habilitado", fg="#aaaaaa")
        self.entry_dni.config(fg=COLOR_OK, highlightbackground=COLOR_OK)
        threading.Thread(target=puerta.abrir, daemon=True).start()
        self._volver_en(TIEMPO_MENSAJE)

    def _estado_vencida(self, socio):
        self.var_dni.set("")
        nombre = f"{socio['nombre']} {socio['apellido']}"
        self.lbl_instruccion.config(text="Cuota vencida", fg=COLOR_ERROR)
        self.lbl_icono.config(text="❌", fg=COLOR_ERROR)
        self.lbl_msg.config(text=nombre, fg=COLOR_ERROR)
        self.lbl_submsg.config(
            text="Tu cuota está vencida.\nAcercate a recepción para renovar.",
            fg="#aaaaaa"
        )
        self.entry_dni.config(fg=COLOR_ERROR, highlightbackground=COLOR_ERROR)
        self._volver_en(TIEMPO_MENSAJE)

    def _estado_no_encontrado(self):
        self.var_dni.set("")
        self.lbl_instruccion.config(text="Socio no encontrado", fg=COLOR_WARN)
        self.lbl_icono.config(text="⚠️", fg=COLOR_WARN)
        self.lbl_msg.config(text="DNI no registrado", fg=COLOR_WARN)
        self.lbl_submsg.config(
            text="Acercate a recepción para darte de alta.",
            fg="#aaaaaa"
        )
        self.entry_dni.config(fg=COLOR_WARN, highlightbackground=COLOR_WARN)
        self._volver_en(TIEMPO_MENSAJE)

    # ─── INPUT ────────────────────────────────────────────────────────────────

    def _on_key(self, event):
        """Captura teclas del numpad y procesa el DNI al presionar Enter."""
        # Solo dígitos y Enter/KP_Enter
        if event.keysym in ("Return", "KP_Enter"):
            self._procesar_dni()
            return "break"
        elif event.keysym == "BackSpace":
            actual = self.var_dni.get()
            self.var_dni.set(actual[:-1])
            return "break"
        elif event.char and event.char.isdigit():
            actual = self.var_dni.get()
            if len(actual) < 10:  # DNI máximo 8 dígitos + margen
                self.var_dni.set(actual + event.char)
            return "break"

    def _procesar_dni(self):
        dni = self.var_dni.get().strip()
        if not dni:
            return
        resultado, socio = verificar_acceso(dni)
        nombre = f"{socio['nombre']} {socio['apellido']}" if socio else ""
        ultimo_acceso["tipo"]   = resultado
        ultimo_acceso["nombre"] = nombre
        ultimo_acceso["dni"]    = dni
        ultimo_acceso["ts"]     = time.time()
        if resultado == "ok":
            self._estado_ok(socio)
        elif resultado == "vencida":
            self._estado_vencida(socio)
        else:
            self._estado_no_encontrado()

    # ─── UTILS ────────────────────────────────────────────────────────────────

    def _tomar_foco(self):
        try:
            self.focus_force()
            self.entry_dni.focus_set()
        except Exception:
            pass

    def _volver_en(self, ms):
        self._cancelar_timer()
        self._timer = self.after(ms, self._estado_espera)

    def _cancelar_timer(self):
        if self._timer:
            try:
                self.after_cancel(self._timer)
            except Exception:
                pass
            self._timer = None
