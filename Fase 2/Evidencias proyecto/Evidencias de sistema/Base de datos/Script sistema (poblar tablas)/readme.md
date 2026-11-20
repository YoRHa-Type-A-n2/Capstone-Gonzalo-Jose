# Base de Datos — Literatus

El esquema y los datos iniciales de este proyecto se gestionan originalmente mediante **Django ORM** (migraciones) y scripts de carga en Python (`scripts/games_setup/run_all_seeds.py`).

Los archivos `.sql` de esta carpeta corresponden al volcado limpio generado desde PostgreSQL para facilitar su despliegue o revisión directa sin necesidad de ejecutar el entorno de Python.

## Contenido
- `01_schema.sql`: Creación de tablas, claves primarias/foráneas, restricciones e índices (DDL).
- `02_datos.sql`: Inserción de catálogo de libros, capítulos, minijuegos, objetos e historias alternas (DML).

## Instrucciones de despliegue en PostgreSQL

### 1. Crear usuario, base de datos y permisos (como superusuario `postgres`)
Ejecutar en `psql` o en la herramienta de consulta de pgAdmin 4:

```sql
CREATE ROLE literatus_user WITH LOGIN PASSWORD 'literatus123';
CREATE DATABASE literatus_db WITH OWNER = literatus_user;
GRANT ALL PRIVILEGES ON DATABASE literatus_db TO literatus_user;