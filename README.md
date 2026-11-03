# Lulistrack Backend

API REST de **Lulistrack**, plataforma para la gestion y seguimiento de entregas de ultima milla. Este servicio conecta el dashboard web y la aplicacion movil con PostgreSQL, Supabase Auth y Supabase Storage.

## Aplicacion en linea
- **API:** https://backendlulistrack.onrender.com
- **Documentacion interactiva:** https://backendlulistrack.onrender.com/docs
- **Estado del servicio:** https://backendlulistrack.onrender.com/health
- **Dashboard web:** https://lulistrack-dashboard.vercel.app

## Tecnologias
- Python, FastAPI y Uvicorn
- SQLAlchemy y PostgreSQL mediante Psycopg 3
- Supabase Auth para autenticacion
- Supabase Storage para evidencias de entrega
- HTTPX para solicitudes a Supabase
- Render para el despliegue de la API

## Funcionalidades
- Autenticacion mediante tokens de Supabase y validacion de permisos administrativos.
- Registro, consulta y asignacion de pedidos.
- Consulta de pedidos activos, disponibles e historial de entregas.
- Registro de repartidores y creacion de sus cuentas de acceso.
- Toma de pedidos por repartidores autorizados.
- Registro de entregas con fotografia, firma y fecha.
- Almacenamiento de evidencias y generacion de enlaces temporales.

## Estructura del proyecto
```text
BackendLulistrack/
├── routers/
│   ├── drivers.py       # Endpoints de repartidores
│   └── orders.py        # Endpoints de pedidos y evidencias
├── auth.py              # Validacion de sesion y permisos
├── database.py          # Conexion a PostgreSQL
├── main.py              # Configuracion de FastAPI y CORS
├── models.py            # Modelos de SQLAlchemy
├── schemas.py           # Esquemas Pydantic
├── storage.py           # Operaciones con Supabase Storage
├── requirements.txt
├── .env.example
└── .gitignore
```

## Instalacion local

Requisitos: Python 3.11 o superior, PostgreSQL y un proyecto de Supabase con Auth y Storage habilitados.

1. Clona el repositorio:
   ```bash
   git clone https://github.com/AngelCuevas123/BackendLulistrack.git
   cd BackendLulistrack
   ```
2. Crea y activa un entorno virtual.

   **Windows PowerShell:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   **macOS / Linux:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Crea un archivo .env en la raiz usando .env.example como referencia y completa tus propios valores.
5. Inicia el servidor:
   ```bash
   uvicorn main:app --reload
   ```

La API estara disponible en http://127.0.0.1:8000. La documentacion interactiva estara en /docs.

## Variables de entorno

| Variable | Obligatoria | Descripcion |
| --- | --- | --- |
| DATABASE_URL | Si | Cadena de conexion a PostgreSQL. |
| SUPABASE_URL | Si | URL del proyecto Supabase. |
| SUPABASE_SERVICE_ROLE_KEY | Si | Clave privada para operaciones administrativas y Storage. |
| ADMIN_USER_ID | Una de las dos | UUID de un administrador de Supabase Auth. |
| ADMIN_USER_IDS | Una de las dos | UUID de varios administradores separados por comas. |
| SUPABASE_BUCKET | No | Bucket de Storage; por defecto evidencias-entrega. |
| CORS_ORIGINS | No | Origenes permitidos separados por comas. |

Ejemplo de formato (utiliza tus propios valores):
```env
DATABASE_URL=postgresql://usuario:contrasena@host:5432/base_de_datos
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_clave_privada_de_servidor
ADMIN_USER_ID=uuid-del-administrador
# ADMIN_USER_IDS=uuid-admin-1,uuid-admin-2
SUPABASE_BUCKET=evidencias-entrega
CORS_ORIGINS=https://lulistrack-dashboard.vercel.app,http://localhost:5173
```

**Seguridad:** nunca publiques el archivo .env, la clave SUPABASE_SERVICE_ROLE_KEY, contrasenas de PostgreSQL ni tokens privados. Configura estos valores como variables de entorno en Render. La clave service role debe permanecer exclusivamente en el backend.

## Endpoints principales

Todas las rutas protegidas requieren el encabezado Authorization: Bearer con un token valido de Supabase.

### Pedidos — /orders

| Metodo | Ruta | Acceso | Descripcion |
| --- | --- | --- | --- |
| GET | /orders/ | Administrador | Consulta todos los pedidos. |
| GET | /orders/active | Administrador | Consulta pedidos no entregados. |
| GET | /orders/completed | Administrador | Consulta entregas completadas. |
| POST | /orders/ | Administrador | Registra un pedido. |
| PATCH | /orders/{order_id}/assign | Administrador | Asigna un pedido a un repartidor. |
| GET | /orders/my | Repartidor | Consulta sus pedidos activos. |
| GET | /orders/my/completed | Repartidor | Consulta su historial. |
| GET | /orders/available | Repartidor | Consulta pedidos pendientes sin asignar. |
| POST | /orders/{order_id}/claim | Repartidor | Toma un pedido disponible. |
| POST | /orders/{order_id}/complete | Repartidor asignado | Registra la entrega y sus evidencias. |
| GET | /orders/{order_id}/evidence | Administrador o repartidor asignado | Consulta enlaces temporales de evidencias. |

### Repartidores — /drivers

| Metodo | Ruta | Acceso | Descripcion |
| --- | --- | --- | --- |
| GET | /drivers/ | Administrador | Consulta todos los repartidores. |
| POST | /drivers/ | Administrador | Crea la cuenta y perfil de un repartidor. |
| GET | /drivers/me | Repartidor | Consulta su propio perfil. |
| GET | /drivers/{driver_id} | Administrador | Consulta un repartidor por ID. |

### Sistema

| Metodo | Ruta | Descripcion |
| --- | --- | --- |
| GET | / | Mensaje de bienvenida. |
| GET | /health | Comprobacion basica del servicio. |
| GET | /docs | Documentacion interactiva Swagger UI. |

## Autenticacion y permisos

Supabase Auth autentica a los usuarios. El backend valida el token recibido consultando el servicio de usuarios de Supabase. Las operaciones administrativas comparan el UUID autenticado con ADMIN_USER_ID y/o ADMIN_USER_IDS. Las operaciones de repartidor comprueban que exista un perfil vinculado al UUID de Supabase.

## Evidencias de entrega

Al completar un pedido, el repartidor asignado envia fotografia y firma en Base64 junto con la fecha de entrega. El backend guarda los archivos en el bucket configurado y almacena sus rutas en PostgreSQL. Al consultar las evidencias, genera enlaces firmados con vigencia de una hora.

## Base de datos

Los modelos de SQLAlchemy representan las tablas orders y drivers. Al iniciar la aplicacion, Base.metadata.create_all crea las tablas que aun no existan. Para cambios de estructura en una base de datos existente, revisa el esquema antes de desplegar: create_all no sustituye un sistema de migraciones.

## Despliegue en Render

Configura las variables de entorno anteriores en Render. Un comando de inicio compatible con el servicio es:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Comprueba el servicio desde /health y consulta /docs para revisar las rutas disponibles.

---

**Lulistrack** — API para la gestion y seguimiento de entregas de ultima milla.
