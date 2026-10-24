import os
import django
import sys

# Configurar la ruta raíz del backend y el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from catalog.models import Book
from mochila.models import Item, AlternateStory, Backpack

User = get_user_model()

def run():
    print("=== POBLANDO CATÁLOGO GLOBAL DE MOCHILA Y EVENTOS ALTERNOS ===")

    # 1. Respaldo retroactivo: Crear mochilas para usuarios antiguos que se registraron antes de la señal
    users_without_backpack = [u for u in User.objects.all() if not hasattr(u, 'backpack')]
    for user in users_without_backpack:
        Backpack.objects.get_or_create(
            user=user,
            defaults={
                "points_balance": 0,
                "total_points_earned": 0
            }
        )
    if users_without_backpack:
        print(f"✓ Se crearon mochilas retroactivas para {len(users_without_backpack)} usuarios antiguos.")
    else:
        print("✓ Todos los usuarios existentes ya cuentan con su mochila.")

    # 2. Localizar el libro de Caperucita Roja
    book = Book.objects.filter(title__icontains="Caperucita").first()
    if not book:
        print("[ERROR] El libro de Caperucita Roja no está registrado en la base de datos.")
        return
    print(f"✓ Libro localizado: '{book.title}' (UUID: {book.id})")

    # 3. Crear el Objeto global: Hacha de leñador (método de desbloqueo: por lectura/minijuego)
    item_data = {
        "name": "Hacha de leñador",
        "description": "Una herramienta pesada y afilada perteneciente al leñador del bosque. ¡Podría ahuyentar a cualquier bestia!",
        "unlock_method": Item.UnlockMethod.READING,
        "points_cost": None,
        "is_active": True,
        "icon": "items/hacha.png"
    }

    item, created_item = Item.objects.get_or_create(
        book=book,
        name=item_data["name"],
        defaults=item_data
    )
    if created_item:
        print(f"✓ Objeto global '{item.name}' creado en el catálogo.")
    else:
        print(f"✓ El objeto global '{item.name}' ya se encontraba en el catálogo.")

    # 4. Crear la Historia Alterna global con el párrafo exacto que solicita el evento
    trigger_text = (
        "El lobo echó a correr tanto como pudo, tomando el camino más corto, y "
        "la niña fuese por el más largo entreteniéndose en coger avellanas, en correr "
        "detrás de las mariposas y en hacer ramilletes con las florecillas que hallaba a su paso."
    )

    alternate_html = (
        "<p>Caperucita continuó su camino con total tranquilidad, disfrutando de las flores y las mariposas, "
        "hasta llegar finalmente a la acogedora cabaña de su abuelita. Ambas pasaron una tarde maravillosa juntas, "
        "compartiendo un delicioso té con pastel de manzana.</p>"
        "<p>Al caer la tarde, se descubrió un detalle que nadie imaginaba: Caperucita había guardado por seguridad "
        "el <strong>hacha de leñador</strong> que él mismo se había dejado olvidada en el cobertizo de su casa.</p>"
        "<p>Al enterarse de lo sucedido, el valiente leñador salió de inmediato en busca del lobo feroz por los senderos del bosque. "
        "Tras cruzar la espesura, se encontró cara a cara con la fiera y le dio una severa y amistosa lección sobre el respeto "
        "y las buenas acciones, asegurando que el bosque volviera a ser un lugar seguro para todos.</p>"
    )

    story_data = {
        "title": "La tarde feliz y la lección del leñador",
        "chapter_index": 1,
        "trigger_phrase": trigger_text,
        "alternate_ending": alternate_html,
        "is_active": True
    }

    story, created_story = AlternateStory.objects.get_or_create(
        item=item,
        defaults=story_data
    )
    if not created_story:
        for key, value in story_data.items():
            setattr(story, key, value)
        story.save()
        print("✓ Historia alterna global actualizada correctamente.")
    else:
        print("✓ Historia alterna global creada correctamente.")

    print("\n🚀 ¡Configuración global lista!")
    print("   - Los nuevos usuarios obtienen su mochila de forma 100% automática gracias a `signals.py`.")
    print("   - El catálogo del hacha y el evento de Caperucita Roja ya están disponibles para todo el sistema.")

if __name__ == "__main__":
    run()