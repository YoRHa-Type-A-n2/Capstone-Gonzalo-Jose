import os
import django
import sys

# Configurar la ruta raíz del backend y el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from catalog.models import Book
from mochila.models import Item, AlternateStory, Backpack

User = get_user_model()

# Estructura global de los 10 relatos y objetos asociados (2 por libro).
# Este script es re-ejecutable: cada corrida SOBRESCRIBE en la BD cualquier campo
# que haya cambiado aquí (descripción, trigger_phrase, alternate_ending, etc.).
# Identidad de cada registro: Item = (libro, name) · AlternateStory = su Item.
# Si cambias el 'name' de un objeto se creará uno nuevo; renómbralo antes en el admin.
RELATOS_DATA = [
    # =========================================================================
    # 1. CAPERUCITA ROJA
    # =========================================================================
    {
        "book_query": "Caperucita",
        "item": {
            "name": "Hacha de leñador",
            "description": "Una herramienta pesada y afilada perteneciente al leñador del bosque. ¡Podría ahuyentar a cualquier bestia!",
            "unlock_method": Item.UnlockMethod.READING,
            "points_cost": None,
            "icon": "assets/images/items/hacha.png"
        },
        "story": {
            "title": "La tarde feliz y la lección del leñador",
            "chapter_index": 1,
            "trigger_phrase": (
                "El lobo echó a correr tanto como pudo, tomando el camino más corto, y "
                "la niña fuese por el más largo entreteniéndose en coger avellanas, en correr "
                "detrás de las mariposas y en hacer ramilletes con las florecillas que hallaba a su paso."
            ),
            "alternate_ending": (
                "<p>Caperucita continuó su camino con total tranquilidad, disfrutando de las flores y las mariposas, "
                "hasta llegar finalmente a la acogedora cabaña de su abuelita. Ambas pasaron una tarde maravillosa juntas, "
                "compartiendo un delicioso té con pastel de manzana.</p>"
                "<p>Al caer la tarde, se descubrió un detalle que nadie imaginaba: Caperucita había guardado por seguridad "
                "el <strong>hacha de leñador</strong> que él mismo se había dejado olvidada en el cobertizo de su casa.</p>"
                "<p>Al enterarse de lo sucedido, el valiente leñador salió de inmediato en busca del lobo feroz por los senderos del bosque. "
                "Tras cruzar la espesura, se encontró cara a cara con la fiera y le dio una severa y amistosa lección sobre el respeto "
                "y las buenas acciones, asegurando que el bosque volviera a ser un lugar seguro para todos.</p>"
            )
        }
    },
    {
        "book_query": "Caperucita",
        "item": {
            "name": "Candado de adivinanzas",
            "description": "Un candado mágico de seguridad que sólo responde ante la agudeza mental y la respuesta correcta.",
            "unlock_method": Item.UnlockMethod.PURCHASE,
            "points_cost": 150,
            "icon": "assets/images/items/candado.png"
        },
        "story": {
            "title": "El candado de las adivinanzas",
            "chapter_index": 1,
            "trigger_phrase": "Poco tardó el lobo en llegar a la casa de la abuela. Llamó: ¡pam! ¡pam!",
            "alternate_ending": (
                "<p>-¿Quién va?</p>"
                "<p>El lobo imitó la voz de Caperucita lo mejor que pudo, que no fue mucho: sonó como una niña con la cabeza dentro de un cubo.</p>"
                "<p>—¡Abuelita, soy yo! ¡Ábreme!</p>"
                "<p>Pero la abuela no había vivido ochenta años para caer en trucos así, y esa mañana había instalado en la puerta un <strong>candado de adivinanzas</strong>.</p>"
                "<p>—Solo se abre con la respuesta correcta —dijo el candado con voz de abuela—. Tiene dientes y no come, ni muerde ni dice nada. ¿Qué es?</p>"
                "<p>El lobo se rascó la cabeza. —¿Un… lobo? —Incorrecto.</p>"
                "<p>Pasó la tarde probando: un cocodrilo, una sierra, un tiburón con buenos modales. El candado no cedía. Cuando llegó Caperucita, le tocó otra adivinanza: «Cuanto más grande es, menos se ve». Contestó sin pestañear: —¡La oscuridad!</p>"
                "<p>Clic. La puerta se abrió. —Pasa, querida —dijo la abuela—. Y no le abras a nadie que conteste «un lobo».</p>"
                "<p>Al amanecer, un lobo ojeroso gritó desde el jardín: —¡UN PEINE! La abuela entreabrió la ventana y le lanzó uno. —Respuesta correcta. Y arréglate esa melena, hijo, que así no se visita a nadie.</p>"
            )
        }
    },

    # =========================================================================
    # 2. HANSEL Y GRETEL
    # =========================================================================
    {
        "book_query": "Hansel",
        "item": {
            "name": "Llave de cobre",
            "description": "Una llave misteriosa hecha de cobre pulido que encaja en cerraduras diminutas y secretas.",
            "unlock_method": Item.UnlockMethod.PURCHASE,
            "points_cost": 150,
            "icon": "assets/images/items/llave_cobre.png"
        },
        "story": {
            "title": "La llave de la cocina encantada",
            "chapter_index": 1,
            "trigger_phrase": "Y sin prestar atención a las lágrimas de los niños tomó a Hansel y lo metió en un diminuto cuarto esperando el día en que estuviese lo suficientemente gordo para comérselo. Una noche mientras la bruja dormía",
            "alternate_ending": (
                "<p>Gretel encontró la llave de cobre escondida detrás de una olla. En lugar de abrir la puerta de la habitación, la llave encajó en una cerradura diminuta de la despensa.</p>"
                "<p>Al girarla, se abrió una cocina encantada llena de utensilios parlantes con la <strong>llave de cobre</strong>. El cucharón cantaba ópera, el rallador contaba adivinanzas y una tetera repetía: —¡Agua caliente! ¡Agua caliente! ¡Pero que nadie me apure!</p>"
                "<p>La bruja entró corriendo y se llevó una enorme sorpresa. —¡Mi cocina secreta! ¡No quería que nadie la viera!</p>"
                "<p>Hansel y Gretel descubrieron que la bruja era una cocinera extraordinaria, pero sus platos siempre salían mal porque sus utensilios se pasaban el día discutiendo. Los niños organizaron un concurso de recetas y consiguieron que todos colaboraran.</p>"
                "<p>La bruja aprendió a preparar pasteles deliciosos y dejó de intentar encerrar visitantes. La cocina se volvió tan famosa que la gente viajaba kilómetros para probar su especialidad: una tarta que, al cortarla, soltaba un pequeño eructo de canela. La bruja la llamaba «Tarta de sorpresa». Hansel prefería llamarla «¡Cuidado con la última porción!».</p>"
            )
        }
    },
    {
        "book_query": "Hansel",
        "item": {
            "name": "Servilleta de lino",
            "description": "Una fina servilleta textil que enseña modales en la mesa hasta a las estructuras de dulce más rebeldes.",
            "unlock_method": Item.UnlockMethod.READING,
            "points_cost": None,
            "icon": "assets/images/items/servilleta.png"
        },
        "story": {
            "title": "La casa con buenos modales",
            "chapter_index": 1,
            "trigger_phrase": "¡Ven Gretel, yo comeré del techo y tu podrás comerte las ventanas!",
            "alternate_ending": (
                "<p>—¡Jovencito! ¡En esta casa no se come sin servilleta!</p>"
                "<p>Los niños se quedaron quietos. Gretel sacó la <strong>servilleta de lino</strong> que llevaba en el bolsillo, la partió en dos y ató una mitad al cuello de cada uno.</p>"
                "<p>—Mucho mejor —aprobó la casa—. Pueden comer, pero con la boca cerrada.</p>"
                "<p>En ese momento salió la bruja con una jaula bajo el brazo. La puerta se le cerró en las narices. —Usted tiene las manos sucias —dijo la casa—. Y llega tarde a la mesa. Sin lavarse no se entra.</p>"
                "<p>La bruja pasó la tarde en la fuente del jardín, frotándose las manos y refunfuñando, mientras los niños comían hasta quedar satisfechos. Al despedirse, la casa les preparó una fiambrera y les marcó el camino de regreso con chispas de chocolate pegadas con caramelo. La bruja seguía lavándose cuando Hansel y Gretel desaparecieron entre los árboles.</p>"
            )
        }
    },

    # =========================================================================
    # 3. EL GATO CON BOTAS
    # =========================================================================
    {
        "book_query": "Gato",
        "item": {
            "name": "Espejo de la verdad",
            "description": "Un espejo pulido que revela la verdadera vocación y forma interior de quien se mire en él.",
            "unlock_method": Item.UnlockMethod.READING,
            "points_cost": None,
            "icon": "assets/images/items/espejo.png"
        },
        "story": {
            "title": "El espejo que descubrió al mago pastelero",
            "chapter_index": 1,
            "trigger_phrase": "-He oído decir que puedes transformarte a tu antojo en cualquier animal. Si es en un perro, un zorro o también un lobo, puedo creérmelo, pero en un elefante me parece totalmente imposible, y por eso he venido, para convencerme por mí mismo.",
            "alternate_ending": (
                "<p>—¿Imposible? —se ofendió el mago, y de inmediato se transformó en un elefante enorme, después en un ratón y finalmente en una nube de humo verde que olía sospechosamente a repollo.</p>"
                "<p>El gato sacó el <strong>espejo de la verdad</strong> y se lo mostró. En el reflejo, el mago no aparecía como un hechicero temible, sino como un cocinero con gorro blanco y un delantal lleno de harina.</p>"
                "<p>—¡Eso es imposible! —gritó el mago—. ¡Yo soy el terror del reino! —Quizás —respondió el gato—, pero también podrías ser el terror de los concursos de repostería.</p>"
                "<p>El mago confesó que siempre había querido preparar pasteles, pero temía que los demás se rieran de él por ser tan poderoso y temido. El gato lo ayudó a organizar una pastelería en el castillo. Sus primeros bizcochos eran enormes: uno ocupaba toda una mesa y otro tuvo que transportarse en una carreta.</p>"
                "<p>El rey probó una porción y declaró que eran deliciosos. El mago se emocionó tanto que se transformó accidentalmente en una magdalena. El gato aprovechó para colocarle una pequeña cereza encima. —¡Ahora sí que eres un verdadero pastelero! —exclamó.</p>"
            )
        }
    },
    {
        "book_query": "Gato",
        "item": {
            "name": "Trompetilla de latón",
            "description": "Un instrumento musical de viento que amplifica el eco de las palabras diez veces más fuerte.",
            "unlock_method": Item.UnlockMethod.PURCHASE,
            "points_cost": 150,
            "icon": "assets/images/items/trompetilla.png"
        },
        "story": {
            "title": "La trompetilla que todo lo repetía",
            "chapter_index": 1,
            "trigger_phrase": "El gato, por su parte, se había adelantado y llegó a un gran prado donde había más de cien personas recogiendo heno.",
            "alternate_ending": (
                "<p>El gato se acercó a los campesinos y les entregó una trompetilla de latón.</p>"
                "<p>—Cuando pase el rey y pregunte de quién son estas tierras, griten con todas sus fuerzas mediante la <strong>trompetilla de latón</strong>: «¡Del Conde de Carabás!».</p>"
                "<p>Lo que no les dijo es que la trompetilla repetía cada palabra diez veces más fuerte. Cuando la carroza pasó, los campesinos gritaron y el eco rodó por las colinas: ¡CONDE DE CARABÁS! ¡CARABÁS! ¡BÁS! ¡BÁS!</p>"
                "<p>El eco llegó hasta el castillo del mago. —¿Un conde con mil voces? —tembló el mago—. ¡Viene un ejército a por mí! Metió su ropa en un baúl, se convirtió en gaviota y escapó por la ventana.</p>"
                "<p>Cuando llegaron el rey, el joven y el gato, hallaron la mesa puesta para doce y una nota: «Vuelvo en tres años. No toquen mi colección de dientes de león». El rey retrocedió, pálido. Pero en el jardín solo había cientos de dientes de león, las florecillas amarillas, regadas con mucho cariño. —¡Qué mago tan cuidadoso! —dijo el gato. El mago nunca volvió.</p>"
            )
        }
    },

    # =========================================================================
    # 4. LOS TRES CHANCHITOS
    # =========================================================================
    {
        "book_query": ("cerdito", "chanchito", "cochinito"),
        "item": {
            "name": "Cuerda de rescate",
            "description": "Una cuerda resistente ideal para ayudar a quienes han quedado atrapados en estrechos ductos de ventilación.",
            "unlock_method": Item.UnlockMethod.READING,
            "points_cost": None,
            "icon": "assets/images/items/cuerda.png"
        },
        "story": {
            "title": "La cuerda que salvó la cena",
            "chapter_index": 1,
            "trigger_phrase": "Entonces el lobo se enfadó de verdad y juró que se comería al cerdito, y que bajaría por la chimenea para atraparlo.",
            "alternate_ending": (
                "<p>El lobo trepó al tejado y se coló por la chimenea, pero era tan ancho que quedó atascado a medio camino. Al asomarse, el cerdito descubrió al lobo con las patas colgando por un lado y la cola moviéndose como un plumero por el otro.</p>"
                "<p>El cerdito sujetó la <strong>cuerda de rescate</strong> y lo ayudó a salir con cuidado. Cuando el lobo apareció, estaba tan cubierto de hollín que parecía una oveja negra con melena.</p>"
                "<p>El cerdito le ofreció un baño y una cena. El lobo, avergonzado, prometió dejar de asustarlo y confesó que siempre había querido trabajar como deshollinador.</p>"
                "<p>El cerdito le regaló un cepillo y una gorra. Pronto se convirtió en el deshollinador más famoso del bosque, porque podía limpiar tres chimeneas al mismo tiempo utilizando sus grandes pulmones.</p>"
                "<p>El negocio fue tan exitoso que tuvo que contratar ayudantes. Su primer empleado fue una cabra que solo aceptaba limpiar chimeneas si le pagaban con calcetines. Nadie supo nunca para qué quería tantos calcetines, pero el cerdito dejó de hacer preguntas.</p>"
            )
        }
    },
    {
        "book_query": ("cerdito", "chanchito", "cochinito"),
        "item": {
            "name": "Patines de ruedas",
            "description": "Un par de patines ligeros con cintas decorativas que permiten huir haciendo curvas a gran velocidad.",
            "unlock_method": Item.UnlockMethod.PURCHASE,
            "points_cost": 150,
            "icon": "assets/images/items/patines.png"
        },
        "story": {
            "title": "Los patines de los hermanos",
            "chapter_index": 1,
            "trigger_phrase": "El primero que se marchó se encontró con un hombre que llevaba un fardo de paja, y le dijo:",
            "alternate_ending": (
                "<p>—Por favor, buen hombre, déme esa paja para construirme una casa.</p>"
                "<p>El hombre se la dio, y el cerdito se construyó una casa con ella. Al poco llegó un lobo, llamó a la puerta y dijo:</p>"
                "<p>—Cerdito, cerdito, déjame entrar.</p>"
                "<p>A lo que el cerdo contestó:</p>"
                "<p>—¡No, no, por los pelos de mi barbita!</p>"
                "<p>El lobo entonces respondió:</p>"
                "<p>—¡Pues soplaré y resoplaré y tu casa derribaré!</p>"
                "<p>Así que sopló y resopló y la casa derribó… pero el cerdito, que llevaba en la mochila unos <strong>patines de ruedas</strong> con cintas de colores y se los había calzado por si acaso, salió disparado entre la paja y se perdió colina abajo. El lobo se quedó con la boca abierta y un montón de pajas entre los dientes.</p>"
                "<p>El segundo cerdito se encontró con un hombre que llevaba un haz de retama, y le dijo:</p>"
                "<p>—Por favor, buen hombre, déme esa retama para construirme una casa.</p>"
                "<p>El hombre se la dio, y el cerdo se construyó su casa. Entonces llegó el lobo y dijo:</p>"
                "<p>—Cerdito, cerdito, déjame entrar.</p>"
                "<p>—¡No, no, por los pelos de mi barbita!</p>"
                "<p>—¡Pues resoplaré y soplaré y tu casa derribaré!</p>"
                "<p>Así que sopló y resopló, y resopló y sopló, y al final derribó la casa… pero el segundo cerdito también llevaba sus patines puestos y salió volando por el camino, justo detrás de su hermano.</p>"
                "<p>Los dos cerditos se encontraron a mitad de la colina. —¡Agárrate! —gritó el primero. Bajaron a toda velocidad, haciendo eses, saltando raíces y silbando como el viento. El lobo corría tras ellos, pero en cada curva se pasaba y terminaba dándole la vuelta a un árbol entero.</p>"
                "<p>Los cerditos habían atado cintas de colores a sus patines. Con cada giro, el lobo se enredaba un poco más: primero las patas, luego la cola, luego las orejas, hasta quedar convertido en un paquete perfecto con un moño en la cabeza.</p>"
                "<p>Cuando llegaron a la casa de ladrillos, el tercer cerdito abrió la puerta y se encontró con dos hermanos patinando y un lobo envuelto como regalo de cumpleaños. —¿Es para mí? —preguntó. Lo desenredaron con cuidado y le sirvieron una taza de té. El lobo solo pidió una cosa: —La próxima vez, ¿podrían avisar antes de girar?</p>"
            )
        }
    },

    # =========================================================================
    # 5. EL PATITO FEO
    # =========================================================================
    {
        "book_query": "Patito",
        "item": {
            "name": "Peine de nenúfar",
            "description": "Un delicado peine tallado en hoja de agua que domina las plumas encrespadas y crea estilos despeinados elegantes.",
            "unlock_method": Item.UnlockMethod.READING,
            "points_cost": None,
            "icon": "assets/images/items/peine_nenufar.png"
        },
        "story": {
            "title": "El peluquero de las plumas rebeldes",
            "chapter_index": 1,
            "trigger_phrase": "Hasta se alegró de haber pasado por tantas penurias y tribulaciones, que lo capacitaban mejor para apreciar ahora su actual felicidad, su nueva situación entre toda aquella belleza que acudía a recibirlo.",
            "alternate_ending": (
                "<p>Los cisnes estaban preparando el Gran Desfile de Elegancia del Estanque, pero una fuerte ráfaga de viento había dejado sus plumas completamente desordenadas.</p>"
                "<p>El patito sacó de su bolso un pequeño <strong>peine de nenúfar</strong> y comenzó a ayudarlos.</p>"
                "<p>Peinó a uno hacia la izquierda, a otro hacia arriba y al más presumido le colocó una corona de pequeñas flores acuáticas. —¡Magnífico! —exclamó el cisne—. ¡Parecemos artistas!</p>"
                "<p>Pronto todos los animales del estanque hicieron fila para recibir un nuevo peinado. Una rana pidió un bigote, una tortuga quiso tener flequillo y un pato solicitó tantas plumas hacia arriba que terminó pareciendo una montaña.</p>"
                "<p>Cuando llegó el momento del desfile, una suave brisa volvió a despeinar a todos los participantes. Sin embargo, esta vez nadie se preocupó: ¡habían descubierto que los peinados más divertidos eran los que cambiaban con el viento!</p>"
                "<p>El patito se convirtió en el peluquero oficial del estanque. Su especialidad era el «despeinado elegante», aunque todavía no conseguía que la tortuga dejara de pedirle un corte de pelo.</p>"
            )
        }
    },
    {
        "book_query": "Patito",
        "item": {
            "name": "Delantal de bolsillos infinitos",
            "description": "Un delantal sorprendente capaz de recuperar cualquier objeto extraviado dentro de sus múltiples compartimentos.",
            "unlock_method": Item.UnlockMethod.PURCHASE,
            "points_cost": 150,
            "icon": "assets/images/items/delantal.png"
        },
        "story": {
            "title": "La oficina de objetos perdidos",
            "chapter_index": 1,
            "trigger_phrase": "Pues entonces guárdate tus opiniones cuando la gente sensata está hablando.",
            "alternate_ending": (
                "<p>Los dos animales suspiraron decepcionados. El patito bajó la cabeza, pero entonces encontró un delantal lleno de bolsillos colgado detrás de la puerta.</p>"
                "<p>Decidió ponérselo para ayudar con las tareas de la casa. Al principio parecía un delantal normal, pero pronto descubrieron que este <strong>delantal de bolsillos infinitos</strong> guardaba sorpresas.</p>"
                "<p>El patito metió el pico en uno y encontró un botón. En otro apareció una cuchara. En un tercero había una zanahoria que nadie recordaba haber comprado. —¡Es perfecto! —exclamó la gallina—. ¡Podemos guardar todas nuestras cosas!</p>"
                "<p>El gato aprovechó para buscar su ovillo de lana perdido. La gallina pidió ayuda para encontrar una llave y la anciana necesitaba recuperar sus lentes. El patito comenzó a revisar los bolsillos y sacó todo tipo de objetos: tres bellotas, una media, una pluma, dos caramelos y hasta una pequeña tetera.</p>"
                "<p>La casa se convirtió en una verdadera oficina de objetos perdidos. El gato organizaba los objetos por tamaño, la gallina los clasificaba por color y el patito se encargaba de guardar todo en su delantal.</p>"
            )
        }
    }
]

