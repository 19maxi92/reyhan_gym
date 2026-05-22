"""
core/puerta.py — Control del relé USB HID para la puerta magnética.
La configuración se guarda en config_puerta.json junto al ejecutable.
"""

import threading
import time
import json
import os
import sys

try:
    import hid
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(BASE_DIR, "config_puerta.json")

TIEMPO_APERTURA = 3

# Comandos HID relay estándar (9 bytes: report_id + cmd + relay_num + padding)
CMD_ABRIR  = bytes([0x00, 0xFF, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_CERRAR = bytes([0x00, 0xFD, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

CONFIG_DEFAULT = {
    "device_path":    "",
    "tiempo_apertura": TIEMPO_APERTURA,
    "simulacion":     False,
}


def cargar_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            for k, v in CONFIG_DEFAULT.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return CONFIG_DEFAULT.copy()


def guardar_config(cfg):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception as e:
        print(f"[CONFIG] Error al guardar: {e}")
        return False


def listar_dispositivos_hid():
    """Devuelve lista de dicts con todos los dispositivos HID conectados."""
    if not HID_AVAILABLE:
        return []
    try:
        return hid.enumerate()
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
class ControlPuerta:
    def __init__(self):
        self.cfg   = cargar_config()
        self._lock = threading.Lock()

    def _path_bytes(self):
        p = self.cfg.get("device_path", "")
        if isinstance(p, bytes):
            return p
        return p.encode("utf-8") if p else b""

    def _conectar(self):
        if not HID_AVAILABLE or self.cfg.get("simulacion"):
            return None
        path = self._path_bytes()
        if not path:
            print("[PUERTA] No hay dispositivo configurado.")
            return None
        try:
            d = hid.device()
            d.open_path(path)
            return d
        except Exception as e:
            print(f"[PUERTA] Error de conexión: {e}")
            return None

    def abrir(self, segundos=None):
        """Abre la puerta y la cierra automáticamente."""
        t = segundos or self.cfg.get("tiempo_apertura", TIEMPO_APERTURA)

        def _ciclo():
            with self._lock:
                if self.cfg.get("simulacion") or not HID_AVAILABLE:
                    print(f"[PUERTA SIMULADA] Abierta {t}s")
                    time.sleep(t)
                    print("[PUERTA SIMULADA] Cerrada")
                    return
                conn = self._conectar()
                if not conn:
                    return
                try:
                    conn.send_feature_report(CMD_ABRIR)
                    time.sleep(t)
                    conn.send_feature_report(CMD_CERRAR)
                except Exception as e:
                    print(f"[PUERTA] Error en ciclo: {e}")
                finally:
                    conn.close()

        threading.Thread(target=_ciclo, daemon=True).start()

    def test_conexion(self):
        """Retorna (ok: bool, mensaje: str)."""
        if self.cfg.get("simulacion") or not HID_AVAILABLE:
            return True, "Modo simulación activo — sin hardware real."
        path = self._path_bytes()
        if not path:
            return False, "❌ No hay dispositivo configurado. Usá Detectar y guardá."
        try:
            d = hid.device()
            d.open_path(path)
            d.close()
            return True, "✅ Dispositivo HID detectado correctamente."
        except Exception as e:
            return False, f"❌ {e}"

    def test_apertura(self):
        """Abre la puerta 1 vez para verificar que el comando funciona."""
        self.abrir(segundos=2)

    def actualizar_config(self, nueva_cfg):
        self.cfg = nueva_cfg
        guardar_config(nueva_cfg)

    def recargar_config(self):
        self.cfg = cargar_config()


# Instancia global compartida por todo el sistema
puerta = ControlPuerta()
