# Bitácora interna — Reyhan Gym

Registro de cambios, archivos tocados y "cosas que conviene saber" del sistema.
Uso interno. Se actualiza con cada cambio relevante (lo más nuevo arriba).

**Cómo buscar:** Ctrl+F por nombre de archivo, pantalla (`pantalla DNI`, `Socios`,
`Pagos`, `Puerta`), tema (`relé`, `notas`, `vencimiento`, `backup`) o hash de commit.

---

## ✅ CHECKLIST ANTES DE CODEAR (cuando Maxi dice "leé la bitácora")

**1. Ramas y `main`**
- `git fetch --all` y revisar si hay ramas `claude/*` con cambios que NO están en `main`:
  `git log --oneline origin/main..origin/<rama>`.
- Si hay cambios sin mergear: **avisar a Maxi antes de tocar nada**.
- Arrancar la rama de trabajo desde el `main` actualizado (o mergear `main` en la rama).
- **`main` es la versión buena.** Al terminar: PR → merge a `main` → se arma el `.exe` desde ahí.

**2. Antes de tocar un archivo**
- Son pocos archivos (ver índice). Casi todo está en `ui/panel_admin.py` (panel) y
  `ui/ventana_acceso.py` (pantalla del DNI).
- Ver el historial del archivo: `git log --oneline -5 -- <archivo>`.
- **La pantalla del DNI la ve cualquiera que entra al gym** (monitor externo).
  No mostrar ahí datos privados (notas, deudas, celular).

**3. Base de datos (`gym.db`, SQLite)**
- La base real vive en la notebook del gym, al lado del `.exe`. **No está en el repo**
  (`.gitignore`) y no se reemplaza al actualizar: solo se cambia el `.exe`.
- Columnas nuevas: hay que agregarlas con "self-healing" en `init_db()`
  (`ALTER TABLE ... ADD COLUMN` dentro de try/except), porque las bases que ya existen
  no se recrean. `CREATE TABLE IF NOT EXISTS` no agrega columnas a una tabla vieja.
- Fechas guardadas como texto `AAAA-MM-DD` (se comparan como string, funciona por el formato).

**4. Cómo se entrega (no se "despliega solo")**
- En una PC con Windows + Python: `build.bat` → genera `dist\SistemaReyhan.exe`.
- Copiar el `.exe` a la notebook del gym reemplazando el anterior (cerrar el sistema antes).
  `gym.db`, `config_puerta.json` y los logos quedan como están.
