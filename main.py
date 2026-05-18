"""
main.py — Punto de entrada del Sistema de Gimnasio.

Al iniciar:
  1. Inicializa la base de datos.
  2. Detecta si hay un segundo monitor conectado.
  3. Lanza la ventana de acceso en el monitor externo (pantalla completa, sin bordes).
  4. Lanza el panel de administración en la notebook.
  5. Hace backup automático al arrancar.
"""

import tkinter as tk
import sys
import os

# Asegurarse de que los imports internos funcionen desde el .exe
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import db.database as db
from ui.panel_admin import PanelAdmin
from ui.ventana_acceso import VentanaAcceso


def detectar_monitores(root):
    """
    Devuelve la geometría del monitor principal y del secundario (si existe).
    Tkinter expone la resolución total del escritorio virtual; si hay dos
    monitores de 1920x1080, el escritorio mide 3840x1080 (extendido horizontal).
    """
    ancho_total = root.winfo_screenwidth()
    alto_total  = root.winfo_screenheight()

    # Monitor principal: asumimos que la notebook está a la izquierda
    # Monitor secundario: el resto a la derecha
    # En W10 LTSC con "Extender pantallas" el monitor principal suele ser
    # el izquierdo (offset 0,0). El secundario empieza donde termina el primero.

    # Intentamos obtener info más precisa con screeninfo si está instalado
    try:
        from screeninfo import get_monitors
        monitores = get_monitors()
        if len(monitores) >= 2:
            m0 = monitores[0]  # notebook
            m1 = monitores[1]  # externo
            return (
                (m0.x, m0.y, m0.width, m0.height),
                (m1.x, m1.y, m1.width, m1.height),
            )
        else:
            m0 = monitores[0]
            return (
                (m0.x, m0.y, m0.width, m0.height),
                None
            )
    except ImportError:
        pass

    # Fallback: si el escritorio es más ancho que alto, asumimos dos monitores
    # de igual resolución lado a lado
    if ancho_total > alto_total * 1.5:
        ancho_uno = ancho_total // 2
        return (
            (0,         0, ancho_uno,  alto_total),
            (ancho_uno, 0, ancho_uno,  alto_total),
        )
    else:
        # Un solo monitor
        return (
            (0, 0, ancho_total, alto_total),
            None
        )


def main():
    # ── Inicializar BD ────────────────────────────────────────────────────────
    db.init_db()

    # ── Backup automático al inicio ───────────────────────────────────────────
    db.hacer_backup()

    # ── Ventana raíz (oculta, solo para Tkinter) ──────────────────────────────
    root = tk.Tk()
    root.withdraw()  # ocultar la raíz, todo se maneja en Toplevel

    # ── Detectar monitores ────────────────────────────────────────────────────
    mon_notebook, mon_externo = detectar_monitores(root)

    # ── Ventana de acceso (monitor externo) ───────────────────────────────────
    if mon_externo:
        mx, my, mw, mh = mon_externo
    else:
        # Si hay un solo monitor, la ventana de acceso va a la mitad derecha
        mx, my, mw, mh = mon_notebook
        mw_mitad = mw // 2
        mx = mw_mitad
        mw = mw_mitad

    ventana_acceso = VentanaAcceso(root, monitor_x=mx, monitor_y=my,
                                   monitor_w=mw, monitor_h=mh)

    # ── Panel de administración (notebook) ────────────────────────────────────
    win_admin = tk.Toplevel(root)
    win_admin.title("Sistema Gym — Administración")
    win_admin.configure(bg="#1c1c1e")

    if mon_externo:
        nx, ny, nw, nh = mon_notebook
        win_admin.geometry(f"{nw}x{nh}+{nx}+{ny}")
    else:
        # Mitad izquierda si es un solo monitor
        nw = mon_notebook[2] // 2
        win_admin.geometry(f"{nw}x{mon_notebook[3]}+0+0")

    win_admin.state("zoomed")  # maximizar en W10

    # Cerrar todo si se cierra el admin
    def on_cerrar():
        root.quit()
        root.destroy()

    win_admin.protocol("WM_DELETE_WINDOW", on_cerrar)

    PanelAdmin(win_admin)

    # ── Loop principal ────────────────────────────────────────────────────────
    root.mainloop()


if __name__ == "__main__":
    main()