def upsert(model, lookup, data):
    """Crea el registro si no existe; si existe, sobrescribe solo los campos que cambiaron.
    Devuelve (objeto, creado, lista_de_campos_modificados)."""
    obj = model.objects.filter(**lookup).first()
    if obj is None:
        return model.objects.create(**lookup, **data), True, []

    changed = [field for field, value in data.items() if getattr(obj, field) != value]
    if changed:
        for field in changed:
            setattr(obj, field, data[field])
        obj.save()
    return obj, False, changed


def find_book(query):
    """Busca el libro por título. 'query' puede ser un texto o una tupla de alternativas."""
    queries = [query] if isinstance(query, str) else list(query)
    for q in queries:
        book = Book.objects.filter(title__icontains=q).first()
        if book:
            return book
    return None


def estado(created, changes):
    if created:
        return "creado"
    if changes:
        return "ACTUALIZADO (" + ", ".join(changes) + ")"
    return "sin cambios"


def run():
    print("=== POBLANDO CATÁLOGO GLOBAL DE MOCHILA Y EVENTOS ALTERNOS ===")

    # 1. Crear mochilas retroactivas para usuarios existentes
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

    # 2. Crear o sobrescribir objetos e historias alternas por libro
    print("\n--- Procesando objetos e historias alternas ---")
    omitidos = 0
    for entry in RELATOS_DATA:
        book_query = entry["book_query"]
        book = find_book(book_query)

        if not book:
            titulos = ", ".join(f"'{t}'" for t in Book.objects.values_list("title", flat=True))
            print(f"[ADVERTENCIA] No se encontró ningún libro que coincida con {book_query} en la BD. Omitiendo entrada.")
            print(f"              Títulos disponibles: {titulos}")
            omitidos += 1
            continue

        item_info = entry["item"]
        story_info = entry["story"]

        with transaction.atomic():
            item, item_created, item_changes = upsert(
                Item,
                {"book": book, "name": item_info["name"]},
                {
                    "description": item_info["description"],
                    "unlock_method": item_info["unlock_method"],
                    "points_cost": item_info["points_cost"],
                    "is_active": True,
                    "icon": item_info["icon"],
                },
            )
            print(f"  • [{book.title}] Objeto '{item.name}': {estado(item_created, item_changes)}.")

            story, story_created, story_changes = upsert(
                AlternateStory,
                {"item": item},
                {
                    "title": story_info["title"],
                    "chapter_index": story_info["chapter_index"],
                    "trigger_phrase": story_info["trigger_phrase"],
                    "alternate_ending": story_info["alternate_ending"],
                    "is_active": True,
                },
            )
            print(f"    └─ Historia alterna '{story.title}': {estado(story_created, story_changes)}.")

    print("\n🚀 ¡Población global completada con éxito!")
    print(f"   - Entradas procesadas: {len(RELATOS_DATA) - omitidos} de {len(RELATOS_DATA)}.")


if __name__ == "__main__":
    run()
