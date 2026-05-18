"""
relay_test.py — Script para detectar el comando correcto del relé USB.
Ejecutar SOLO con el relé conectado, desde la notebook del gimnasio.
No forma parte del sistema principal.
"""

import sys
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: pyserial no instalado. Ejecutar: pip install pyserial")
    sys.exit(1)

# Comandos más comunes para relés USB genéricos chinos
COMANDOS = {
    "Generico A (abrir)":   bytes([0xA0, 0x01, 0x01, 0xA2]),
    "Generico A (cerrar)":  bytes([0xA0, 0x01, 0x00, 0xA1]),
    "Generico B (abrir)":   bytes([0xFF, 0x01, 0x01]),
    "Generico B (cerrar)":  bytes([0xFF, 0x01, 0x00]),
    "CH340 (abrir)":        bytes([0xA0, 0x01, 0x01, 0xA2]),
    "CH340 (cerrar)":       bytes([0xA0, 0x01, 0x00, 0xA1]),
    "Simple 1":             bytes([0x01]),
    "Simple 0":             bytes([0x00]),
}

def listar_puertos():
    print("\n=== Puertos COM disponibles ===")
    puertos = serial.tools.list_ports.comports()
    if not puertos:
        print("  No se encontraron puertos COM.")
        return []
    for p in puertos:
        print(f"  {p.device} — {p.description}")
    return [p.device for p in puertos]

def test_puerto(puerto, baudrate=9600):
    print(f"\n=== Testeando {puerto} a {baudrate} baud ===")
    try:
        conn = serial.Serial(puerto, baudrate, timeout=1)
        print(f"  Conexión OK en {puerto}")

        for nombre, cmd in COMANDOS.items():
            resp = input(f"\n  Enviar '{nombre}' ({cmd.hex()})? [s/n]: ").lower()
            if resp == "s":
                conn.write(cmd)
                print(f"  Enviado: {cmd.hex()}")
                time.sleep(0.5)

        conn.close()
        print(f"\n  Puerto {puerto} cerrado.")
    except Exception as e:
        print(f"  ERROR: {e}")

if __name__ == "__main__":
    puertos = listar_puertos()
    if not puertos:
        sys.exit(1)

    print("\nIngresa el puerto a testear (ej: COM3):")
    puerto = input("  > ").strip().upper()

    if puerto not in puertos:
        print(f"  Puerto {puerto} no encontrado. Verificar conexión.")
        sys.exit(1)

    test_puerto(puerto)
    print("\nGuardá el índice del comando que funcionó.")
    print("Entrá al Panel Admin → sección Puerta → seleccioná el tipo de comando y guardá.")
