<div align="center">

# Literatus Novelist

**Plataforma de lectura interactiva que combina literatura digital, biblioteca personal, economía virtual e inteligencia artificial conversacional para transformar obras clásicas en experiencias inmersivas.**

[![Angular](https://img.shields.io/badge/Angular-17.3-DD0031?style=for-the-badge&logo=angular&logoColor=white)](https://angular.io/)
[![Django](https://img.shields.io/badge/Django-6.0.4-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.17.1-A30000?style=for-the-badge)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Capacitor](https://img.shields.io/badge/Capacitor-8.4-119EFF?style=for-the-badge&logo=capacitor&logoColor=white)](https://capacitorjs.com/)

</div>

-------------------------------------------------------------------------

## 📖 Estado del Proyecto

**MVP funcional en desarrollo (Fase 2 - Avance).** El repositorio contiene una aplicación full-stack operativa con API REST, frontend en Angular, flujo de autenticación JWT, catálogo de libros, biblioteca personal, lector con capítulos HTML, chat con personajes IA, TTS, pagos Webpay y dashboard administrativo. Aún requiere hardening de seguridad, normalización de configuración y mejoras de producto antes de considerarse listo para producción.

## 🎯 ¿Qué Problema Resuelve?

Literatus Novelist busca reducir la fricción de entrada a la lectura profunda, especialmente en públicos acostumbrados a experiencias digitales dinámicas. Para ello, convierte obras literarias en una plataforma interactiva donde el usuario puede:
- Descubrir libros, autores, géneros y personajes.
- Adquirir obras o paquetes de "Tinta".
- Leer capítulos desde una biblioteca personal.
- Conversar con personajes o autores representados por avatares de IA.
- Desbloquear narración premium y experiencias de voz.
- Administrar contenido editorial desde un panel privado.

La solución separa claramente la experiencia de usuario en Angular de una API Django REST que concentra reglas de negocio, persistencia, seguridad, pagos y orquestación de IA.

## 🛠️ Stack Tecnológico

| Capa | Tecnologías |
| --- | --- |
| **Frontend web** | Angular 17.3, TypeScript 5.4, RxJS 7.8, Angular Material/CDK, Lucide Icons, Lottie |
| **PWA / Mobile** | Angular Service Worker, Web Manifest, Capacitor 8.4, Android Gradle project |
| **Backend** | Python 3.12+, Django 6.0.4, Django REST Framework 3.17.1, Simple JWT, drf-spectacular |
| **Base de datos** | PostgreSQL vía `DATABASE_URL`, modelos con UUID, auditoría temporal y soft delete |
| **IA conversacional** | OpenRouter / Google GenAI (Gemini), DeepSeek como proveedor de respaldo, system prompts por avatar |
| **Voz / audio** | Kokoro TTS vía API externa, ElevenLabs, ONNX Runtime Web, faster-whisper para flujos de alineación |
| **Pagos** | Transbank Webpay Plus SDK 6.1.0 |
| **Storage / media** | Media local en desarrollo; soporte para URL pública de Supabase Storage |
| **Deploy** | Frontend preparado para Vercel; backend preparado para Render/Gunicorn |

## ✨ Características Principales

- **Catálogo editorial normalizado:** Libros, autores, géneros, tags, ediciones, capítulos, reseñas y archivos protegidos.
- **Biblioteca personal:** Inventario por usuario, control de propiedad digital, progreso de lectura EPUB CFI/página y marcadores.
- **Lector inmersivo:** Lectura por capítulos HTML, descarga segura desde inventario, audios por capítulo y datos de alineación.
- **Personajes IA:** Avatares asociados a ediciones, desbloqueo por progreso, sesiones de chat, historial y contador de popularidad.
- **Motor multi-provider:** OpenRouter con failover y respaldo; consumo dinámico de Tinta según proveedor.
- **Economía virtual:** Perfiles con saldo de Tinta, compra de libros con Tinta y paquetes de recarga.
- **Pagos Webpay Plus:** Creación y confirmación de transacciones, entrega atómica de libros o Tinta y soporte para compras gratuitas.
- **Personalización de UI:** Soporte para temas (Oscuro, Claro, Sepia) modificables desde el perfil del usuario.
- **Dashboard administrativo:** Métricas, gestión de libros, parseo EPUB, alta/edición de autores, categorías y avatares.
- **API documentada:** Esquema OpenAPI y Swagger UI vía drf-spectacular.
- **PWA y Android:** Service worker para caché de assets/inventario y proyecto Android generado con Capacitor.

## 🏗️ Arquitectura

```mermaid
flowchart LR
    A["Angular SPA / PWA"] -->|JWT + REST| B["Django REST API"]
    B --> C["PostgreSQL"]
    B --> D["Webpay Plus"]
    B --> E["OpenRouter / Gemini / DeepSeek"]
    B --> F["Kokoro / ElevenLabs TTS"]
    B --> G["Media local o Supabase Storage"]
    A --> H["Capacitor Android"]
```

El backend está organizado por dominios:
- `users`: Identidad, perfiles, roles y saldo de Tinta.
- `catalog`: Catálogo público, autores, libros, ediciones, capítulos y reseñas.
- `library`: Inventario del usuario, progreso, marcadores y descargas.
- `ai_engine`: Avatares, sesiones, mensajes, providers LLM y TTS.
- `finance`: Transacciones Webpay y entrega atómica de compras.
- `dashboard`: Administración de contenido y analíticas.

-------------------------------------------------------------------------

## 🚀 Guía de Instalación y Ejecución Local

Sigue estos pasos para levantar el entorno de desarrollo de **Literatus Novelist** en tu máquina local.

### 1. Requisitos Previos
* Python 3.12.3
* PostgreSQL (con pgAdmin o psql)
* Node.js y npm

### 2. Configurar el Backend (Django)
Abre una terminal en la carpeta `Producto/backend`:
```bash
# Crear y activar el entorno virtual
python -m venv venv
venv\Scripts\activate  # En Windows
# source venv/bin/activate  # En Mac/Linux

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar el Frontend (Angular)
Abre otra terminal en la carpeta `Producto/frontend`:
```bash
# Instalar dependencias de Node y Angular CDK
npm install
npm install @angular/cdk
```

### 4. Configurar PostgreSQL
En tu pgAdmin o Query Tool de PostgreSQL, ejecuta los siguientes comandos para crear la base de datos y el usuario:
```sql
CREATE ROLE literatus_user WITH LOGIN PASSWORD 'literatus123';
CREATE DATABASE literatus_db WITH OWNER = literatus_user;
GRANT ALL PRIVILEGES ON DATABASE literatus_db TO literatus_user;
```

### 5. Variables de Entorno (`.env`)
En la carpeta `Producto/backend`, crea un archivo llamado `.env` y pega lo siguiente:

```env
# Activar modo depuración
DEBUG=True

# Clave secreta de Django (Generar una nueva con el comando de abajo)
SECRET_KEY='tu_clave_secreta_aqui'

# URL de conexión a la base de datos PostgreSQL
DATABASE_URL=postgres://literatus_user:literatus123@localhost:5432/literatus_db

# Hosts permitidos
ALLOWED_HOSTS=localhost,127.0.0.1

# Variables para IA y Voz (Solicitar al equipo o generar propias)
OPENROUTER_API_KEY="tu_api_key_aqui"
GOOGLE_API_KEY=""
DEEPSEEK_API_KEY=""

# Webpay / Transbank (Integración)
WEBPAY_COMMERCE_CODE=597055555532
WEBPAY_API_KEY=579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C
WEBPAY_ENVIRONMENT=INTEGRACION
WEBPAY_RETURN_URL=http://localhost:8000/api/v1/finance/confirm/
FRONTEND_URL=http://localhost:4200
```

*Para generar una nueva `SECRET_KEY`, puedes ejecutar:*
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Migrar la Base de Datos y crear Superusuario
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Poblar la Base de Datos (Seeders)
Con el entorno virtual activado, ejecuta los siguientes scripts en orden:

**En la carpeta `scripts`:**
```bash
python seed_classic_avatars.py
```

**En la carpeta `scripts/db_setup`:**
```bash
python seed_data.py
python seed_manga_avatars.py
python seed_metamorfosis.py
```

**En la carpeta `scripts/games_setup`:**
```bash
python seed_literatus_games.py
python populate_minigames.py
python populate_mochila.py
```

### 8. Cargar Libros de Prueba
Descomprime el archivo `libros.zip` (ubicado en la carpeta `Producto`) y combina su contenido con la carpeta `backend/media` para agregar los libros de prueba.

### 9. Levantar la Aplicación
**Backend:**
```bash
cd Producto/backend
python manage.py runserver
```
*(El backend correrá en http://localhost:8000/)*

**Frontend:**
```bash
cd Producto/frontend
ng serve
```
*(El frontend correrá en http://localhost:4200/)*

-------------------------------------------------------------------------

## 📡 Uso / Documentación Rápida de la API

### Registro y Login
```bash
curl -X POST http://localhost:8000/api/v1/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "email": "demo@example.com", "password": "Password123!"}'
```
El login devuelve `access`, `refresh` y datos básicos del usuario. Para endpoints privados usa: `Authorization: Bearer <ACCESS_TOKEN>`.

### Consultar Catálogo
```bash
curl http://localhost:8000/api/v1/catalog/books/
curl "http://localhost:8000/api/v1/catalog/books/?search=poe"
curl http://localhost:8000/api/v1/catalog/books/<book-slug>/details/
```

### Comprar una obra con Tinta
```bash
curl -X POST http://localhost:8000/api/v1/catalog/books/<book-slug>/purchase/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
*La compra usa una transacción atómica y bloquea el perfil con `select_for_update()` para evitar condiciones de carrera.*

### Iniciar Pago Webpay
```bash
curl -X POST http://localhost:8000/api/v1/finance/pay/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"item_type": "ink", "item_reference": "500"}'
```

### Chat con Personajes (IA)
```bash
curl -X POST http://localhost:8000/api/v1/ai/chat/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<session_uuid>", "message": "¿Qué debería aprender de este capítulo?"}'
```

-------------------------------------------------------------------------

## 📁 Estructura del Proyecto

```text
LiteratusNovelist/
|-- Documentacion/                         # Informes, manuales, QA, requerimientos y arquitectura
|-- Gestion/                               # Actas, integrantes y documentos de gestión académica
|-- Producto/
|   |-- backend/
|   |   |-- config/                        # Settings, urls, ASGI/WSGI
|   |   |-- core/                          # Modelo base, paginación, decoradores
|   |   |-- users/                         # Usuario custom, perfiles, JWT, Tinta
|   |   |-- catalog/                       # Libros, autores, géneros, ediciones, capítulos
|   |   |-- library/                       # Inventario, progreso, bookmarks, descargas
|   |   |-- ai_engine/                     # Avatares, chat, providers LLM, TTS
|   |   |-- finance/                       # Webpay Plus y transacciones
|   |   |-- dashboard/                     # Admin API y métricas
|   |   |-- scripts/                       # Seeds, scraping, sync de assets y utilidades
|   |   |-- json_data/                     # Datos auxiliares para importación/generación
|   |   |-- manage.py
|   |   |-- requirements.txt
|   |   `-- .env.example
|   `-- frontend/
|       |-- src/app/
|       |   |-- auth/                      # Login y registro
|       |   |-- catalog/                   # Listado, detalle, checkout y pagos
|       |   |-- library/                   # Biblioteca, lector, taberna y chat
|       |   |-- characters/                # Hub global de personajes IA
|       |   |-- dashboard/                 # Panel administrativo lazy-loaded
|       |   |-- core/                      # Servicios, guards, interceptor y componentes base
|       |   `-- users/                     # Perfil de usuario
|       |-- android/                       # Proyecto Android generado por Capacitor
|       |-- angular.json
|       |-- capacitor.config.ts
|       |-- ngsw-config.json
|       |-- package.json
|       `-- vercel.json
|-- prompt-mejoras-literatus.md            # Auditoría y backlog de mejoras
`-- README.md
```

## 🗺️ Roadmap / Tareas Pendientes
- **Hardening de producción:** Validar `DEBUG=False`, `ALLOWED_HOSTS`, CORS estricto, CSP, rotación de claves y separación de secretos por ambiente.
- **Configuración de entorno:** Ampliar `.env.example` con todas las variables que el backend lee.
- **Supabase y media:** Revisar uso de `supabase-js` desde frontend, asegurar RLS/buckets y mover operaciones sensibles al backend cuando corresponda.
- **Dashboard financiero:** Corregir la consulta de métricas que filtra transacciones por `AUTHORIZED`, ya que el modelo usa estados como `exitosa`, `fallida`, `iniciada` y `reversada`.
- **Flujos de cuenta:** Agregar recuperación de contraseña, verificación de email y políticas de bloqueo/rate limit para login.
- **Refuerzo de lógica de negocio:** Restringir permisos de escritura (POST/PUT/DELETE) en endpoints como `GenreViewSet` exclusivamente a administradores, y corregir rutas que esperan `<int:pk>` en modelos que usan UUID (ej. `AIAvatar`).
- **Idempotencia de Pagos:** Reforzar la confirmación de Webpay (especialmente recarga de Tinta) para evitar doble entrega si el token se confirma más de una vez.
- **SEO:** Implementar meta tags dinámicos, `robots.txt`, `sitemap.xml` y evaluar SSR/SSG para fichas de libros/autores.
- **Testing:** Ampliar pruebas backend para compras, Webpay, consumo de Tinta, permisos de biblioteca y chat; agregar pruebas frontend de rutas críticas.
- **Observabilidad:** Incorporar logging estructurado, captura de errores y métricas de latencia para IA/TTS/pagos.
- **Datos iniciales:** Formalizar comandos de seed/importación para que un nuevo entorno pueda poblar catálogo, autores, ediciones y avatares de forma reproducible.

## 👥 Autoría y Contacto

Proyecto académico desarrollado por:
- **Gonzalo Venegas** (`YoRHa-Type-A-n2`)
- **José Muñoz** (`jos2309`)

Para detalles de gestión, roles y documentos asociados, revisar `Gestion/Integrantes.txt` y la carpeta `Documentacion/`.

## 📄 Licencia

Proyecto académico Duoc UC. Definir una licencia Open Source formal antes de publicar o aceptar contribuciones externas.
```

5. Haz clic en **"Commit changes"** y realiza el Pull Request de siempre.

¡Con esto el README quedará hermoso, profesional y seguro (sin claves expuestas)! 🚀🏆
