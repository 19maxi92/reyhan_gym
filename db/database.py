import sqlite3
import os
import sys
import shutil
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# Al correr como .exe (PyInstaller) __file__ apunta al temp de extracción;
# sys.executable apunta al .exe real. Desde fuente, usamos abspath normal.
if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH    = os.path.join(_BASE, "gym.db")
BACKUP_DIR = "C:/backup_gym"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS planes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            activo INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS socios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dni TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            celular TEXT NOT NULL,
            plan_id INTEGER,
            fecha_nacimiento TEXT,
            email TEXT,
            observaciones TEXT,
            activo INTEGER DEFAULT 1,
            fecha_alta TEXT NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES planes(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id INTEGER NOT NULL,
            fecha_pago TEXT NOT NULL,
            fecha_vencimiento TEXT NOT NULL,
            meses INTEGER DEFAULT 1,
            FOREIGN KEY (socio_id) REFERENCES socios(id)
        )
    """)

    # Planes por defecto si no hay ninguno
    c.execute("SELECT COUNT(*) FROM planes")
    if c.fetchone()[0] == 0:
        planes_default = [
            ("Gym", 0),
            ("Gym + 1 clase Pilates", 0),
            ("Gym + 2 clases Pilates", 0),
            ("Gym + 3 clases Pilates", 0),
        ]
        c.executemany("INSERT INTO planes (nombre, precio) VALUES (?, ?)", planes_default)

    conn.commit()
    conn.close()


def calcular_vencimiento(fecha_pago_str, meses=1):
    """Calcula la fecha de vencimiento sumando meses exactos a la fecha de pago."""
    fecha_pago = datetime.strptime(fecha_pago_str, "%Y-%m-%d").date()
    vencimiento = fecha_pago + relativedelta(months=meses)
    return vencimiento.strftime("%Y-%m-%d")


# ─── SOCIOS ────────────────────────────────────────────────────────────────────

def alta_socio(dni, nombre, apellido, celular, plan_id,
               fecha_nacimiento=None, email=None, observaciones=None):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO socios (dni, nombre, apellido, celular, plan_id,
                fecha_nacimiento, email, observaciones, fecha_alta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (dni, nombre.strip(), apellido.strip(), celular, plan_id,
              fecha_nacimiento, email, observaciones,
              date.today().strftime("%Y-%m-%d")))
        conn.commit()
        return True, "Socio dado de alta correctamente."
    except sqlite3.IntegrityError:
        return False, "Ya existe un socio con ese DNI."
    finally:
        conn.close()


def baja_socio(socio_id):
    conn = get_conn()
    conn.execute("UPDATE socios SET activo = 0 WHERE id = ?", (socio_id,))
    conn.commit()
    conn.close()


def get_socio_inactivo_por_dni(dni):
    conn = get_conn()
    row = conn.execute("""
        SELECT s.*, p.nombre as plan_nombre
        FROM socios s
        LEFT JOIN planes p ON s.plan_id = p.id
        WHERE s.dni = ? AND s.activo = 0
    """, (dni,)).fetchone()
    conn.close()
    return dict(row) if row else None


def reactivar_socio(socio_id, nombre, apellido, celular, plan_id,
                    fecha_nacimiento=None, email=None, observaciones=None):
    conn = get_conn()
    conn.execute("""
        UPDATE socios SET activo=1, nombre=?, apellido=?, celular=?, plan_id=?,
            fecha_nacimiento=?, email=?, observaciones=?
        WHERE id=?
    """, (nombre.strip(), apellido.strip(), celular, plan_id,
          fecha_nacimiento, email, observaciones, socio_id))
    conn.commit()
    conn.close()


def editar_socio(socio_id, nombre, apellido, celular, plan_id,
                 fecha_nacimiento=None, email=None, observaciones=None):
    conn = get_conn()
    conn.execute("""
        UPDATE socios SET nombre=?, apellido=?, celular=?, plan_id=?,
            fecha_nacimiento=?, email=?, observaciones=?
        WHERE id=?
    """, (nombre.strip(), apellido.strip(), celular, plan_id,
          fecha_nacimiento, email, observaciones, socio_id))
    conn.commit()
    conn.close()


def buscar_socios(texto):
    conn = get_conn()
    q = f"%{texto}%"
    rows = conn.execute("""
        SELECT s.*, p.nombre as plan_nombre
        FROM socios s
        LEFT JOIN planes p ON s.plan_id = p.id
        WHERE s.activo = 1 AND (
            s.dni LIKE ? OR s.nombre LIKE ? OR
            s.apellido LIKE ? OR s.celular LIKE ?
        )
        ORDER BY s.apellido, s.nombre
    """, (q, q, q, q)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_socio_por_dni(dni):
    conn = get_conn()
    row = conn.execute("""
        SELECT s.*, p.nombre as plan_nombre
        FROM socios s
        LEFT JOIN planes p ON s.plan_id = p.id
        WHERE s.dni = ? AND s.activo = 1
    """, (dni,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_socio_por_id(socio_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT s.*, p.nombre as plan_nombre
        FROM socios s
        LEFT JOIN planes p ON s.plan_id = p.id
        WHERE s.id = ?
    """, (socio_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── CUOTA / ACCESO ────────────────────────────────────────────────────────────

def cuota_vigente(socio_id):
    """Devuelve True si el socio tiene cuota vigente hoy."""
    hoy = date.today().strftime("%Y-%m-%d")
    conn = get_conn()
    row = conn.execute("""
        SELECT fecha_vencimiento FROM pagos
        WHERE socio_id = ?
        ORDER BY fecha_vencimiento DESC
        LIMIT 1
    """, (socio_id,)).fetchone()
    conn.close()
    if not row:
        return False
    return row["fecha_vencimiento"] >= hoy


def verificar_acceso(dni):
    """
    Retorna: 'ok', 'vencida', 'no_encontrado'
    """
    socio = get_socio_por_dni(dni)
    if not socio:
        return "no_encontrado", None
    if cuota_vigente(socio["id"]):
        return "ok", socio
    return "vencida", socio


# ─── PAGOS ─────────────────────────────────────────────────────────────────────

def registrar_pago(socio_id, fecha_pago=None, meses=1):
    if not fecha_pago:
        fecha_pago = date.today().strftime("%Y-%m-%d")
    vencimiento = calcular_vencimiento(fecha_pago, meses)
    conn = get_conn()
    conn.execute("""
        INSERT INTO pagos (socio_id, fecha_pago, fecha_vencimiento, meses)
        VALUES (?, ?, ?, ?)
    """, (socio_id, fecha_pago, vencimiento, meses))
    conn.commit()
    conn.close()
    return vencimiento


def get_pagos_socio(socio_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM pagos WHERE socio_id = ?
        ORDER BY fecha_pago DESC
    """, (socio_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── PLANES ────────────────────────────────────────────────────────────────────

def get_planes(solo_activos=True):
    conn = get_conn()
    q = "SELECT * FROM planes WHERE activo=1" if solo_activos else "SELECT * FROM planes"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def agregar_plan(nombre, precio):
    conn = get_conn()
    conn.execute("INSERT INTO planes (nombre, precio) VALUES (?, ?)", (nombre, precio))
    conn.commit()
    conn.close()


def editar_plan(plan_id, nombre, precio):
    conn = get_conn()
    conn.execute("UPDATE planes SET nombre=?, precio=? WHERE id=?", (nombre, precio, plan_id))
    conn.commit()
    conn.close()


def activar_plan(plan_id):
    conn = get_conn()
    conn.execute("UPDATE planes SET activo=1 WHERE id=?", (plan_id,))
    conn.commit()
    conn.close()


def desactivar_plan(plan_id):
    conn = get_conn()
    conn.execute("UPDATE planes SET activo=0 WHERE id=?", (plan_id,))
    conn.commit()
    conn.close()


def borrar_plan(plan_id):
    conn = get_conn()
    count = conn.execute(
        "SELECT COUNT(*) FROM socios WHERE plan_id=? AND activo=1", (plan_id,)
    ).fetchone()[0]
    conn.close()
    if count > 0:
        msg = f"No se puede borrar: {count} socio(s) tienen este plan asignado. Desactivalo en su lugar."
        return False, msg
    return True, ""


def borrar_plan_definitivo(plan_id):
    conn = get_conn()
    conn.execute("DELETE FROM planes WHERE id=?", (plan_id,))
    conn.commit()
    conn.close()


# ─── DASHBOARD ─────────────────────────────────────────────────────────────────

def get_dashboard():
    hoy = date.today()
    hoy_str = hoy.strftime("%Y-%m-%d")
    en_7_dias = (hoy + relativedelta(days=7)).strftime("%Y-%m-%d")
    mes_actual = hoy.strftime("%m")

    conn = get_conn()

    total_activos = conn.execute(
        "SELECT COUNT(*) FROM socios WHERE activo=1"
    ).fetchone()[0]

    # Socios con cuota vencida (nunca pagaron o último vencimiento < hoy)
    vencidos = conn.execute("""
        SELECT COUNT(*) FROM socios s
        WHERE s.activo=1 AND (
            NOT EXISTS (SELECT 1 FROM pagos p WHERE p.socio_id = s.id)
            OR (
                SELECT MAX(fecha_vencimiento) FROM pagos p WHERE p.socio_id = s.id
            ) < ?
        )
    """, (hoy_str,)).fetchone()[0]

    # Socios que vencen en los próximos 7 días
    proximos = conn.execute("""
        SELECT s.nombre, s.apellido, s.celular, p.fecha_vencimiento
        FROM socios s
        JOIN pagos p ON p.socio_id = s.id
        WHERE s.activo=1 AND p.fecha_vencimiento BETWEEN ? AND ?
        AND p.fecha_vencimiento = (
            SELECT MAX(fecha_vencimiento) FROM pagos WHERE socio_id = s.id
        )
        ORDER BY p.fecha_vencimiento
    """, (hoy_str, en_7_dias)).fetchall()

    # Cumpleaños del mes
    cumples = conn.execute("""
        SELECT nombre, apellido, celular, fecha_nacimiento
        FROM socios
        WHERE activo=1 AND fecha_nacimiento IS NOT NULL
        AND strftime('%m', fecha_nacimiento) = ?
        ORDER BY strftime('%d', fecha_nacimiento)
    """, (mes_actual,)).fetchall()

    conn.close()

    return {
        "total_activos": total_activos,
        "vencidos": vencidos,
        "proximos_a_vencer": [dict(r) for r in proximos],
        "cumples_mes": [dict(r) for r in cumples],
    }


# ─── BACKUP ────────────────────────────────────────────────────────────────────

def hacer_backup():
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = os.path.join(BACKUP_DIR, f"gym_backup_{fecha}.db")
        shutil.copy2(DB_PATH, destino)
        return True, destino
    except Exception as e:
        return False, str(e)
