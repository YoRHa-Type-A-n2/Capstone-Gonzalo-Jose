import os
import django
import uuid
import sys


# Agregar la ruta raíz del backend (backend/) al path para que encuentre el módulo 'config'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Importar modelos del backend
from catalog.models import Book
from games.models import BookMinigame, Minigame

minigames_dataset = {
    "Caperucita Roja": {
        "rafaga_vf": [
            {
                "passage_text": "Caperucita Roja caminaba por el bosque para llevarle una cesta con comida a su abuelita enferma. En el camino, se encontró con el lobo feroz, quien le sugirió tomar el camino más largo.",
                "time_per_statement": 3,
                "statements": [
                    { "text": "Caperucita llevaba comida a su abuelita.", "isTrue": True },
                    { "text": "Caperucita se encontró con un oso en el bosque.", "isTrue": False },
                    { "text": "El lobo le sugirió tomar el camino más corto.", "isTrue": False }
                ]
            },
            {
                "passage_text": "El lobo llegó primero a la casa de la abuela, se vistió con su ropa y se metió en la cama esperando a Caperucita.",
                "time_per_statement": 3,
                "statements": [
                    { "text": "El lobo llegó a la casa antes que Caperucita.", "isTrue": True },
                    { "text": "El lobo se escondió debajo de la mesa.", "isTrue": False },
                    { "text": "El lobo usó la ropa de la abuela.", "isTrue": True }
                ]
            }
        ],
        "emoticono_dialogo": [
            {
                "emotionImage": "assets/images/emoticono/lobo_sorprendido.png",
                "dialogues": [
                    { "text": "¡Qué dientes tan grandes tienes!", "isCorrect": True },
                    { "text": "¡Qué flores tan bonitas llevas!", "isCorrect": False },
                    { "text": "¡Hola abuelita, vine a cantar!", "isCorrect": False },
                    { "text": "¡Me gusta mucho tu sombrero!", "isCorrect": False }
                ]
            },
            {
                "emotionImage": "assets/images/emoticono/caperucita_feliz.png",
                "dialogues": [
                    { "text": "¡Te traje unas galletas, abuelita!", "isCorrect": True },
                    { "text": "¡Tengo mucho miedo del lobo!", "isCorrect": False },
                    { "text": "¡Me he perdido en el bosque!", "isCorrect": False },
                    { "text": "¡Prefiero comer pastel de manzana!", "isCorrect": False }
                ]
            }
        ],
        "imagen_pixelada": [
            {
                "total_time": 7,
                "challenges": [
                    {
                        "correctCharacter": "Lobo Feroz",
                        "imageSrc": "assets/images/pixelado/lobo_disfrazado.png",
                        "options": ["El Cazador", "Lobo Feroz", "La Abuelita", "Caperucita", "El Leñador"]
                    }
                ]
            },
            {
                "total_time": 7,
                "challenges": [
                    {
                        "correctCharacter": "El Cazador",
                        "imageSrc": "assets/images/pixelado/cazador_bosque.png",
                        "options": ["El Leñador", "El Cazador", "El Lobo", "El Padre", "El Guardabosques"]
                    }
                ]
            }
        ],
        "encuentra_contradiccion": [
            {
                "timeLimit": 6,
                "challenges": [
                    {
                        "id": 1,
                        "premiseText": "Caperucita vestía una capa roja y llevaba una canasta con pan y miel para su abuelita.",
                        "explanation": "La imagen de contradicción muestra a Caperucita con una capa azul brillante.",
                        "images": [
                            { "id": 101, "imageSrc": "assets/images/contra/caperucita_roja_1.png", "altText": "Caperucita con capa roja", "isContradiction": False },
                            { "id": 102, "imageSrc": "assets/images/contra/caperucita_canasta.png", "altText": "Canasta con pan", "isContradiction": False },
                            { "id": 103, "imageSrc": "assets/images/contra/caperucita_azul.png", "altText": "Caperucita vistiendo capa azul", "isContradiction": True },
                            { "id": 104, "imageSrc": "assets/images/contra/bosque_camino.png", "altText": "Camino en el bosque", "isContradiction": False }
                        ]
                    }
                ]
            },
            {
                "timeLimit": 6,
                "challenges": [
                    {
                        "id": 2,
                        "premiseText": "El lobo feroz llegó primero a la casa de la abuelita y se disfrazó con su gorro de dormir.",
                        "explanation": "La contradicción muestra al lobo usando una corona de rey en lugar del gorro de dormir.",
                        "images": [
                            { "id": 105, "imageSrc": "assets/images/contra/lobo_gorro.png", "altText": "Lobo con gorro de dormir", "isContradiction": False },
                            { "id": 106, "imageSrc": "assets/images/contra/casa_abuela.png", "altText": "Casa de la abuelita", "isContradiction": False },
                            { "id": 107, "imageSrc": "assets/images/contra/lobo_corona.png", "altText": "Lobo vistiendo una corona de rey", "isContradiction": True },
                            { "id": 108, "imageSrc": "assets/images/contra/cama_abuela.png", "altText": "Cama de la abuelita", "isContradiction": False }
                        ]
                    }
                ]
            }
        ],
        "reconstruccion_manuscrito": [
            {
                "challenges": [
                    {
                        "id": 1,
                        "title": "El encuentro en el bosque",
                        "fragments": [
                            { "id": 1, "text": "Caperucita recibe la canasta de comida y se despide cariñosamente de su madre." },
                            { "id": 2, "text": "Al entrar al bosque, se distrae juntando flores silvestres a la orilla del camino." },
                            { "id": 3, "text": "Un lobo astuto se le acerca con amabilidad y le pregunta hacia dónde se dirige." },
                            { "id": 4, "text": "La niña le confiesa ingenuamente que va a visitar a su abuelita enferma." },
                            { "id": 5, "text": "El lobo le sugirió tomar el camino más largo mientras él corre por el atajo." }
                        ]
                    }
                ]
            },
            {
                "challenges": [
                    {
                        "id": 2,
                        "title": "El rescate en la cabaña",
                        "fragments": [
                            { "id": 1, "text": "El lobo entra a la casa de la abuela, la encierra y se viste con su ropa de dormir." },
                            { "id": 2, "text": "Caperucita llega a la cabaña y nota sorprendida el gran tamaño de los ojos de su abuela." },
                            { "id": 3, "text": "Al preguntar por sus enormes dientes, el lobo salta de la cama para atraparla." },
                            { "id": 4, "text": "Los fuertes gritos de auxilio de la niña son escuchados por un leñador cercano." },
                            { "id": 5, "text": "El leñador entra rápidamente a la casa, libra a la abuela y espanta al lobo para siempre." }
                        ]
                    }
                ]
            }
        ],
        "completa_dialogo": [
            {
                "levels": [
                    {
                        "id": 1,
                        "textBefore": "¡Qué",
                        "textAfter": "tan grandes tienes, abuelita! —dijo la niña extrañada.",
                        "correctWord": "orejas",
                        "options": ["orejas", "manos", "zapatos", "sombreros"],
                        "timeLeft": 7.0
                    }
                ]
            },
            {
                "levels": [
                    {
                        "id": 2,
                        "textBefore": "¡Qué orejas tan grandes tienes! —Son para",
                        "textAfter": "mejor —respondió el lobo disfrazado en la cama.",
                        "correctWord": "oírte",
                        "options": ["oírte", "comerte", "abrazarte", "mirarte"],
                        "timeLeft": 7.0
                    }
                ]
            }
        ],
        "testigo_ocular": [
            {
                "id": 1,
                "title": "Caperucita Roja",
                "imageUrl": "assets/images/testigo/caperucita_bosque.png",
                "questions": [
                    {
                        "prompt": "¿De qué color es la capa/caperuza de la niña?",
                        "correctOption": "Rojo",
                        "options": ["Rojo", "Azul", "Verde", "Amarillo"]
                    },
                    {
                        "prompt": "¿Qué animal aparece acechando en la escena?",
                        "correctOption": "El Lobo",
                        "options": ["El Lobo", "El Oso", "El Zorro", "El Cazador"]
                    },
                    {
                        "prompt": "¿Qué objeto lleva Caperucita en la mano/brazo?",
                        "correctOption": "Una canasta",
                        "options": ["Una canasta", "Un farol", "Un paraguas", "Un libro"]
                    }
                ]
            },
            {
                "id": 2,
                "title": "Cabaña de la Abuela",
                "imageUrl": "assets/images/testigo/casa_abuelita.png",
                "questions": [
                    {
                        "prompt": "¿Qué objeto había sobre la mesa junto a la cama de la abuela?",
                        "correctOption": "Un florero con rosas",
                        "options": ["Un florero con rosas", "Una lámpara encendida", "Un vaso de agua", "Un libro abierto"]
                    },
                    {
                        "prompt": "¿Qué prenda llevaba puesta el personaje recostado?",
                        "correctOption": "Un gorro de dormir",
                        "options": ["Un gorro de dormir", "Una corona", "Un sombrero de paja", "Un casco"]
                    },
                    {
                        "prompt": "¿De qué color eran las cortinas de la ventana de la cabaña?",
                        "correctOption": "Rojas con cuadros blancos",
                        "options": ["Rojas con cuadros blancos", "Verdes lisas", "Azules con flores", "Amarillas"]
                    }
                ]
            }
        ],
        "cazador_intrusos": [
            {
                "id": 1,
                "title": "La Cabaña de la Abuela",
                "textDescription": "Al entrar en la cabaña, Caperucita vio a su abuela recostada bajo una manta roja en su cama de madera. Sobre la mesa descansaba la cesta de pan, mientras el lobo disfrazado observaba pacientemente.",
                "bgImageUrl": "assets/images/cazador-intrusos/cabana-abuela-bg.jpg",
                "items": [
                    { "id": "item-1", "name": "Cesta de pan", "imageUrl": "assets/images/cazador-intrusos/cesta-pan.png", "isIntruder": False },
                    { "id": "item-2", "name": "Cama de madera", "imageUrl": "assets/images/cazador-intrusos/cama-madera.png", "isIntruder": False },
                    { "id": "item-3", "name": "Lobo disfrazado", "imageUrl": "assets/images/cazador-intrusos/lobo-disfrazado.png", "isIntruder": False },
                    { "id": "item-4", "name": "Manta roja", "imageUrl": "assets/images/cazador-intrusos/manta-roja.png", "isIntruder": False },
                    { "id": "item-5", "name": "Teléfono móvil", "imageUrl": "assets/images/cazador-intrusos/telefono-movil.png", "isIntruder": True },
                    { "id": "item-6", "name": "Extintor de incendios", "imageUrl": "assets/images/cazador-intrusos/extintor-incendios.png", "isIntruder": True }
                ]
            },
            {
                "id": 2,
                "title": "El Sendero del Bosque",
                "textDescription": "Caperucita caminaba entre los frondosos árboles llevando su capa roja, rodeada de hermosas flores silvestres y pequeñas mariposas que volaban a su alrededor.",
                "bgImageUrl": "assets/images/cazador-intrusos/bosque-bg.jpg",
                "items": [
                    { "id": "item-1", "name": "Capa roja", "imageUrl": "assets/images/cazador-intrusos/capa-roja.png", "isIntruder": False },
                    { "id": "item-2", "name": "Flores silvestres", "imageUrl": "assets/images/cazador-intrusos/flores.png", "isIntruder": False },
                    { "id": "item-3", "name": "Mariposas", "imageUrl": "assets/images/cazador-intrusos/mariposa.png", "isIntruder": False },
                    { "id": "item-4", "name": "Audífonos inalámbricos", "imageUrl": "assets/images/cazador-intrusos/audifonos.png", "isIntruder": True },
                    { "id": "item-5", "name": "Semáforo", "imageUrl": "assets/images/cazador-intrusos/semaforo.png", "isIntruder": True },
                    { "id": "item-6", "name": "Microondas", "imageUrl": "assets/images/cazador-intrusos/microondas.png", "isIntruder": True }
                ]
            }
        ],
        "busca_imagen": [
            {
                "id": 1,
                "storyTitle": "Caperucita Roja",
                "textSnippet": "Oculta entre las gruesas ramas del gran roble en medio del bosque, una pequeña cesta con manzanas descansaba olvidada.",
                "targetObjectName": "Cesta con manzanas",
                "imageUrl": "assets/images/busca-imagen/caperucita-cesta.jpg",
                "targetArea": {
                    "top": 62,
                    "left": 81,
                    "width": 14,
                    "height": 14
                }
            },
            {
                "id": 2,
                "storyTitle": "Caperucita Roja",
                "textSnippet": "Asomado detrás de la cortina del dormitorio, se podían ver las puntiagudas orejas del lobo acechando la llegada de la niña.",
                "targetObjectName": "Gorro del lobo",
                "imageUrl": "assets/images/busca-imagen/caperucita-dormitorio.jpg",
                "targetArea": {
                    "top": 25,
                    "left": 40,
                    "width": 18,
                    "height": 18
                }
            }
        ],
        "comics_desordenados": [
            {
                "id": 1,
                "title": "Caperucita Roja",
                "panels": [
                    { "id": 1, "image": "assets/images/comics/caperucita1.png" },
                    { "id": 2, "image": "assets/images/comics/caperucita2.png" },
                    { "id": 3, "image": "assets/images/comics/caperucita3.png" },
                    { "id": 4, "image": "assets/images/comics/caperucita4.png" }
                ]
            },
            {
                "id": 2,
                "title": "El Rescate de Caperucita",
                "panels": [
                    { "id": 1, "image": "assets/images/comics/caperucita5.png" },
                    { "id": 2, "image": "assets/images/comics/caperucita6.png" },
                    { "id": 3, "image": "assets/images/comics/caperucita7.png" },
                    { "id": 4, "image": "assets/images/comics/caperucita8.png" }
                ]
            }
        ]
    },
    "Los tres cerditos": {
        "rafaga_vf": [
            {
                "passage_text": "El primer cerdito construyó su casa de paja rápidamente para irse a jugar, mientras que el hermano mayor trabajó duro en su casa de ladrillos.",
                "time_per_statement": 3,
                "statements": [
                    { "text": "El primer cerdito hizo su casa de madera.", "isTrue": False },
                    { "text": "El hermano mayor usó ladrillos.", "isTrue": True },
                    { "text": "La casa de paja se construyó muy rápido.", "isTrue": True }
                ]
            },
            {
                "passage_text": "El lobo sopló y sopló hasta derrumbar las casas de paja y madera, pero la casa de ladrillo resistió sin moverse.",
                "time_per_statement": 3,
                "statements": [
                    { "text": "El lobo derribó la casa de ladrillo.", "isTrue": False },
                    { "text": "La casa de madera se cayó con el soplido.", "isTrue": True },
                    { "text": "El lobo usó un martillo para romper las casas.", "isTrue": False }
                ]
            }
        ],
        "emoticono_dialogo": [
            {
                "emotionImage": "assets/images/emoticono/lobo_furioso.png",
                "dialogues": [
                    { "text": "¡Soplaré y soplaré y tu casa derribaré!", "isCorrect": True },
                    { "text": "¡Por favor, déjame entrar a tomar té!", "isCorrect": False },
                    { "text": "¡Construyeron una linda casa!", "isCorrect": False },
                    { "text": "¡Vengo a entregarles una carta!", "isCorrect": False }
                ]
            },
            {
                "emotionImage": "assets/images/emoticono/cerdito_aliviado.png",
                "dialogues": [
                    { "text": "¡Aquí dentro el lobo no podrá hacernos nada!", "isCorrect": True },
                    { "text": "¡Tengo que construir otra casa de paja!", "isCorrect": False },
                    { "text": "¡El lobo es nuestro nuevo amigo!", "isCorrect": False },
                    { "text": "¡Salgamos a jugar al jardín!", "isCorrect": False }
                ]
            }
        ],
        "imagen_pixelada": [
            {
                "total_time": 7,
                "challenges": [
                    {
                        "correctCharacter": "Casa de Ladrillo",
                        "imageSrc": "assets/images/pixelado/casa_ladrillo.png",
                        "options": ["Casa de Paja", "Casa de Madera", "Casa de Ladrillo", "Castillo", "Cabaña de Piedra"]
                    }
                ]
            },
            {
                "total_time": 7,
                "challenges": [
                    {
                        "correctCharacter": "Cerdito Mayor",
                        "imageSrc": "assets/images/pixelado/cerdito_trabajador.png",
                        "options": ["Cerdito Menor", "Cerdito Mediano", "Cerdito Mayor", "Lobo", "Oso Constructor"]
                    }
                ]
            }
        ],
        "encuentra_contradiccion": [
            {
                "timeLimit": 6,
                "challenges": [
                    {
                        "id": 1,
                        "premiseText": "El cerdito mayor trabajó duro colocando ladrillos rojos para construir una casa resistente.",
                        "explanation": "La imagen de contradicción muestra la casa pintada completamente de color verde brillante.",
                        "images": [
                            { "id": 201, "imageSrc": "assets/images/contra/cerdito_construyendo_ladrillos.png", "altText": "Cerdito colocando ladrillos", "isContradiction": False },
                            { "id": 202, "imageSrc": "assets/images/contra/casa_ladrillos_roja.png", "altText": "Casa de ladrillos rojos", "isContradiction": False },
                            { "id": 203, "imageSrc": "assets/images/contra/casa_ladrillos_verde.png", "altText": "Casa de ladrillos verdes", "isContradiction": True },
                            { "id": 204, "imageSrc": "assets/images/contra/herramientas_construccion.png", "altText": "Herramientas de albañil", "isContradiction": False }
                        ]
                    }
                ]
            },
            {
                "timeLimit": 6,
                "challenges": [
                    {
                        "id": 2,
                        "premiseText": "El lobo intentó derribar la primera casa soplando con gran fuerza.",
                        "explanation": "La contradicción muestra al lobo intentando derribar la casa soplando con un secador de pelo en lugar de su propia boca.",
                        "images": [
                            { "id": 205, "imageSrc": "assets/images/contra/lobo_soplando.png", "altText": "Lobo soplando fuerte", "isContradiction": False },
                            { "id": 206, "imageSrc": "assets/images/contra/casa_paja_volando.png", "altText": "Paja volando por el aire", "isContradiction": False },
                            { "id": 207, "imageSrc": "assets/images/contra/lobo_secador.png", "altText": "Lobo sosteniendo un secador de pelo", "isContradiction": True },
                            { "id": 208, "imageSrc": "assets/images/contra/cerdito_huyendo.png", "altText": "Cerdito corriendo asustado", "isContradiction": False }
                        ]
                    }
                ]
            }
        ],
        "reconstruccion_manuscrito": [
            {
                "challenges": [
                    {
                        "id": 1,
                        "title": "La construcción de los hogares",
                        "fragments": [
                            { "id": 1, "text": "Tres hermanos cerditos deciden construir sus propias casas en el campo." },
                            { "id": 2, "text": "El menor, perezoso, edifica una cabaña simple usando paja en pocos minutos." },
                            { "id": 3, "text": "El segundo hermano recolecta ramas secas y arma su casita de madera." },
                            { "id": 4, "text": "El hermano mayor trabaja duro todo el día colocando ladrillos y cemento." },
                            { "id": 5, "text": "Al caer la noche, los tres cerditos se refugian tranquilos en sus viviendas." }
                        ]
                    }
                ]
            },
            {
                "challenges": [
                    {
                        "id": 2,
                        "title": "El soplo del lobo",
                        "fragments": [
                            { "id": 1, "text": "El lobo hambriento llega a la casa de paja y exige que le abran la puerta." },
                            { "id": 2, "text": "Sopla con fuerza y derriba la paja, haciendo correr al primer cerdito hacia la casa de madera." },
                            { "id": 3, "text": "El lobo sopla nuevamente y destruye la madera, obligando a los hermanos a huir." },
                            { "id": 4, "text": "Ambos se refugian en la sólida casa de ladrillo junto al hermano mayor." },
                            { "id": 5, "text": "El lobo sopla hasta cansarse pero no logra mover ni un solo ladrillo." }
                        ]
                    }
                ]
            }
        ],
        "completa_dialogo": [
            {
                "levels": [
                    {
                        "id": 1,
                        "textBefore": "¡Soplaré y soplaré y tu casa",
                        "textAfter": "! —gritó con fuerza el lobo feroz.",
                        "correctWord": "derribaré",
                        "options": ["derribaré", "pintaré", "limpiaré", "abriré"],
                        "timeLeft": 7.0
                    }
                ]
            },
            {
                "levels": [
                    {
                        "id": 2,
                        "textBefore": "En esta casa de",
                        "textAfter": "estamos totalmente seguros contra cualquier peligro.",
                        "correctWord": "ladrillo",
                        "options": ["ladrillo", "paja", "cristal", "cartón"],
                        "timeLeft": 7.0
                    }
                ]
            }
        ],
        "testigo_ocular": [
            {
                "id": 1,
                "title": "Construcción de la Casa de Ladrillos",
                "imageUrl": "assets/images/testigo/construccion_ladrillo.png",
                "questions": [
                    {
                        "prompt": "¿Qué herramienta tenía el cerdito mayor en la mano?",
                        "correctOption": "Una cuchara de albañil",
                        "options": ["Una cuchara de albañil", "Un martillo", "Una pala", "Un serrucho"]
                    },
                    {
                        "prompt": "¿De qué color eran los ladrillos amontonados?",
                        "correctOption": "Rojos",
                        "options": ["Rojos", "Grises", "Amarillos", "Azules"]
                    },
                    {
                        "prompt": "¿Qué llevaba puesto en la cabeza el cerdito constructor?",
                        "correctOption": "Un casco amarillo de protección",
                        "options": ["Un casco amarillo de protección", "Un gorro rojo", "Un sombrero de paja", "Nada"]
                    }
                ]
            },
            {
                "id": 2,
                "title": "El Soplo del Lobo",
                "imageUrl": "assets/images/testigo/lobo_soplando_paja.png",
                "questions": [
                    {
                        "prompt": "¿De qué color era la chimenea de la casa de paja?",
                        "correctOption": "No tenía chimenea",
                        "options": ["No tenía chimenea", "Roja", "Gris", "Amarilla"]
                    },
                    {
                        "prompt": "¿Hacia qué lado volaban los haces de paja cuando el lobo sopló?",
                        "correctOption": "Hacia la derecha de la pantalla",
                        "options": ["Hacia la derecha de la pantalla", "Hacia la izquierda", "Hacia arriba", "Hacia abajo"]
                    },
                    {
                        "prompt": "¿Qué expresión tenía el cerdito dentro de la casa?",
                        "correctOption": "Asustado corriendo",
                        "options": ["Asustado corriendo", "Sonriendo tranquilo", "Dormido", "Enojado"]
                    }
                ]
            }
        ],
        "cazador_intrusos": [
            {
                "id": 1,
                "title": "El Taller del Cerdito Mayor",
                "textDescription": "En la zona de construcción, el cerdito mayor organizaba los materiales indispensables: un montón de sólidos ladrillos, un balde de cemento listo para usarse, una plana regla de madera y su cuchara de albañil.",
                "bgImageUrl": "assets/images/cazador-intrusos/construccion-cerdito-bg.jpg",
                "items": [
                    { "id": "item-1", "name": "Ladrillos", "imageUrl": "assets/images/cazador-intrusos/ladrillos.png", "isIntruder": False },
                    { "id": "item-2", "name": "Balde de cemento", "imageUrl": "assets/images/cazador-intrusos/balde-cemento.png", "isIntruder": False },
                    { "id": "item-3", "name": "Cuchara de albañil", "imageUrl": "assets/images/cazador-intrusos/cuchara-albanil.png", "isIntruder": False },
                    { "id": "item-4", "name": "Regla de madera", "imageUrl": "assets/images/cazador-intrusos/regla-madera.png", "isIntruder": False },
                    { "id": "item-5", "name": "Nave espacial", "imageUrl": "assets/images/cazador-intrusos/nave-espacial.png", "isIntruder": True },
                    { "id": "item-6", "name": "Secador de pelo", "imageUrl": "assets/images/cazador-intrusos/secador-pelo.png", "isIntruder": True }
                ]
            },
            {
                "id": 2,
                "title": "El Claro del Bosque",
                "textDescription": "Cerca del bosque, los dos hermanos menores preparaban sus hogares. Uno juntaba atados de paja seca mientras que el otro acomodaba tablones de madera resistente.",
                "bgImageUrl": "assets/images/cazador-intrusos/claro-bosque-bg.jpg",
                "items": [
                    { "id": "item-1", "name": "Atado de paja", "imageUrl": "assets/images/cazador-intrusos/paja.png", "isIntruder": False },
                    { "id": "item-2", "name": "Tablones de madera", "imageUrl": "assets/images/cazador-intrusos/tablones.png", "isIntruder": False },
                    { "id": "item-3", "name": "Cuerda de amarre", "imageUrl": "assets/images/cazador-intrusos/cuerda.png", "isIntruder": False },
                    { "id": "item-4", "name": "Televisor de pantalla plana", "imageUrl": "assets/images/cazador-intrusos/tv.png", "isIntruder": True },
                    { "id": "item-5", "name": "Semáforo", "imageUrl": "assets/images/cazador-intrusos/semaforo.png", "isIntruder": True },
                    { "id": "item-6", "name": "Patineta eléctrica", "imageUrl": "assets/images/cazador-intrusos/patineta.png", "isIntruder": True }
                ]
            }
        ],
        "busca_imagen": [
            {
                "id": 1,
                "storyTitle": "Los tres cerditos",
                "textSnippet": "Cerca de la parte superior de la resistente pared roja, sobresalía la chimenea por donde el lobo intentaría entrar.",
                "targetObjectName": "Chimenea de ladrillos",
                "imageUrl": "assets/images/busca-imagen/casa-ladrillos.jpg",
                "targetArea": {
                    "top": 15,
                    "left": 70,
                    "width": 20,
                    "height": 20
                }
            },
            {
                "id": 2,
                "storyTitle": "Los tres cerditos",
                "textSnippet": "En la esquina inferior del patio, entre el polvo de la construcción, había quedado olvidada una pequeña cuchara de albañil.",
                "targetObjectName": "Cuchara de albañil",
                "imageUrl": "assets/images/busca-imagen/patio-construccion.jpg",
                "targetArea": {
                    "top": 75,
                    "left": 12,
                    "width": 15,
                    "height": 15
                }
            }
        ],
        "comics_desordenados": [
            {
                "id": 1,
                "title": "Construyendo las Casas",
                "panels": [
                    { "id": 1, "image": "assets/images/comics/cerditos1.png" },
                    { "id": 2, "image": "assets/images/comics/cerditos2.png" },
                    { "id": 3, "image": "assets/images/comics/cerditos3.png" },
                    { "id": 4, "image": "assets/images/comics/cerditos4.png" }
                ]
            },
            {
                "id": 2,
                "title": "El Soplo Feroz",
                "panels": [
                    { "id": 1, "image": "assets/images/comics/cerditos5.png" },
                    { "id": 2, "image": "assets/images/comics/cerditos6.png" },
                    { "id": 3, "image": "assets/images/comics/cerditos7.png" },
                    { "id": 4, "image": "assets/images/comics/cerditos8.png" }
                ]
            }
        ]
    },
    "El gato con botas": {
        "rafaga_vf": [
            {
                "passage_text": "Un joven molinero heredó solo un gato, pero el animal le prometió que si le daba un par de botas y un saco, lo haría muy rico.",
                "time_per_statement": 3,
                "statements": [
                    { "text": "El joven heredó un gran castillo.", "isTrue": False },
                    { "text": "El gato pidió unas botas y un saco.", "isTrue": True },
                    { "text": "El gato prometió ayudar a su dueño.", "isTrue": True }
                ]
            },
            {
                "passage_text": "El gato engañó al malvado ogro pidiéndole que se convirtiera en un pequeño ratón, momento en el cual se lo comió para quedarse con su castillo.",
                "time_per_statement": 3,
                "statements": [
                    { "text": "El ogro se convirtió en un gran león primero.", "isTrue": True },
                    { "text": "El gato se hizo amigo del ogro.", "isTrue": False },
                    { "text": "El gato se comió al ogro transformado en ratón.", "isTrue": True }
                ]
            }
        ],
        "emoticono_dialogo": [
            {
                "emotionImage": "assets/images/emoticono/gato_gritando.png",
                "dialogues": [
                    { "text": "¡Socorro! ¡El Marqués de Carabás se está ahogando en el río!", "isCorrect": True },
                    { "text": "¡Miren qué pez tan grande he atrapado para cenar!", "isCorrect": False },
                    { "text": "¡Hola Rey, venimos a cantar una hermosa canción!", "isCorrect": False },
                    { "text": "¡Tengo mucho frío, necesito que me presten ropa!", "isCorrect": False }
                ]
            },
            {
                "emotionImage": "assets/images/emoticono/ogro_fiero.png",
                "dialogues": [
                    { "text": "¡Puedo transformarme en un feroz y enorme león!", "isCorrect": True },
                    { "text": "¡Soy un pequeño ratoncito que busca queso!", "isCorrect": False },
                    { "text": "¡Bienvenidos a mi fiesta en el gran castillo!", "isCorrect": False },
                    { "text": "¡Me da mucho miedo la magia y los trucos!", "isCorrect": False }
                ]
            }
        ],
        "imagen_pixelada": [
            {
                "total_time": 7,
                "challenges": [
                    {
                        "correctCharacter": "El Gato con Botas",
                        "imageSrc": "assets/images/pixelado/gato_con_botas.png",
                        "options": ["El Marqués de Carabás", "El Gato con Botas", "El Rey", "El Ogro", "El Molinero"]
                    }
                ]
            },
            {
                "total_time": 7,
                "challenges": [
                    {
                        "correctCharacter": "Castillo del Ogro",
                        "imageSrc": "assets/images/pixelado/castillo_ogro.png",
                        "options": ["Casa del Molino", "Palacio Real", "Castillo del Ogro", "Choza del Bosque", "Cueva Misteriosa"]
                    }
                ]
            }
        ],
        "encuentra_contradiccion": [
            {
                "timeLimit": 6,
                "challenges": [
                    {
                        "id": 1,
                        "premiseText": "El hábil gato calzaba unas elegantes botas de cuero y llevaba un sombrero con pluma.",
                        "explanation": "La contradicción muestra al gato usando zapatillas deportivas en lugar de botas.",
                        "images": [
                            { "id": 301, "imageSrc": "assets/images/contra/gato_botas_cuero.png", "altText": "Gato con botas altas de cuero", "isContradiction": False },
                            { "id": 302, "imageSrc": "assets/images/contra/gato_sombrero.png", "altText": "Sombrero con pluma", "isContradiction": False },
                            { "id": 303, "imageSrc": "assets/images/contra/gato_zapatillas.png", "altText": "Gato con zapatillas deportivas", "isContradiction": True },
                            { "id": 304, "imageSrc": "assets/images/contra/gato_capa.png", "altText": "Gato vistiendo capa", "isContradiction": False }
                        ]
                    }
                ]
            },
            {
                "timeLimit": 6,
                "challenges": [
                    {
                        "id": 2,
                        "premiseText": "El gato llevaba un sombrero con una gran pluma y un saco al hombro.",
                        "explanation": "La imagen de contradicción muestra al gato usando una corona de cumpleaños en lugar de su sombrero.",
                        "images": [
                            { "id": 305, "imageSrc": "assets/images/contra/gato_sombrero_pluma.png", "altText": "Gato vistiendo sombrero con pluma", "isContradiction": False },
                            { "id": 306, "imageSrc": "assets/images/contra/gato_saco_hombro.png", "altText": "Gato cargando su saco de tela", "isContradiction": False },
                            { "id": 307, "imageSrc": "assets/images/contra/gato_corona_cumpleanos.png", "altText": "Gato con una corona de papel de cumpleaños", "isContradiction": True },
                            { "id": 308, "imageSrc": "assets/images/contra/botas_cuero.png", "altText": "Botas de cuero altas", "isContradiction": False }
                        ]
                    }
                ]
            }
        ],
        "reconstruccion_manuscrito": [
            {
                "challenges": [
                    {
                        "id": 1,
                        "title": "La herencia del molinero",
                        "fragments": [
                            { "id": 1, "text": "Un viejo molinero fallece dejando únicamente un astuto gato al menor de sus hijos." },
                            { "id": 2, "text": "El joven se lamenta por su suerte, temiendo no tener cómo ganarse la vida." },
                            { "id": 3, "text": "El gato habla con su amo y le pide un par de botas altas y una bolsa de tela." },
                            { "id": 4, "text": "El felino sale al monte y atrapa un conejo usando una trampa ingeniosa." },
                            { "id": 5, "text": "Lleva la presa al palacio real ofreciéndola como obsequio del Marqués de Carabás." }
                        ]
                    }
                ]
            },
            {
                "challenges": [
                    {
                        "id": 2,
                        "title": "El encuentro con el Ogro",
                        "fragments": [
                            { "id": 1, "text": "El gato marcha hacia el castillo de un poderoso y temido ogro mago." },
                            { "id": 2, "text": "Desafía al ogro preguntándole si es capaz de transformarse en un gran león." },
                            { "id": 3, "text": "El ogro demuestra su poder convirtiéndose en una enorme fiera que asusta al gato." },
                            { "id": 4, "text": "El felino lo reta a convertirse en un animal diminuto como un simple ratón." },
                            { "id": 5, "text": "El ogro se transforma en ratón y el gato salta instantáneamente sobre él comiéndoselo." }
                        ]
                    }
                ]
            }
        ],
        "completa_dialogo": [
            {
                "levels": [
                    {
                        "id": 1,
                        "textBefore": "No os preocupéis, mi señor, solo dadme unas",
                        "textAfter": "y veréis de lo que soy capaz.",
                        "correctWord": "botas",
                        "options": ["botas", "monedas", "armas", "riendas"],
                        "timeLeft": 7.0
                    }
                ]
            },
            {
                "levels": [
                    {
                        "id": 2,
                        "textBefore": "Os entrego este regalo de parte del famoso Marqués de",
                        "textAfter": "—dijo el gato al rey.",
                        "correctWord": "Carabás",
                        "options": ["Carabás", "Molinero", "Castillo", "Real"],
                        "timeLeft": 7.0
                    }
                ]
            }
        ],
        "testigo_ocular": [
            {
                "id": 1,
                "title": "El Gato ante el Rey",
                "imageUrl": "assets/images/testigo/gato_rey.png",
                "questions": [
                    {
                        "prompt": "¿De qué color era la pluma del sombrero del gato?",
                        "correctOption": "Roja",
                        "options": ["Roja", "Blanca", "Azul", "Dorada"]
                    },
                    {
                        "prompt": "¿Qué animal traía el gato dentro de su saco?",
                        "correctOption": "Un conejo",
                        "options": ["Un conejo", "Un pato", "Un pez", "Un ratón"]
                    },
                    {
                        "prompt": "¿Qué accesorio llevaba el Rey en sus manos?",
                        "correctOption": "Un cetro dorado",
                        "options": ["Un cetro dorado", "Una espada", "Un mapa del reino", "Un abanico"]
                    }
                ]
            },
            {
                "id": 2,
                "title": "El Gran Palacio del Ogro",
                "imageUrl": "assets/images/testigo/ogro_transformacion.png",
                "questions": [
                    {
                        "prompt": "¿Qué objeto sostenía el ogro antes de transformarse?",
                        "correctOption": "Un bastón mágico",
                        "options": ["Un bastón mágico", "Una copa de vino", "Un libro de hechizos", "Nada"]
                    },
                    {
                        "prompt": "¿En qué pequeño animal le pidió el gato al ogro que se convirtiera?",
                        "correctOption": "Un ratón",
                        "options": ["Un ratón", "Un pájaro", "Un insecto", "Un sapo"]
                    },
                    {
                        "prompt": "¿De qué material era el gran tapiz colgado en la pared del palacio?",
                        "correctOption": "De terciopelo rojo con bordados dorados",
                        "options": ["De terciopelo rojo con bordados dorados", "De lino blanco", "De seda azul", "No había tapiz"]
                    }
                ]
            }
        ],
        "cazador_intrusos": [
            {
                "id": 1,
                "title": "La Habitación del Gato",
                "textDescription": "El astuto felino preparaba sus pertenencias antes de partir hacia el palacio real: unas elegantes botas de cuero, su clásico sombrero con pluma, el saco de tela para la caza, un cinto ajustado y una amplia capa.",
                "bgImageUrl": "assets/images/cazador-intrusos/habitacion-gato-bg.jpg",
                "items": [
                    { "id": "item-1", "name": "Botas de cuero", "imageUrl": "assets/images/cazador-intrusos/botas.png", "isIntruder": False },
                    { "id": "item-2", "name": "Sombrero con pluma", "imageUrl": "assets/images/cazador-intrusos/sombrero.png", "isIntruder": False },
                    { "id": "item-3", "name": "Saco de tela", "imageUrl": "assets/images/cazador-intrusos/saco.png", "isIntruder": False },
                    { "id": "item-4", "name": "Capa", "imageUrl": "assets/images/cazador-intrusos/capa.png", "isIntruder": False },
                    { "id": "item-5", "name": "Cinto de cuero", "imageUrl": "assets/images/cazador-intrusos/cinto.png", "isIntruder": False },
                    { "id": "item-6", "name": "Computadora portátil", "imageUrl": "assets/images/cazador-intrusos/laptop.png", "isIntruder": True }
                ]
            },
            {
                "id": 2,
                "title": "El Gran Banquete Real",
                "textDescription": "En la mesa del rey se ofrecían deliciosos platillos de caza servidos en finas jarras de plata y copas de cristal.",
                "bgImageUrl": "assets/images/cazador-intrusos/banquete-real-bg.jpg",
                "items": [
                    { "id": "item-1", "name": "Jarra de plata", "imageUrl": "assets/images/cazador-intrusos/jarra-plata.png", "isIntruder": False },
                    { "id": "item-2", "name": "Copa de cristal", "imageUrl": "assets/images/cazador-intrusos/copa.png", "isIntruder": False },
                    { "id": "item-3", "name": "Plato de truchas", "imageUrl": "assets/images/cazador-intrusos/truchas.png", "isIntruder": False },
                    { "id": "item-4", "name": "Radio a pilas", "imageUrl": "assets/images/cazador-intrusos/radio.png", "isIntruder": True },
                    { "id": "item-5", "name": "Calculadora solar", "imageUrl": "assets/images/cazador-intrusos/calculadora.png", "isIntruder": True },
                    { "id": "item-6", "name": "Lámpara LED", "imageUrl": "assets/images/cazador-intrusos/lampara-led.png", "isIntruder": True }
                ]
            }
        ],
        "busca_imagen": [
            {
                "id": 1,
                "storyTitle": "El gato con botas",
                "textSnippet": "Junto al trono real, ocultas a la sombra de los pesados mantos del rey, relucían las botas de cuero bien lustradas del minino.",
                "targetObjectName": "Botas del gato",
                "imageUrl": "assets/images/busca-imagen/gato-trono.jpg",
                "targetArea": {
                    "top": 70,
                    "left": 45,
                    "width": 16,
                    "height": 16
                }
            },
            {
                "id": 2,
                "storyTitle": "El gato con botas",
                "textSnippet": "Cerca del gran ventanal del castillo, el fino sombrero con la pluma roja permanecía colgado de un perchero de bronce.",
                "targetObjectName": "Sombrero con pluma",
                "imageUrl": "assets/images/busca-imagen/castillo-ventanal.jpg",
                "targetArea": {
                    "top": 30,
                    "left": 15,
                    "width": 12,
                    "height": 12
                }
            }
        ],
        "comics_desordenados": [
            {
                "id": 1,
                "title": "El Astuto Plan del Gato",
                "panels": [
                    { "id": 1, "image": "assets/images/comics/gato1.png" },
                    { "id": 2, "image": "assets/images/comics/gato2.png" },
                    { "id": 3, "image": "assets/images/comics/gato3.png" },
                    { "id": 4, "image": "assets/images/comics/gato4.png" }
                ]
            },
            {
                "id": 2,
                "title": "Engañando al Ogro",
                "panels": [
                    { "id": 1, "image": "assets/images/comics/gato5.png" },
                    { "id": 2, "image": "assets/images/comics/gato6.png" },
                    { "id": 3, "image": "assets/images/comics/gato7.png" },
                    { "id": 4, "image": "assets/images/comics/gato8.png" }
                ]
            }
        ]
    },
    "Hansel y Gretel": {
        "rafaga_vf": [
            {
                "passage_text": "Hansel lanzó migas de pan al suelo para recordar el camino de regreso a casa, pero los pájaros del bosque se las comieron todas.",
                "time_per_statement": 3,
                "statements": [
                    { "text": "Hansel usó piedras blancas la primera vez.", "isTrue": True },
                    { "text": "Los pájaros se comieron las migas de pan.", "isTrue": True },
                    { "text": "Los niños encontraron el camino fácilmente.", "isTrue": False }
                ]
            },
            {
                "passage_text": "En medio del bosque encontraron una casita hecha de caramelos y chocolates. La anciana que vivía allí era en realidad una bruja malvada.",
                "time_per_statement": 3,
                "statements": [
                    { "text": "La casa estaba hecha de madera vieja.", "isTrue": False },
                    { "text": "Una amable abuelita vivía en la casa.", "isTrue": False },
                    { "text": "La casa estaba cubierta de dulces.", "isTrue": True }
                ]
            }
        ],
        "emoticono_dialogo": [
            {
                "emotionImage": "assets/images/emoticono/bruja_malvada.png",
                "dialogues": [
                    { "text": "¡Niños, entren a comer unos dulces!", "isCorrect": True },
                    { "text": "¡Sálvenme de este bosque oscuro!", "isCorrect": False },
                    { "text": "¡No toquen mi casa de madera!", "isCorrect": False },
                    { "text": "¡Voy a regalarles mi varita mágica!", "isCorrect": False }
                ]
            },
            {
                "emotionImage": "assets/images/emoticono/gretel_valiente.png",
                "dialogues": [
                    { "text": "¡No sé cómo mirar dentro del horno, enséñame cómo entra una persona!", "isCorrect": True },
                    { "text": "¡Bruja, voy a prepararte una sopa deliciosa!", "isCorrect": False },
                    { "text": "¡Déjame salir corriendo a buscar ayuda al bosque!", "isCorrect": False },
                    { "text": "¡Quiero encender el fuego para cocinar pan!", "isCorrect": False }
                ]
            }
        ],
        "imagen_pixelada": [
            {
                "total_time": 7,
                "challenges": [
                    {
                        "correctCharacter": "Casa de Dulces",
                        "imageSrc": "assets/images/pixelado/casa_dulces.png",
                        "options": ["Castillo Real", "Casa de Dulces", "Cabaña de Madera", "Cueva", "Torre de Piedra"]
                    }
                ]
            },
            {
                "total_time": 7,
                "challenges": [
                    {
                        "correctCharacter": "Hansel",
                        "imageSrc": "assets/images/pixelado/hansel_encerrado.png",
                        "options": ["Gretel", "Hansel", "El Padre", "El Leñador", "El Guardián"]
                    }
                ]
            }
        ],
        "encuentra_contradiccion": [
            {
                "timeLimit": 6,
                "challenges": [
                    {
                        "id": 1,
                        "premiseText": "Hansel arrojaba migas de pan blanco al suelo para marcar el camino de regreso a casa.",
                        "explanation": "La contradicción muestra a Hansel arrojando monedas de oro en lugar de pan.",
                        "images": [
                            { "id": 401, "imageSrc": "assets/images/contra/hansel_migas.png", "altText": "Hansel soltando migas", "isContradiction": False },
                            { "id": 402, "imageSrc": "assets/images/contra/camino_migas.png", "altText": "Migas en el suelo", "isContradiction": False },
                            { "id": 403, "imageSrc": "assets/images/contra/hansel_monedas.png", "altText": "Hansel tirando monedas de oro", "isContradiction": True },
                            { "id": 404, "imageSrc": "assets/images/contra/bosque_oscuro.png", "altText": "Bosque de noche", "isContradiction": False }
                        ]
                    }
                ]
            },
            {
                "timeLimit": 6,
                "challenges": [
                    {
                        "id": 2,
                        "premiseText": "La casita del bosque estaba construida completamente de dulces, chocolates y galletas.",
                        "explanation": "La contradicción muestra una casa hecha completamente de troncos de madera.",
                        "images": [
                            { "id": 405, "imageSrc": "assets/images/contra/casa_dulce.png", "altText": "Casa hecha de golosinas", "isContradiction": False },
                            { "id": 406, "imageSrc": "assets/images/contra/ventana_caramelo.png", "altText": "Ventanas de azúcar", "isContradiction": False },
                            { "id": 407, "imageSrc": "assets/images/contra/casa_madera_troncos.png", "altText": "Casa rústica de troncos", "isContradiction": True },
                            { "id": 408, "imageSrc": "assets/images/contra/techo_chocolate.png", "altText": "Techo de chocolate", "isContradiction": False }
                        ]
                    }
                ]
            }
        ],
        "reconstruccion_manuscrito": [
            {
                "challenges": [
                    {
                        "id": 1,
                        "title": "Perdidos en la espesura",
                        "fragments": [
                            { "id": 1, "text": "Debido a la escasez de comida, los niños son llevados a lo profundo del bosque." },
                            { "id": 2, "text": "Hansel deja caer pequeños pedazos de pan en el sendero para recordar el regreso." },
                            { "id": 3, "text": "Al intentar volver, descubren desconsolados que los pájaros se comieron todas las migas." },
                            { "id": 4, "text": "Caminam sin rumbo durante días entre los densos árboles buscando refugio." },
                            { "id": 5, "text": "A lo lejos divisan una extraña casita hecha enteramente de pan de jengibre." }
                        ]
                    }
                ]
            },
            {
                "challenges": [
                    {
                        "id": 2,
                        "title": "El engaño a la bruja",
                        "fragments": [
                            { "id": 1, "text": "Una malvada bruja atrapa a Hansel en una jaula y pone a Gretel a cocinar." },
                            { "id": 2, "text": "Como la bruja ve muy poco, Hansel le muestra un hueso de pollo para simular estar flaco." },
                            { "id": 3, "text": "Cansada de esperar, la bruja decide encender el horno de barro para cocinarlo." },
                            { "id": 4, "text": "Gretel engaña a la bruja pidiéndole que le muestre cómo revisar el fuego." },
                            { "id": 5, "text": "La niña empuja a la bruja dentro del horno, libera a su hermano y huyen con perlas." }
                        ]
                    }
                ]
            }
        ],
        "completa_dialogo": [
            {
                "levels": [
                    {
                        "id": 1,
                        "textBefore": "¡Miren! La ventana de esta casa está hecha de",
                        "textAfter": "transparente —dijo Hansel antes de probar un pedazo.",
                        "correctWord": "azúcar",
                        "options": ["azúcar", "plástico", "piedra", "madera"],
                        "timeLeft": 7.0
                    }
                ]
            },
            {
                "levels": [
                    {
                        "id": 2,
                        "textBefore": "Abre la boca y prueba este delicioso",
                        "textAfter": "de chocolate —dijo la anciana a Gretel.",
                        "correctWord": "pastel",
                        "options": ["pastel", "zapato", "juguete", "sombrero"],
                        "timeLeft": 7.0
                    }
                ]
            }
        ],
        "testigo_ocular": [
            {
                "id": 1,
                "title": "La Casa de Dulces",
                "imageUrl": "assets/images/testigo/casa_dulces_frente.png",
                "questions": [
                    {
                        "prompt": "¿De qué eran las paletas de la entrada de la casa de dulces?",
                        "correctOption": "De espiral rosado y blanco",
                        "options": ["De espiral rosado y blanco", "De chocolate oscuro", "De caramelo azul", "De gelatina verde"]
                    },
                    {
                        "prompt": "¿Qué dulce formaba las tejas del techo de la casita?",
                        "correctOption": "Galletas de jengibre",
                        "options": ["Galletas de jengibre", "Chicles", "Gomitas de ositos", "Mermelada"]
                    },
                    {
                        "prompt": "¿De qué material estaba hecha la cerca alrededor del jardín?",
                        "correctOption": "Bastones de caramelo",
                        "options": ["Bastones de caramelo", "Barras de chocolate", "Madera barnizada", "Caramelos duros"]
                    }
                ]
            },
            {
                "id": 2,
                "title": "En el Horno de la Bruja",
                "imageUrl": "assets/images/testigo/bruja_horno.png",
                "questions": [
                    {
                        "prompt": "¿Qué sostenía Gretel en la mano cerca del horno?",
                        "correctOption": "Una escoba de paja",
                        "options": ["Una escoba de paja", "Un plato de sopa", "Una llave de hierro", "Una varita"]
                    },
                    {
                        "prompt": "¿De qué material estaba hecha la puerta del horno iluminado?",
                        "correctOption": "Hierro forjado oscuro",
                        "options": ["Hierro forjado oscuro", "Madera de roble", "Piedra tallada", "Cobre brillante"]
                    },
                    {
                        "prompt": "¿Qué colgaba del techo sobre la zona del horno?",
                        "correctOption": "Atados de hierbas secas",
                        "options": ["Atados de hierbas secas", "Sartenes de cocina", "Jaulas de pájaros", "Candelabros de hierro"]
                    }
                ]
            }
        ],
        "cazador_intrusos": [
            {
                "id": 1,
                "title": "La Fachada Dulce",
                "textDescription": "Los niños sorprendidos contemplaron la fachada repleta de sabrosas golosinas: paredes hechas de pan de jengibre, tejas cubiertas de chocolate, bastones de caramelo flanqueando la puerta y calugas de manjar.",
                "bgImageUrl": "assets/images/cazador-intrusos/casa-dulce-bg.jpg",
                "items": [
                    { "id": "item-1", "name": "Pan de jengibre", "imageUrl": "assets/images/cazador-intrusos/jengibre.png", "isIntruder": False },
                    { "id": "item-2", "name": "Tejas de chocolate", "imageUrl": "assets/images/cazador-intrusos/chocolate.png", "isIntruder": False },
                    { "id": "item-3", "name": "Bastón de caramelo", "imageUrl": "assets/images/cazador-intrusos/baston-caramelo.png", "isIntruder": False },
                    { "id": "item-4", "name": "Caluga de manjar", "imageUrl": "assets/images/cazador-intrusos/caluga.png", "isIntruder": False },
                    { "id": "item-5", "name": "Hamburguesa con queso", "imageUrl": "assets/images/cazador-intrusos/hamburguesa.png", "isIntruder": True },
                    { "id": "item-6", "name": "Consola de videojuegos", "imageUrl": "assets/images/cazador-intrusos/consola.png", "isIntruder": True }
                ]
            },
            {
                "id": 2,
                "title": "Interior de la Cabaña",
                "textDescription": "Dentro de la cocina de la bruja se podía ver un gran horno de barro encendido, una jaula de hierro donde estaba Hansel y un cofre colmado de perlas y piedras preciosas.",
                "bgImageUrl": "assets/images/cazador-intrusos/interior-bruja-bg.jpg",
                "items": [
                    { "id": "item-1", "name": "Horno de barro", "imageUrl": "assets/images/cazador-intrusos/horno.png", "isIntruder": False },
                    { "id": "item-2", "name": "Jaula de hierro", "imageUrl": "assets/images/cazador-intrusos/jaula.png", "isIntruder": False },
                    { "id": "item-3", "name": "Cofre de perlas", "imageUrl": "assets/images/cazador-intrusos/cofre.png", "isIntruder": False },
                    { "id": "item-4", "name": "Monopatín", "imageUrl": "assets/images/cazador-intrusos/monopatin.png", "isIntruder": True },
                    { "id": "item-5", "name": "Impresora", "imageUrl": "assets/images/cazador-intrusos/impresora.png", "isIntruder": True },
                    { "id": "item-6", "name": "Sartén eléctrico", "imageUrl": "assets/images/cazador-intrusos/sarten.png", "isIntruder": True }
                ]
            }
        ],
        "busca_imagen": [
            {
                "id": 1,
                "storyTitle": "Hansel y Gretel",
                "textSnippet": "Oculto entre la densa hojarasca del camino, un pequeño pájaro blanco picoteaba las últimas migas de pan dejadas por Hansel.",
                "targetObjectName": "Pájaro blanco",
                "imageUrl": "assets/images/busca-imagen/bosque-migas.jpg",
                "targetArea": {
                    "top": 50,
                    "left": 30,
                    "width": 15,
                    "height": 15
                }
            },
            {
                "id": 2,
                "storyTitle": "Hansel y Gretel",
                "textSnippet": "Cerca del gran horno de barro, amarrada a un clavo de la pared, colgaba la pesada llave dorada que abría la jaula de hierro.",
                "targetObjectName": "Llave de la jaula",
                "imageUrl": "assets/images/busca-imagen/cocina-bruja.jpg",
                "targetArea": {
                    "top": 20,
                    "left": 80,
                    "width": 10,
                    "height": 10
                }
            }
        ],
        "comics_desordenados": [
            {
                "id": 1,
                "title": "Perdidos en el Bosque",
                "panels": [
                    { "id": 1, "image": "assets/images/comics/hansel1.png" },
                    { "id": 2, "image": "assets/images/comics/hansel2.png" },
                    { "id": 3, "image": "assets/images/comics/hansel3.png" },
                    { "id": 4, "image": "assets/images/comics/hansel4.png" }
                ]
            },
            {
                "id": 2,
                "title": "El Escape del Horno",
                "panels": [
                    { "id": 1, "image": "assets/images/comics/hansel5.png" },
                    { "id": 2, "image": "assets/images/comics/hansel6.png" },
                    { "id": 3, "image": "assets/images/comics/hansel7.png" },
                    { "id": 4, "image": "assets/images/comics/hansel8.png" }
                ]
            }
        ]
    },
    "El patito feo": {
        "rafaga_vf": [
            {
                "passage_text": "Un pequeño pajarito nació en un nido de patos. Era más grande y de color diferente a sus hermanos, por lo que todos en la granja se burlaban de él.",
                "time_per_statement": 3,
                "statements": [
                    { "text": "El patito era idéntico a sus hermanos.", "isTrue": False },
                    { "text": "Los animales de la granja eran amables con él.", "isTrue": False },
                    { "text": "El patito decidió irse de la granja.", "isTrue": True }
                ]
            },
            {
                "passage_text": "Pasó el frío invierno y al llegar la primavera, el patito se miró en el reflejo del agua y descubrió que se había transformado en un hermoso cisne blanco.",
                "time_per_statement": 3,
                "statements": [
                    { "text": "El patito se convirtió en un gran ganso.", "isTrue": False },
                    { "text": "Se dio cuenta de su cambio al verse en el agua.", "isTrue": True },
                    { "text": "Se transformó en un hermoso cisne blanco.", "isTrue": True }
                ]
            }
        ],
        "emoticono_dialogo": [
            {
                "emotionImage": "assets/images/emoticono/patito_triste.png",
                "dialogues": [
                    { "text": "Nadie quiere jugar conmigo por ser diferente...", "isCorrect": True },
                    { "text": "¡Soy el pato más rápido del estanque!", "isCorrect": False },
                    { "text": "¡Qué bonita es mi granja!", "isCorrect": False },
                    { "text": "¡Me encanta nadar con mis hermanos!", "isCorrect": False }
                ]
            },
            {
                "emotionImage": "assets/images/emoticono/cisne_majestuoso.png",
                "dialogues": [
                    { "text": "¡No soy un pato feo, soy un cisne!", "isCorrect": True },
                    { "text": "¡Extraño ser un pequeño patito gris!", "isCorrect": False },
                    { "text": "¡Nunca aprenderé a volar!", "isCorrect": False },
                    { "text": "¡Quiero regresar a la granja de pollos!", "isCorrect": False }
                ]
            }
        ],
        "imagen_pixelada": [
            {
                "total_time": 7,
                "challenges": [
                    {
                        "correctCharacter": "Patito Feo",
                        "imageSrc": "assets/images/pixelado/patito_nacimiento.png",
                        "options": ["Mamá Pata", "Patito Feo", "Pollito", "Cisne", "Pavo Real"]
                    }
                ]
            },
            {
                "total_time": 7,
                "challenges": [
                    {
                        "correctCharacter": "Granja de Animales",
                        "imageSrc": "assets/images/pixelado/granja_animales.png",
                        "options": ["Bosque Nevado", "Granja de Animales", "Lago Congelado", "Nido de Pájaros", "Molino de Viento"]
                    }
                ]
            }
        ],
        "encuentra_contradiccion": [
            {
                "timeLimit": 6,
                "challenges": [
                    {
                        "id": 1,
                        "premiseText": "El pequeño ave nadaba solitario en el estanque durante la fría época de invierno.",
                        "explanation": "La contradicción muestra al ave nadando bajo un sol de verano con palmeras alrededor.",
                        "images": [
                            { "id": 501, "imageSrc": "assets/images/contra/patito_nieve.png", "altText": "Patito entre la nieve", "isContradiction": False },
                            { "id": 502, "imageSrc": "assets/images/contra/estanque_congelado.png", "altText": "Estanque invernal", "isContradiction": False },
                            { "id": 503, "imageSrc": "assets/images/contra/patito_playa.png", "altText": "Patito en la playa tropical", "isContradiction": True },
                            { "id": 504, "imageSrc": "assets/images/contra/patito_triste.png", "altText": "Patito solo en el agua", "isContradiction": False }
                        ]
                    }
                ]
            },
            {
                "timeLimit": 6,
                "challenges": [
                    {
                        "id": 2,
                        "premiseText": "El patito nadó alegremente hacia el centro del estanque para reunirse con los hermosos cisnes.",
                        "explanation": "La imagen de contradicción muestra al patito nadando hacia un grupo de flamencos rosados en lugar de los cisnes blancos.",
                        "images": [
                            { "id": 505, "imageSrc": "assets/images/contra/patito_nadando_estanque.png", "altText": "Patito nadando en el estanque", "isContradiction": False },
                            { "id": 506, "imageSrc": "assets/images/contra/cisnes_blancos.png", "altText": "Grupo de cisnes blancos", "isContradiction": False },
                            { "id": 507, "imageSrc": "assets/images/contra/flamencos_rosados.png", "altText": "Grupo de flamencos rosados", "isContradiction": True },
                            { "id": 508, "imageSrc": "assets/images/contra/agua_estanque.png", "altText": "Agua cristalina del estanque", "isContradiction": False }
                        ]
                    }
                ]
            }
        ],
        "reconstruccion_manuscrito": [
            {
                "challenges": [
                    {
                        "id": 1,
                        "title": "El nacimiento en el corral",
                        "fragments": [
                            { "id": 1, "text": "Una mamá pato incuba sus huevos en un nido escondido cerca del estanque." },
                            { "id": 2, "text": "El último huevo en romper el cascarón revela un pajarillo grande y gris." },
                            { "id": 3, "text": "Las demás aves de la granja lo molestan constantemente por su apariencia." },
                            { "id": 4, "text": "El triste patito decide huir durante la noche para no estorbar a su familia." },
                            { "id": 5, "text": "Vaga sin destino soportando heladas y tempestades a lo largo de los meses." }
                        ]
                    }
                ]
            },
            {
                "challenges": [
                    {
                        "id": 2,
                        "title": "La transformación primaveral",
                        "fragments": [
                            { "id": 1, "text": "El sol vuelve a brillar marcando el inicio de una cálida primavera." },
                            { "id": 2, "text": "El patito despliega sus alas descubriendo que son más fuertes y grandes." },
                            { "id": 3, "text": "Aterriza en un lago donde ve nadar a tres majestuosas aves blancas." },
                            { "id": 4, "text": "Baja la cabeza con timidez y observa atentamente su propio reflejo en el cristalino agua." },
                            { "id": 5, "text": "Se da cuenta jubiloso de que no era un pato feo, sino un hermoso cisne." }
                        ]
                    }
                ]
            }
        ],
        "completa_dialogo": [
            {
                "levels": [
                    {
                        "id": 1,
                        "textBefore": "No te preocupes por tu aspecto, pronto llegará la",
                        "textAfter": "y todo cambiará.",
                        "correctWord": "primavera",
                        "options": ["primavera", "noche", "lluvia", "tormenta"],
                        "timeLeft": 7.0
                    }
                ]
            },
            {
                "levels": [
                    {
                        "id": 2,
                        "textBefore": "¡Miren! ¡No soy un pato, soy un elegante",
                        "textAfter": "! —exclamó con alegría.",
                        "correctWord": "cisne",
                        "options": ["cisne", "ganso", "halcón", "pavo"],
                        "timeLeft": 7.0
                    }
                ]
            }
        ],
        "testigo_ocular": [
            {
                "id": 1,
                "title": "El Nacimiento en la Granja",
                "imageUrl": "assets/images/testigo/patito_nacimiento_escena.png",
                "questions": [
                    {
                        "prompt": "¿Cuántos patitos amarillos nacieron junto al patito feo?",
                        "correctOption": "Cuatro",
                        "options": ["Cuatro", "Tres", "Cinco", "Dos"]
                    },
                    {
                        "prompt": "¿De qué color eran las plumas del patito feo al nacer?",
                        "correctOption": "Gris",
                        "options": ["Gris", "Amarillo", "Blanco", "Negro"]
                    },
                    {
                        "prompt": "¿Dónde se encontraba ubicado el nido de la mamá pata?",
                        "correctOption": "Junto a un matorral cerca del agua",
                        "options": ["Junto a un matorral cerca del agua", "Dentro del granero", "Sobre un montón de paja seca", "Bajo un puente de madera"]
                    }
                ]
            },
            {
                "id": 2,
                "title": "El Reflejo en el Estanque",
                "imageUrl": "assets/images/testigo/cisne_reflejo.png",
                "questions": [
                    {
                        "prompt": "¿Qué planta florecía al lado del estanque cuando se vio en el agua?",
                        "correctOption": "Lirios de agua",
                        "options": ["Lirios de agua", "Girasoles", "Rosas rojas", "Tulipanes"]
                    },
                    {
                        "prompt": "¿Qué figura proyectaba el agua al mirar su propio reflejo?",
                        "correctOption": "Un elegante cisne blanco",
                        "options": ["Un elegante cisne blanco", "Un pato gris", "Un ganso silvestre", "Un ave dorada"]
                    },
                    {
                        "prompt": "¿Cómo estaba el clima al momento de mirarse en el estanque?",
                        "correctOption": "Soleado de primavera",
                        "options": ["Soleado de primavera", "Lluvioso de otoño", "Nevado de invierno", "Nublado"]
                    }
                ]
            }
        ],
        "cazador_intrusos": [
            {
                "id": 1,
                "title": "El Corral de la Granja",
                "textDescription": "En el concurrido corral convivían armoniosamente Mamá Pata encubando sus huevos, una gallina cacareando, un pavo real desplegando sus plumas y un pequeño ganso.",
                "bgImageUrl": "assets/images/cazador-intrusos/corral-granja-bg.jpg",
                "items": [
                    { "id": "item-1", "name": "Mamá Pata", "imageUrl": "assets/images/cazador-intrusos/pata.png", "isIntruder": False },
                    { "id": "item-2", "name": "Gallina", "imageUrl": "assets/images/cazador-intrusos/gallina.png", "isIntruder": False },
                    { "id": "item-3", "name": "Pavo Real", "imageUrl": "assets/images/cazador-intrusos/pavo.png", "isIntruder": False },
                    { "id": "item-4", "name": "Ganso", "imageUrl": "assets/images/cazador-intrusos/ganso.png", "isIntruder": False },
                    { "id": "item-5", "name": "Pingüino de la Antártida", "imageUrl": "assets/images/cazador-intrusos/pinguino.png", "isIntruder": True },
                    { "id": "item-6", "name": "Submarino", "imageUrl": "assets/images/cazador-intrusos/submarino.png", "isIntruder": True }
                ]
            },
            {
                "id": 2,
                "title": "El Lago Primaveral",
                "textDescription": "Al llegar la primavera, el estanque brillaba rodeado de frondosos juncos verdes, hermosas flores de lirio flotando en el cristalino estanque y majestuosos cisnes blancos nadando en libertad.",
                "bgImageUrl": "assets/images/cazador-intrusos/lago-primaveral-bg.jpg",
                "items": [
                    { "id": "item-1", "name": "Juncos verdes", "imageUrl": "assets/images/cazador-intrusos/juncos.png", "isIntruder": False },
                    { "id": "item-2", "name": "Flores de lirio", "imageUrl": "assets/images/cazador-intrusos/lirios.png", "isIntruder": False },
                    { "id": "item-3", "name": "Cisne blanco", "imageUrl": "assets/images/cazador-intrusos/cisne.png", "isIntruder": False },
                    { "id": "item-4", "name": "Pista de esquí", "imageUrl": "assets/images/cazador-intrusos/esqui.png", "isIntruder": True },
                    { "id": "item-5", "name": "Raqueta de tenis", "imageUrl": "assets/images/cazador-intrusos/raqueta.png", "isIntruder": True },
                    { "id": "item-6", "name": "Lámpara de pie", "imageUrl": "assets/images/cazador-intrusos/lampara.png", "isIntruder": True }
                ]
            }
        ],
        "busca_imagen": [
            {
                "id": 1,
                "storyTitle": "El patito feo",
                "textSnippet": "Oculto entre la paja seca del rincón del corral, sobresalía un huevo considerablemente más grande que los demás.",
                "targetObjectName": "Huevo grande",
                "imageUrl": "assets/images/busca-imagen/corral-huevos.jpg",
                "targetArea": {
                    "top": 60,
                    "left": 25,
                    "width": 18,
                    "height": 18
                }
            },
            {
                "id": 2,
                "storyTitle": "El patito feo",
                "textSnippet": "Justo al centro del tranquilo estanque, la silueta reflejada de un esbelto cuello blanco se revelaba claramente sobre el agua.",
                "targetObjectName": "Reflejo del cisne",
                "imageUrl": "assets/images/busca-imagen/estanque-reflejo.jpg",
                "targetArea": {
                    "top": 45,
                    "left": 50,
                    "width": 22,
                    "height": 22
                }
            }
        ],
        "comics_desordenados": [
            {
                "id": 1,
                "title": "Nacimiento y Rechazo",
                "panels": [
                    { "id": 1, "image": "assets/images/comics/patito1.png" },
                    { "id": 2, "image": "assets/images/comics/patito2.png" },
                    { "id": 3, "image": "assets/images/comics/patito3.png" },
                    { "id": 4, "image": "assets/images/comics/patito4.png" }
                ]
            },
            {
                "id": 2,
                "title": "La Transformación",
                "panels": [
                    { "id": 1, "image": "assets/images/comics/patito5.png" },
                    { "id": 2, "image": "assets/images/comics/patito6.png" },
                    { "id": 3, "image": "assets/images/comics/patito7.png" },
                    { "id": 4, "image": "assets/images/comics/patito8.png" }
                ]
            }
        ]
    }
}

