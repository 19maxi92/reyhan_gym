"""
core/puerta.py — Control del relé USB-Serial para la puerta magnética.
La configuración (puerto COM, comando) se guarda en config_puerta.json
junto al ejecutable, para que persista entre reinicios.
"""

import threading
import time
import json
import os

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# ─── CONFIG ────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config_puerta.json")

TIEMPO_APERTURA = 3  # segundos

# Comandos más comunes (índice guardado en config)
COMANDOS_DISPONIBLES = [
    ("Genérico A  [A0 01 01 A2]",  bytes([0xA0, 0x01, 0x01, 0xA2]), bytes([0xA0, 0x01, 0x00, 0xA1])),
    ("Genérico B  [FF 01 01]",     bytes([0xFF, 0x01, 0x01]),        bytes([0xFF, 0x01, 0x00])),
    ("Simple byte [01 / 00]",      bytes([0x01]),                    bytes([0x00])),
]

CONFIG_DEFAULT = {
    "puerto":          "COM3",
    "baudrate":        9600,
    "comando_idx":     0,
    "tiempo_apertura": TIEMPO_APERTURA,
    "simulacion":      False,
}


def cargar_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            # Rellenar claves faltantes con defaults
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


def listar_puertos():
    """Devuelve lista de strings de puertos COM disponibles."""
    if not SERIAL_AVAILABLE:
        return []
    try:
        return [p.device for p in serial.tools.list_ports.comports()]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
class ControlPuerta:
    def __init__(self):
        self.cfg  = cargar_config()
        self._lock = threading.Lock()

    def _cmd_abrir(self):
        idx = self.cfg.get("comando_idx", 0)
        return COMANDOS_DISPONIBLES[idx][1]

    def _cmd_cerrar(self):
        idx = self.cfg.get("comando_idx", 0)
        return COMANDOS_DISPONIBLES[idx][2]

    def _conectar(self):
        if not SERIAL_AVAILABLE or self.cfg.get("simulacion"):
            return None
        try:
            return serial.Serial(
                self.cfg["puerto"],
                self.cfg.get("baudrate", 9600),
                timeout=1
            )
        except Exception as e:
            print(f"[PUERTA] Error de conexión: {e}")
            return None

    def abrir(self, segundos=None):
        """Abre la puerta y la cierra automáticamente."""
        t = segundos or self.cfg.get("tiempo_apertura", TIEMPO_APERTURA)

        def _ciclo():
            with self._lock:
                if self.cfg.get("simulacion") or not SERIAL_AVAILABLE:
                    print(f"[PUERTA SIMULADA] Abierta {t}s")
                    time.sleep(t)
                    print("[PUERTA SIMULADA] Cerrada")
                    return
                conn = self._conectar()
                if not conn:
                    return
                try:
                    conn.write(self._cmd_abrir())
                    time.sleep(t)
                    conn.write(self._cmd_cerrar())
                except Exception as e:
                    print(f"[PUERTA] Error en ciclo: {e}")
                finally:
                    conn.close()

        threading.Thread(target=_ciclo, daemon=True).start()

    def test_conexion(self):
        """
        Intenta abrir y cerrar el puerto.
        Retorna (ok: bool, mensaje: str)
        """
        if self.cfg.get("simulacion") or not SERIAL_AVAILABLE:
            return True, "Modo simulación activo — sin hardware real."
        try:
            conn = serial.Serial(
                self.cfg["puerto"],
                self.cfg.get("baudrate", 9600),
                timeout=1
            )
            conn.close()
            return True, f"✅ Puerto {self.cfg['puerto']} detectado correctamente."
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
