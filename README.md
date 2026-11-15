# Lulistrack Backend — 3.0

API REST de **Lulistrack**, plataforma de gestión y seguimiento de entregas de última milla. El backend concentra la lógica de negocio y conecta el dashboard administrativo y la aplicación móvil con Supabase, PostgreSQL, almacenamiento de evidencias y Firebase.

## Servicios en línea

- **API:** https://backendlulistrack.onrender.com
- **Documentación interactiva:** https://backendlulistrack.onrender.com/docs
- **Estado del servicio:** https://backendlulistrack.onrender.com/health
- **Dashboard:** https://lulistrack-dashboard.vercel.app

## Ecosistema

| Componente | Tecnología | Repositorio |
| --- | --- | --- |
| Aplicación móvil | Flutter y Dart | [LulistrackApp](https://github.com/AngelCuevas123/LulistrackApp/tree/lulistrack-3.0) |
| Backend y API | FastAPI y Python | Este repositorio |
| Panel administrativo | React y Vite | [LulistrackDashboard](https://github.com/AngelCuevas123/LulistrackDashboard/tree/lulistrack-3.0) |
| Base de datos y autenticación | Supabase Auth y PostgreSQL | Proyecto Supabase |
| Evidencias | Supabase Storage | Proyecto Supabase |
| Notificaciones | Firebase Admin SDK e Installation ID | Proyecto Firebase |

## Funcionalidades

### Pedidos y repartidores
- Autenticación mediante tokens de Supabase.
- Validación de permisos administrativos y de repartidor.
- Registro y consulta de pedidos.
- Consulta de pedidos activos, disponibles e historial.
- Asignación de pedidos a repartidores.
- Aceptación de pedidos disponibles desde la app móvil.
- Registro de repartidores y creación de sus cuentas de acceso.
- Registro de entregas con fotografía, firma y fecha.
- Consulta de evidencias mediante enlaces temporales.

### Notificaciones push
- Registro y desactivación de dispositivos asociados a repartidores.
- Almacenamiento del Firebase Installation ID (FID) en PostgreSQL.
- Envío de notificaciones a los dispositivos activos de un repartidor mediante Firebase Admin SDK.
- Envío por lotes de hasta 500 identificadores por solicitud.
- Desactivación de identificadores que Firebase confirma como no registrados.
- Manejo de errores de notificación sin interrumpir la operación principal de asignación.

La app móvil registra el FID después de iniciar sesión y solicita al backend desactivarlo al cerrar sesión.

### Evidencias y almacenamiento
- Recepción de fotografía y firma codificadas en Base64.
- Almacenamiento de archivos en Supabase Storage.
- Persistencia de las referencias de evidencia en PostgreSQL.
- Generación de enlaces firmados temporales para consultar las evidencias.

## Tecnologías

- Python
- FastAPI y Uvicorn
- SQLAlchemy
- PostgreSQL y Psycopg 3
- Supabase Auth y Supabase Storage
- HTTPX
- Firebase Admin SDK
- Render para el despliegue de la API

## Estructura del proyecto

~~~text
BackendLulistrack/
├── routers/
│   ├── drivers.py
│   └── orders.py
├── services/
│   └── notification_service.py
├── auth.py
├── database.py
├── firebase_config.py
├── main.py
├── models.py
├── schemas.py
├── storage.py
├── requirements.txt
└── .env.example
~~~

## Endpoints principales

Las rutas protegidas requieren el encabezado Authorization: Bearer con un token válido de Supabase.

### Pedidos — /orders

| Método | Ruta | Acceso | Descripción |
| --- | --- | --- | --- |
| GET | /orders/ | Administrador | Consulta todos los pedidos. |
| GET | /orders/active | Administrador | Consulta pedidos activos. |
| GET | /orders/completed | Administrador | Consulta entregas completadas. |
| POST | /orders/ | Administrador | Registra un pedido. |
| PATCH | /orders/{order_id}/assign | Administrador | Asigna un pedido a un repartidor y dispara la notificación push. |
| GET | /orders/my | Repartidor | Consulta sus pedidos activos. |
| GET | /orders/my/completed | Repartidor | Consulta su historial. |
| GET | /orders/available | Repartidor | Consulta pedidos disponibles. |
| POST | /orders/{order_id}/claim | Repartidor | Acepta un pedido disponible. |
| POST | /orders/{order_id}/complete | Repartidor asignado | Registra la entrega y sus evidencias. |
| GET | /orders/{order_id}/evidence | Administrador o repartidor asignado | Consulta enlaces temporales de evidencias. |

### Repartidores — /drivers

| Método | Ruta | Acceso | Descripción |
| --- | --- | --- | --- |
| GET | /drivers/ | Administrador | Consulta todos los repartidores. |
| POST | /drivers/ | Administrador | Crea cuenta y perfil de repartidor. |
| GET | /drivers/me | Repartidor | Consulta su propio perfil. |
| GET | /drivers/{driver_id} | Administrador | Consulta un repartidor por ID. |
| POST | /drivers/me/fcm-token | Repartidor autenticado | Registra o reactiva el FID del dispositivo. |
| DELETE | /drivers/me/fcm-token | Repartidor autenticado | Desactiva el FID al cerrar sesión. |

Los endpoints conservan el nombre histórico fcm-token por compatibilidad; el valor que reciben y almacenan es el **Firebase Installation ID**, no un token FCM tradicional.

### Sistema

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | / | Mensaje de bienvenida. |
| GET | /health | Comprobación básica del servicio. |
| GET | /docs | Documentación interactiva Swagger UI. |

## Configuración local

Requisitos: Python 3.11 o superior, PostgreSQL y proyectos de Supabase y Firebase configurados.

1. Clona la rama 3.0:

   ~~~bash
   git clone --branch lulistrack-3.0 https://github.com/AngelCuevas123/BackendLulistrack.git
   cd BackendLulistrack
   ~~~

2. Crea y activa un entorno virtual:

   **Windows PowerShell**
   ~~~powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ~~~

   **macOS / Linux**
   ~~~bash
   python -m venv venv
   source venv/bin/activate
   ~~~

3. Instala dependencias:

   ~~~bash
   pip install -r requirements.txt
   ~~~

4. Copia .env.example a .env y configura los valores de tu entorno.

5. Configura una cuenta de servicio de Firebase Admin SDK fuera del repositorio y define FIREBASE_CREDENTIALS_PATH con la ruta local del archivo JSON.

6. Inicia la API:

   ~~~bash
   uvicorn main:app --reload
   ~~~

La API local estará disponible en http://127.0.0.1:8000 y Swagger UI en /docs.

## Variables de entorno

| Variable | Requerida | Descripción |
| --- | --- | --- |
| DATABASE_URL | Sí | Cadena de conexión a PostgreSQL. |
| SUPABASE_URL | Sí | URL del proyecto Supabase. |
| SUPABASE_SERVICE_ROLE_KEY | Sí | Clave privada usada únicamente por el backend. |
| ADMIN_USER_ID o ADMIN_USER_IDS | Sí | UUID de uno o varios administradores autorizados. |
| FIREBASE_CREDENTIALS_PATH | Sí | Ruta al JSON de la cuenta de servicio de Firebase Admin SDK. |
| SUPABASE_BUCKET | No | Bucket de evidencias; por defecto evidencias-entrega. |
| CORS_ORIGINS | No | Orígenes permitidos separados por comas. |

Ejemplo de formato (usa tus propios valores):

~~~env
DATABASE_URL=postgresql://usuario:contrasena@host:5432/base_de_datos
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_clave_privada_de_servidor
ADMIN_USER_ID=uuid-del-administrador
# ADMIN_USER_IDS=uuid-admin-1,uuid-admin-2
FIREBASE_CREDENTIALS_PATH=/ruta/segura/firebase-service-account.json
SUPABASE_BUCKET=evidencias-entrega
CORS_ORIGINS=https://lulistrack-dashboard.vercel.app,http://localhost:5173
~~~

No subas el archivo de cuenta de servicio, claves privadas, contraseñas ni archivos .env al repositorio. En Render, configura la cuenta de servicio como archivo secreto y define FIREBASE_CREDENTIALS_PATH con la ruta proporcionada por el entorno.

## Base de datos

SQLAlchemy representa las entidades de pedidos, repartidores y dispositivos. La tabla de dispositivos conserva el FID, la plataforma, el repartidor asociado y el estado activo. Al iniciar, Base.metadata.create_all crea las tablas que no existen; no sustituye un sistema de migraciones para modificar tablas ya creadas.

## Despliegue en Render

Configura las variables de entorno y el archivo secreto de Firebase en el servicio de Render. Un comando de inicio compatible es:

~~~bash
uvicorn main:app --host 0.0.0.0 --port $PORT
~~~

Comprueba el servicio en /health y revisa las rutas disponibles en /docs.

## Repositorios relacionados

- [Aplicación móvil — rama 3.0](https://github.com/AngelCuevas123/LulistrackApp/tree/lulistrack-3.0)
- [Dashboard — rama 3.0](https://github.com/AngelCuevas123/LulistrackDashboard/tree/lulistrack-3.0)

---

**Lulistrack 3.0** — API para la gestión y seguimiento de entregas de última milla.