def run():
    print("=== POBLANDO MINIJUEGOS EN LA BASE DE DATOS ===")
    created_count = 0

    for book_title, game_types in minigames_dataset.items():
        # Búsqueda flexible usando palabras clave principales para evitar errores con artículos
        keyword = book_title.replace("El ", "").replace("Los ", "").strip()
        book = Book.objects.filter(title__icontains=keyword).first()
        
        if not book:
            print(f"[ERROR] El libro '{book_title}' (buscando por '{keyword}') no existe en la BD.")
            continue
            
        print(f"✓ Libro encontrado en BD: '{book.title}' con ID real: {book.id}")

        for game_code, samples in game_types.items():
            minigame, _ = Minigame.objects.get_or_create(
                code=game_code,
                defaults={
                    "name": game_code.replace('_', ' ').title(),
                    "description": f"Minijuego tipo {game_code}"
                }
            )

            for idx, sample_data in enumerate(samples, start=1):
                game, created = BookMinigame.objects.get_or_create(
                    book=book,
                    minigame=minigame,
                    config_data=sample_data,
                    defaults={
                        "title": f"Desafío {minigame.name} #{idx}"
                    }
                )
                if created:
                    created_count += 1

    print(f"\n✓ Proceso finalizado. Se crearon {created_count} nuevos registros.")

if __name__ == "__main__":
    run()