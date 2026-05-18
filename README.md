# Sistema Reyhan — Gestión de Gimnasio

Sistema de escritorio para el control de socios, pagos y acceso automático de puerta en el gimnasio Reyhan Centro de Entrenamiento.

---

## Características

- **Ventana de acceso** en monitor externo: el socio ingresa su DNI desde un teclado numérico y la puerta se abre automáticamente si la cuota está al día.
- **Panel de administración** en la notebook con las secciones:
  - Dashboard con métricas en tiempo real (socios activos, cuotas vencidas, próximos a vencer, cumpleaños del mes)
  - Alta, edición y baja de socios
  - Registro de pagos con cálculo automático de vencimiento
  - Gestión de planes y precios
  - Configuración del relé USB-Serial para la puerta magnética
  - Backup manual de la base de datos
- **Backup automático** al iniciar el sistema (guardado en `C:\backup_gym\`).
- **Modo simulación** para probar el sistema sin hardware conectado.
- **Tema oscuro / claro** toggleable en el panel de administración.

---

## Estructura del proyecto

```
reyhan_gym/
├── main.py               # Punto de entrada — detecta monitores y lanza las ventanas
├── requirements.txt      # Dependencias Python
├── build.bat             # Script para generar el .exe con PyInstaller (Windows)
├── relay_test.py         # Utilidad standalone para detectar el comando correcto del relé
├── db/
│   └── database.py       # SQLite: socios, pagos, planes, dashboard, backup
├── core/
│   └── puerta.py         # Control del relé USB-Serial (apertura/cierre de puerta)
├── ui/
│   ├── ventana_acceso.py # Pantalla del monitor externo (input DNI, resultado de acceso)
│   └── panel_admin.py    # Panel de administración con sidebar y todas las secciones
└── icon/
    ├── reyhan.ico
    ├── reyhan_icon.png
    └── reyhan_icon.svg
```

---

## Requisitos

- Python 3.8 o superior
- Windows 10/11 (el sistema usa `tkinter` y controla puertos COM)
- Relé USB-Serial genérico (CH340 o similar) para la puerta magnética

### Dependencias Python

```
pip install -r requirements.txt
```

```
python-dateutil
pyserial
screeninfo
Pillow
```

---

## Ejecutar en desarrollo

```bash
python main.py
```

---

## Generar el ejecutable

Desde la carpeta del proyecto, con doble click o desde consola:

```bat
build.bat
```

El ejecutable queda en `dist\SistemaReyhan.exe`.

**Para instalar en la notebook del gimnasio:**
1. Copiar `dist\SistemaReyhan.exe` a la notebook.
2. Doble click para ejecutar — crea `gym.db` y `C:\backup_gym\` automáticamente.
3. Crear acceso directo en el escritorio.
4. Opcional: agregar al inicio de Windows para que arranque solo.

---

## Base de datos

SQLite (`gym.db`) con tres tablas:

| Tabla    | Descripción                              |
|----------|------------------------------------------|
| `socios` | Datos del socio: DNI, nombre, plan, etc. |
| `planes` | Planes disponibles y precios             |
| `pagos`  | Historial de pagos con fecha de vencimiento calculada por mes exacto |

Al iniciar por primera vez se crean los planes por defecto (Gym, Gym + Pilates x1/2/3).

---

## Configuración de la puerta

La configuración del relé USB se guarda en `config_puerta.json` (al lado del ejecutable). Se puede editar desde el panel de administración → sección **Puerta**.

Parámetros disponibles:

| Parámetro         | Descripción                                      | Default |
|-------------------|--------------------------------------------------|---------|
| `puerto`          | Puerto COM del relé                              | COM3    |
| `baudrate`        | Velocidad serial                                 | 9600    |
| `comando_idx`     | Índice del tipo de comando del relé (0, 1 o 2)  | 0       |
| `tiempo_apertura` | Segundos que la puerta permanece abierta         | 3       |
| `simulacion`      | True para operar sin hardware real               | false   |

Para detectar el comando correcto del relé, usar la utilidad:

```bash
python relay_test.py
```

---

## Monitores

El sistema detecta automáticamente si hay un segundo monitor:

- **Monitor externo** → ventana de acceso a pantalla completa (sin bordes, sin barra de tareas).
- **Notebook** → panel de administración.

Si solo hay un monitor, la ventana de acceso ocupa la mitad derecha y el panel la mitad izquierda.

Se puede mejorar la detección instalando `screeninfo` (ya incluido en requirements).

---

## Backup

Los backups se guardan en `C:\backup_gym\` con el nombre `gym_backup_YYYYMMDD_HHMMSS.db`.

- **Automático**: al iniciar el sistema.
- **Manual**: botón **Backup** en el sidebar del panel de administración.
