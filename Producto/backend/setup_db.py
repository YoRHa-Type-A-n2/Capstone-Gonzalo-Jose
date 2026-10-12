import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configura aquí tus credenciales de superusuario de PostgreSQL
DB_HOST = "localhost"
DB_PORT = "5432"
ADMIN_USER = "postgres"
ADMIN_PASSWORD = "gcngba182"  # Reemplaza con tu contraseña de postgres

# Datos de la nueva base de datos y usuario que el proyecto utilizará
NEW_DB_NAME = "literatus_db"
NEW_DB_USER = "literatus_user"
NEW_DB_PASSWORD = "literatus123"  # Puedes cambiar la contraseña del nuevo usuario

try:
    print("Conectando al servidor PostgreSQL como administrador...")
    connection = psycopg2.connect(
        user=ADMIN_USER,
        password=ADMIN_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    
    # Es obligatorio establecer el modo autocommit para crear bases de datos y usuarios
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()

    # 1. Crear la base de datos
    print(f"Creando la base de datos '{NEW_DB_NAME}'...")
    cursor.execute(f"CREATE DATABASE {NEW_DB_NAME};")
    print("Base de datos creada con éxito.")

    # 2. Crear el usuario y contraseña
    print(f"Creando el usuario '{NEW_DB_USER}'...")
    cursor.execute(f"CREATE USER {NEW_DB_USER} WITH PASSWORD '{NEW_DB_PASSWORD}';")
    print("Usuario creado con éxito.")

    # 3. Otorgar privilegios al usuario sobre la base de datos
    print("Otorgando permisos al usuario...")
    cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {NEW_DB_NAME} TO {NEW_DB_USER};")
    
    # Opcional pero recomendado en Postgres modernos para esquemas públicos:
    cursor.execute(f"ALTER DATABASE {NEW_DB_NAME} OWNER TO {NEW_DB_USER};")
    print("¡Configuración completada exitosamente!")

    print("\n--- TUS DATOS PARA EL ARCHIVO .ENV ---")
    print(f"DATABASE_URL=postgres://{NEW_DB_USER}:{NEW_DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{NEW_DB_NAME}")

except Exception as error:
    print(f"\nOcurrió un error durante la ejecución: {error}")

finally:
    if 'connection' in locals() and connection:
        cursor.close()
        connection.close()
        print("Conexión cerrada.")