- Antes de reemplazar conviene un **Backup** desde el sidebar (va a `C:\backup_gym\`).

**5. Probar antes de entregar**
- `python -m py_compile` de cada archivo tocado.
- Prueba visual en Linux: necesita `tkinter` (acá anda con `python3.12`) + `xvfb-run`.
  Copiar el proyecto a una carpeta temporal (para no crear `gym.db` en el repo), cargar
  socios de prueba con `db.alta_socio` / `db.registrar_pago` y sacar capturas con
  `PIL.ImageGrab`. La puerta sin hardware cae sola en modo simulado.
- Decirle a Maxi qué se probó y qué no (lo que no se puede probar acá: relé real,
  dos monitores reales, Windows).

**6. Al terminar**
- Anotar el cambio en el Historial de esta bitácora (pedido, solución, archivos, probado, ojo).
- Commit + push + PR a `main`, y avisarle a Maxi que hay que rearmar el `.exe`.

---

## Índice rápido de archivos

| Archivo | Para qué sirve |
|---|---|
| `main.py` | Arranque: crea la base, hace backup, cierra el relé, detecta monitores y abre las dos ventanas. |
| `db/database.py` | Todo SQLite: socios, pagos, planes, dashboard, backup. `verificar_acceso()` decide si abre. |
| `ui/ventana_acceso.py` | **Pantalla del DNI** (monitor externo, pantalla completa). Carteles OK / vencida / no encontrado + vencimiento. |
| `ui/panel_admin.py` | Panel de la notebook: Dashboard, Socios, Pagos, Planes, Puerta, Backup, tema claro/oscuro. |
| `core/puerta.py` | Relé USB **HID** de la puerta magnética (`hidapi`). Config en `config_puerta.json`. |
| `relay_test.py` | Utilidad suelta para probar el relé. |
| `build.bat` | Genera el `.exe` con PyInstaller. |
| `icon/` | Íconos. Logos opcionales: `logo_dark.(jpeg/jpg/png)` para la pantalla DNI. |

**Tablas:** `socios` (con `observaciones` = notas rápidas), `pagos` (`fecha_vencimiento`
calculada por mes exacto), `planes`.

---

## Cosas que conviene saber (lecciones aprendidas)

- **Cuota al día = último vencimiento >= hoy.** El día del vencimiento todavía entra;
  al día siguiente ya no. Se usa el vencimiento más lejano (`MAX`), no el último pago cargado.
- **La puerta es HID, no puerto COM.** El README todavía habla de COM/pyserial/baudrate
  (quedó viejo). Se configura por **VID+PID** (estable entre reinicios); el `device_path`
  es solo respaldo porque cambia al reconectar el USB (ver 13/07).
- **El relé se cierra al arrancar** y `abrir()` reintenta cerrar hasta 3 veces: antes
  quedaba abierto y parecía que una cuota vencida abría la puerta.
- **DNI duplicado / loop de apertura:** las teclas se capturan en el `Entry` (no en la
  ventana) con `return "break"`, y el campo se limpia apenas se procesa. No volver a
  bindear en el `Toplevel`.
- **Rutas con el `.exe`:** `gym.db` y `config_puerta.json` van al lado de `sys.executable`
  cuando corre empaquetado (`sys.frozen`). No usar rutas relativas al `__file__` para datos.
- **Reactivar un socio dado de baja borra sus pagos viejos** (a propósito, 27/05) para que
  no entre con un vencimiento anterior.
- **Panel y pantalla DNI corren en el mismo proceso.** El "último acceso" se comparte por el
  dict `ultimo_acceso` de `ventana_acceso.py`; los botones de simular cartel del panel llaman
  directo a `_estado_ok` / `_estado_vencida` de la ventana.
- **Notas del socio = columna `observaciones`.** Es el mismo campo del formulario de
  edición (ahí se llama "Notas"). No crear otra columna para lo mismo.

---

## Historial de cambios

### 2026-10-08 — Pantalla DNI muestra el vencimiento + notas rápidas por socio
rama `claude/youthful-mendel-ngjxmr`
- **Pedido 1:** que en la pantalla donde la gente pone el DNI aparezca "tu cuota vence tal día",
  para que los socios tengan el control.
  - Después del cartel de OK sale grande: **"Tu cuota vence el DD/MM/AAAA"** (blanco).
    Si faltan 5 días o menos sale en naranja: "faltan N días" / "vence MAÑANA" / "vence HOY".
  - Cuota vencida: en rojo **"Tu cuota venció el DD/MM/AAAA"**. Si nunca pagó, no muestra fecha.
  - `verificar_acceso()` ahora devuelve el socio con `vencimiento`. Nueva
    `get_ultimo_vencimiento()`; `cuota_vigente()` la usa (misma lógica que antes).
  - Los botones de "simular cartel" (sección Puerta) muestran una fecha de ejemplo.
- **Pedido 2:** al lado de cada socio, un botón/box chico para anotar cosas cortas y que se vean
  ("debe 2500", "se le deben 5000").
  - Socios: nueva columna **📝 Notas** a la derecha. Las filas con nota se ven en **naranja**.
  - Para anotar: **doble click en la columna 📝 Notas**, o seleccionar el socio y botón
    **📝 Notas**. Abre una ventanita con Guardar (o Ctrl+Enter) / Borrar nota / Cancelar.
  - También se ve en **Pagos** (columna + la nota en naranja dentro de la ventana de cobro).
  - El buscador también busca en las notas (ej. escribir "debe" lista a todos los que deben).
  - Usa la columna existente `observaciones` (nueva `set_observaciones()`); en el formulario
    de edición el campo pasó a llamarse "Notas". **No se muestra en la pantalla del DNI.**
- **Archivos:** `db/database.py`, `ui/ventana_acceso.py`, `ui/panel_admin.py`, `BITACORA.md` (nueva).
- **Probado** (Linux + Xvfb, base de prueba): carteles con vence en 26 días / faltan 2 días /
  venció ayer / nunca pagó / DNI inexistente; nota nueva desde la ventanita y guardada en la base;
  filas en naranja; búsqueda "debe" → 3 socios; columna en Pagos.
  **No probado:** Windows, dos monitores reales, relé real.
- **Ojo:** hay que rearmar el `.exe` con `build.bat`. No hace falta tocar la base.

### 2026-07-13 — Puerta: config por VID+PID y fix relé que quedaba abierto
`c49b38c`, `4fd17c5` · PR #8
- Guarda VID+PID en `config_puerta.json`; `_conectar()` prueba VID+PID y usa el path de respaldo.
- `abrir()` reintenta cerrar hasta 3 veces; `cerrar()` al iniciar el sistema.
- Mejores textos de la sección Puerta.
- **Archivos:** `core/puerta.py`, `main.py`, `ui/panel_admin.py`.

### 2026-05-27 — Logos, validaciones, último acceso, reactivar socio
`fe89429`, `e50a478`, `c31a4b9`, `26729b9`, `48dce98`, `c5f5362`, `24e733d`, `d609969` · PRs #6 y #7
- Logos en sidebar y pantalla DNI (`.jpeg`, `.jpg` o `.png`), más grandes.
- Validaciones en alta de socio (DNI 5–9 dígitos, celular, fechas, email) y en pagos (1–12 meses).
- Card "último acceso" en el dashboard + último acceso en el header del panel.
- Alta con DNI de un socio dado de baja → ofrece reactivarlo y **borra sus pagos viejos**.
- Click en un campo de fecha selecciona todo para editar más rápido.

### 2026-05-26 — Fecha de pago en el alta de socio
`868e5e5` · PR #5
- Al dar de alta se puede elegir la fecha del primer pago (por defecto hoy).

### 2026-05-22 — Config puerta, mini monitor, CSV, pago al alta, botón Activar Monitor
`253e835`, `820e503` · PRs #3 y #4
- Sección Puerta configurable desde el panel; exportar socios a CSV; registrar pago al dar de alta.
- Botón **Activar Monitor** en el sidebar: devuelve el foco al campo DNI de la pantalla externa.

### 2026-05-18 — Arranque del sistema y primeros arreglos
`0a57e7f` … `111f5f4` · PRs #1 y #2
- Subida inicial, README, integridad de archivos.
- Puerta pasa a relé HID (`hidapi`, `send_feature_report`).
- Fix DNI duplicado (binding en el `Entry`) y loop de apertura (limpiar el campo al procesar).
- `gym.db` al lado del `.exe` (`sys.frozen`). `build.bat` con `python -m pip` / `python -m PyInstaller`.

---

## Pendientes / ideas

- README desactualizado en la parte de la puerta (habla de COM/pyserial; hoy es HID por VID+PID).

---

## Plantilla para nuevas entradas

```
### AAAA-MM-DD — Título corto
`hash` · rama `...`
- Pedido:
- Solución:
- Archivos:
- Probado / no probado:
- Ojo con:
```
