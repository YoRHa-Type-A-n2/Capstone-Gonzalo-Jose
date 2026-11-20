import os
import subprocess
import sys
from pathlib import Path

# Este script vive en: <backend_root>/scripts/games_setup/run_all_seeds.py
SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent
BACKEND_DIR = SCRIPTS_DIR.parent

SCRIPTS_TO_RUN = [
    # 1. Datos base y carga principal de libros
    SCRIPTS_DIR / "db_setup" / "seed_data.py",
    SCRIPT_DIR / "seed_literatus_games.py",

    # 2. Avatares y contenido complementario (se corren después de que existan los libros)
    SCRIPTS_DIR / "db_setup" / "seed_metamorfosis.py",
    SCRIPTS_DIR / "seed_classic_avatars.py",
    SCRIPTS_DIR / "db_setup" / "seed_manga_avatars.py",

    # 3. Minijuegos, mochila e historias alternas
    SCRIPT_DIR / "populate_minigames.py",
    SCRIPT_DIR / "populate_minigames_nuevos_libros.py",
    SCRIPT_DIR / "populate_minigames_nuevos_libros_2.py",
    SCRIPT_DIR / "populate_mochila.py",
    SCRIPT_DIR / "alternos.py",
]


def main() -> int:
    print(f"Usando intérprete: {sys.executable}")
    print(f"Directorio backend: {BACKEND_DIR}\n")

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{BACKEND_DIR}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(BACKEND_DIR)
    )

    total = len(SCRIPTS_TO_RUN)
    for idx, script_path in enumerate(SCRIPTS_TO_RUN, start=1):
        print(f"[{idx}/{total}] Ejecutando: {script_path.relative_to(BACKEND_DIR)}")

        if not script_path.exists():
            print(f"❌ Error: No se encontró el archivo {script_path}")
            return 1

        # Ejecutamos desde BACKEND_DIR para que rutas relativas como media/ o .env funcionen igual
        # que al correr manage.py desde la raíz del backend.
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BACKEND_DIR),
            env=env,
        )

        if result.returncode != 0:
            print(f"\n❌ Falló '{script_path.name}' con código de salida {result.returncode}.")
            print("Proceso detenido para evitar datos incompletos o inconsistentes.")
            return result.returncode

        print(f"✅ Completado: {script_path.name}\n")

    print("🎉 Todos los scripts de población finalizaron correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())