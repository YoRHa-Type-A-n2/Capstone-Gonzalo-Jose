"""
populate_minigames_nuevos_libros_2.py
=====================================
Pobla los minijuegos de 9 libros nuevos (segundo lote) (2 desafíos x 10 tipos de juego = 20 por libro).

Uso:
    python populate_minigames_nuevos_libros_2.py                  # inserta en la BD
    python populate_minigames_nuevos_libros_2.py --export-images  # genera imagenes_por_crear.md (ambos lotes)
    python populate_minigames_nuevos_libros_2.py --export-images --flat  # igual, pero sin carpeta en el nombre

Igual que el primer lote (y a diferencia de populate_minigames.py):
  * NO borra todos los BookMinigame. Solo reemplaza los de estos 9 libros
    (se puede ejecutar varias veces sin duplicar y sin tocar Caperucita, etc.).
  * El libro se busca con una lista de palabras clave explícita (KEYWORDS).
  * Cada imagen nueva trae "imageDescription" (descripción para crearla). Es una
    clave extra dentro del JSON: el frontend puede ignorarla sin problema.
  * Las posiciones de las opciones correctas se mezclan con semilla fija
    (resultado reproducible).
"""
import os
import sys
import random

IMG = "assets/images/"

GAME_CODES = [
    "rafaga_vf", "emoticono_dialogo", "imagen_pixelada", "encuentra_contradiccion",
    "reconstruccion_manuscrito", "completa_dialogo", "testigo_ocular",
    "cazador_intrusos", "busca_imagen", "comics_desordenados",
]


# ----------------------------------------------------------------------------
# Funciones auxiliares (generan el mismo formato config_data de los otros libros)
# ----------------------------------------------------------------------------
def _mix(items, seed):
    items = list(items)
    random.Random(seed).shuffle(items)
    return items


def rafaga(passage, stmts):
    assert len(stmts) == 3, passage
    return {
        "passage_text": passage,
        "time_per_statement": 7,
        "statements": [{"text": t, "isTrue": v} for t, v in stmts],
    }


def emoticono(img, desc, correct, wrongs):
    assert len(wrongs) == 3, img
    d = [{"text": correct, "isCorrect": True}] + [{"text": w, "isCorrect": False} for w in wrongs]
    return {
        "emotionImage": f"{IMG}emoticono/{img}.png",
        "imageDescription": desc,
        "dialogues": _mix(d, img),
    }


def pixelada(img, desc, correct, wrongs):
    assert len(wrongs) == 4, img
    return {
        "total_time": 7,
        "challenges": [{
            "correctCharacter": correct,
            "imageSrc": f"{IMG}pixelado/{img}.png",
            "imageDescription": desc,
            "options": _mix([correct] + wrongs, img),
        }],
    }


def contradiccion(cid, base, premise, explanation, oks, bad):
    """oks: 3 tuplas (archivo, altText, descripcion). bad: 1 tupla (la contradicción)."""
    assert len(oks) == 3, premise
    imgs = [(f, a, d, False) for f, a, d in oks] + [(bad[0], bad[1], bad[2], True)]
    imgs = _mix(imgs, f"contra{base}")
    return {
        "timeLimit": 7,
        "challenges": [{
            "id": cid,
            "premiseText": premise,
            "explanation": explanation,
            "images": [
                {"id": base + n, "imageSrc": f"{IMG}contra/{f}.png", "altText": a,
                 "imageDescription": d, "isContradiction": c}
                for n, (f, a, d, c) in enumerate(imgs, start=1)
            ],
        }],
    }


def reconstruccion(cid, title, frags):
    """frags: 5 textos EN ORDEN CRONOLÓGICO (id 1..5 = orden correcto)."""
    assert len(frags) == 5, title
    return {"challenges": [{
        "id": cid, "title": title,
        "fragments": [{"id": i, "text": t} for i, t in enumerate(frags, start=1)],
    }]}


def completa(cid, before, after, correct, wrongs):
    assert len(wrongs) == 3, before
    return {"levels": [{
        "id": cid, "textBefore": before, "textAfter": after, "correctWord": correct,
        "options": _mix([correct] + wrongs, f"cd{cid}{correct}"), "timeLeft": 7.0,
    }]}


def testigo(tid, title, img, desc, qas):
    """qas: 3 tuplas (pregunta, correcta, [3 incorrectas])."""
    assert len(qas) == 3, title
    return {
        "id": tid, "title": title,
        "imageUrl": f"{IMG}testigo/{img}.png",
        "imageDescription": desc,
        "questions": [
            {"prompt": p, "correctOption": c, "options": _mix([c] + w, f"{img}{p}")}
            for p, c, w in qas
        ],
    }


def lib(key, name, intruder=False):
    """Objeto que YA existe en assets/images/cazador-intrusos/."""
    return {"key": key, "name": name, "isIntruder": intruder, "desc": None}


def new(key, name, desc):
    """Objeto correcto NUEVO (hay que crear la imagen con la descripción)."""
    return {"key": key, "name": name, "isIntruder": False, "desc": desc}


def cazador(cid, title, text, bg, bg_desc, items):
    ok = sum(1 for i in items if not i["isIntruder"])
    assert len(items) == 6 and 2 <= ok <= 5, title
    out = []
    for n, it in enumerate(_mix(items, f"cz{bg}"), start=1):
        d = {"id": f"item-{n}", "name": it["name"],
             "imageUrl": f"{IMG}cazador-intrusos/{it['key']}.png",
             "isIntruder": it["isIntruder"]}
        if it["desc"]:
            d["imageDescription"] = it["desc"]
        out.append(d)
    return {
        "id": cid, "title": title, "textDescription": text,
        "bgImageUrl": f"{IMG}cazador-intrusos/{bg}.jpg",
        "bgImageDescription": bg_desc,
        "items": out,
    }


def busca(bid, story, snippet, target, img, desc, area):
    top, left, w, h = area
    assert top + h <= 100 and left + w <= 100, target
    assert w * h in (1500, 1000), f"{target}: el objeto debe ocupar exactamente el 15% (escena recargada) o el 10% (escena estándar) de la imagen"
    return {
        "id": bid, "storyTitle": story, "textSnippet": snippet,
        "targetObjectName": target,
        "imageUrl": f"{IMG}busca-imagen/{img}.jpg",
        "imageDescription": desc,
        "targetArea": {"top": top, "left": left, "width": w, "height": h},
    }


def comic(cid, title, slug, start, descs):
    assert len(descs) == 4, title
    return {"id": cid, "title": title, "panels": [
        {"id": i, "image": f"{IMG}comics/{slug}{start + i - 1}.png", "imageDescription": d}
        for i, d in enumerate(descs, start=1)
    ]}


NEW_DATASET = {}
KEYWORDS = {}


def add_book(title, keywords, **games):
    assert set(games) == set(GAME_CODES), f"{title}: faltan/sobran juegos"
    for code, lst in games.items():
        assert len(lst) == 2, f"{title}/{code}: deben ser 2 desafíos"
    NEW_DATASET[title] = {code: games[code] for code in GAME_CODES}
    KEYWORDS[title] = keywords


# ============================================================================
# 1. LA BELLA DURMIENTE (Grimm / Perrault)
# ============================================================================
add_book(
    "La Bella Durmiente", ["Bella Durmiente", "Durmiente"],
    rafaga_vf=[
        rafaga("Cuando nació la princesa, el rey organizó una gran fiesta. Invitó a doce de las trece hadas del reino, porque solo tenía doce platos de oro.", [
            ("El rey invitó a doce hadas.", True),
            ("El rey invitó a las trece hadas.", False),
            ("Los platos de la fiesta eran de oro.", True)]),
        rafaga("El hada no invitada lanzó una maldición: a los quince años la princesa se pincharía con un huso. Otra hada suavizó el hechizo: la princesa dormiría cien años.", [
            ("La princesa se pincharía con un huso.", True),
            ("La maldición la lanzó un hada que sí fue invitada.", False),
            ("La princesa dormiría cien años.", True)]),
    ],
    emoticono_dialogo=[
        emoticono("bella_hada_enojada",
                  "Un hada de túnica negra y varita, con gesto de furia, de pie en la puerta de un gran salón de banquete de un castillo, frente al rey y la reina.",
                  "¡Nadie me invitó, pero vengo a dejar mi regalo!",
                  ["¡Gracias por invitarme a esta linda fiesta!", "¡Les traigo un pastel de cumpleaños!", "¡Vengo a bailar con todos ustedes!"]),
        emoticono("bella_princesa_huso",
                  "La princesa de quince años, con vestido rosa, en lo alto de una torre, mirando con curiosidad a una anciana que hila con un huso.",
                  "¿Qué es esa cosa que da vueltas tan rápido?",
                  ["¡Qué rico huele el pastel del desayuno!", "¡Hoy iré a cabalgar por el bosque!", "¡Tengo mucho frío, cerremos las ventanas!"]),
    ],
    imagen_pixelada=[
        pixelada("bella_huso",
                 "Un huso de madera con un poco de hilo blanco enrollado, apoyado sobre una rueca antigua, en una habitación de piedra.",
                 "El huso", ["Una varita mágica", "Una aguja de coser", "Un peine de plata", "Una cuchara"]),
        pixelada("bella_castillo_espinas",
                 "Un castillo de piedra con torres, casi oculto por un denso seto de ramas espinosas con algunas rosas blancas.",
                 "El castillo cubierto de espinas", ["Una torre de hielo", "Un palacio de oro", "Una casa de campo", "Un faro"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 800,
            "La princesa se pinchó el dedo con el huso de una anciana, en lo alto de una torre.",
            "La imagen contradictoria muestra a la princesa pinchándose el dedo con un cactus en medio del desierto.",
            [("bella_torre_alta", "Torre alta de piedra", "Una torre alta de piedra con una pequeña puerta y una escalera de caracol visible por la ventana."),
             ("bella_anciana_huso", "Anciana hilando", "Una anciana con pañuelo azul hilando con un huso junto a una rueca, en un cuarto de la torre."),
             ("bella_princesa_dedo", "Princesa sorprendida", "La princesa mirando su dedo con cara de sorpresa dentro del cuarto de la torre.")],
            ("bella_princesa_cactus", "Princesa y un cactus", "La princesa pinchándose el dedo con un cactus grande en medio de un desierto soleado.")),
        contradiccion(2, 810,
            "Cuando el castillo se durmió, creció a su alrededor un enorme seto de espinas y rosas.",
            "La imagen contradictoria muestra el castillo rodeado de arena y palmeras en una isla tropical, sin espinas.",
            [("bella_seto_rosas", "Seto de espinas y rosas", "Un gigantesco seto de ramas con espinas y rosas blancas que rodea un castillo."),
             ("bella_castillo_cubierto", "Castillo medio cubierto", "Un castillo con las torres asomando sobre una maraña espesa de ramas con espinas."),
             ("bella_rosas_blancas", "Rosas con espinas", "Primer plano de rosas blancas con tallos de largas espinas.")],
            ("bella_castillo_isla", "Castillo en isla tropical", "Un castillo rodeado de arena dorada y palmeras en una isla tropical con mar turquesa.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La maldición", [
            "Nace la princesa y el rey organiza una gran fiesta con doce hadas.",
            "Un hada no invitada llega enojada y lanza una maldición.",
            "Otra hada suaviza el hechizo: la princesa dormirá cien años en lugar de morir.",
            "El rey ordena quemar todos los husos del reino.",
            "A los quince años, la princesa encuentra en una torre a una anciana que hila."]),
        reconstruccion(2, "El sueño de cien años", [
            "La princesa se pincha el dedo con el huso y cae dormida.",
            "Todo el castillo se queda dormido junto a ella.",
            "Alrededor del castillo crece un enorme seto de espinas.",
            "Después de cien años, un príncipe llega y las espinas se convierten en flores.",
            "El príncipe besa a la princesa y todos despiertan."]),
    ],
    completa_dialogo=[
        completa(1, "A los quince años, la princesa se pinchó el dedo con un", ".", "huso", ["clavo", "cuchillo", "espejo"]),
        completa(2, "La princesa y todo el castillo durmieron durante cien", ".", "años", ["días", "noches", "meses"]),
    ],
    testigo_ocular=[
        testigo(1, "La torre del huso", "bella_cuarto_torre",
                "Cuarto circular al final de una escalera de caracol en una torre; una anciana con pañuelo azul sentada junto a una rueca con un huso; en la pequeña ventana, una paloma blanca; en la puerta, una llave oxidada en la cerradura; telarañas en las esquinas.",
                [("¿De qué color era el pañuelo de la anciana?", "Azul", ["Rojo", "Verde", "Negro"]),
                 ("¿Qué ave estaba en la ventana?", "Una paloma blanca", ["Un cuervo", "Un búho", "Un loro"]),
                 ("¿Qué había en la cerradura de la puerta?", "Una llave oxidada", ["Una cinta roja", "Un candado dorado", "Una campanilla"])]),
        testigo(2, "El castillo dormido", "bella_salon_dormido",
                "Gran salón con todos dormidos: un rey en su trono con la corona torcida; una cocinera con una cuchara de madera, dormida junto a una olla; un perro dormido bajo la mesa; cortinas amarillas en las ventanas.",
                [("¿Dónde dormía el rey?", "En su trono", ["En la cama", "En el suelo", "En una silla del jardín"]),
                 ("¿Qué sostenía la cocinera?", "Una cuchara de madera", ["Un cuchillo", "Un plato", "Una escoba"]),
                 ("¿Qué animal dormía bajo la mesa?", "Un perro", ["Un gato", "Un conejo", "Un loro"])]),
    ],
    cazador_intrusos=[
        cazador(1, "La torre de la princesa",
                "En lo alto de la torre había un huso de hilar, una cama de madera y una vieja llave oxidada.",
                "bella-torre-bg", "Interior de una torre de piedra con una pequeña ventana, suelo de madera y telarañas suaves; espacio libre para 6 objetos.",
                [new("huso", "Huso de hilar", "Huso de madera con hilo blanco enrollado, fondo transparente."),
                 lib("cama-madera", "Cama de madera"),
                 new("llave-oxidada", "Llave oxidada", "Llave antigua de hierro oxidada, fondo transparente."),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("lampara-led", "Lámpara LED", True),
                 lib("microondas", "Microondas", True)]),
        cazador(2, "El jardín de espinas",
                "Alrededor del castillo dormido crecía un rosal con espinas, lleno de rosas, y en la entrada brillaba la corona del rey.",
                "bella-jardin-bg", "Jardín frente a un castillo dormido, con pasto y neblina suave al atardecer; espacio libre para 6 objetos.",
                [new("rosal-espinas", "Rosal con espinas", "Rosal con ramas de espinas largas y rosas blancas, fondo transparente."),
                 lib("flores", "Rosas"),
                 lib("corona-rey", "Corona del rey"),
                 lib("semaforo", "Semáforo", True),
                 lib("patineta", "Patineta eléctrica", True),
                 lib("consola", "Consola de videojuegos", True)]),
    ],
    busca_imagen=[
        busca(1, "La Bella Durmiente",
              "En lo alto de la torre, junto a la rueca de la anciana, un huso de madera esperaba a la princesa.",
              "Huso", "bella-torre-busca",
              "Cuarto de una torre con una anciana sentada junto a una rueca. En la parte izquierda, un huso de madera alto con hilo blanco, de color algo más claro que la rueca y con contorno marcado. Escena muy recargada: el cuarto está lleno de ruecas, telarañas, canastas con hilos, ovillos, baúles y cortinas viejas.",
              (30, 15, 25, 60)),
        busca(2, "La Bella Durmiente",
              "Entre las espinas del seto, asomaba una rosa blanca que parecía guardar el secreto del castillo.",
              "Rosa blanca", "bella-seto-busca",
              "Seto de espinas frente a un castillo dormido. En la parte central-derecha, una rosa blanca entre las ramas, que destaca levemente por su blancura frente a las espinas.",
              (28, 55, 32, 31.25)),
    ],
    comics_desordenados=[
        comic(1, "El hechizo", "bella", 1, [
            "El rey y la reina celebran el nacimiento de la princesa en un gran salón con doce hadas.",
            "Un hada vestida de negro entra al salón con gesto furioso.",
            "El hada lanza la maldición con su varita, mientras todos miran asustados.",
            "Otra hada se acerca a la cuna y suaviza el hechizo."]),
        comic(2, "El sueño", "bella", 5, [
            "La princesa sube la escalera de la torre y encuentra a la anciana hilando.",
            "La princesa toca el huso y cae dormida sobre una cama.",
            "El castillo duerme y un seto de espinas lo cubre.",
            "Cien años después, un príncipe llega ante las rosas floridas del castillo."]),
    ],
)

# ============================================================================
# 2. EL TRAJE NUEVO DEL EMPERADOR (Andersen)
# ============================================================================
add_book(
    "El traje nuevo del emperador", ["traje nuevo", "emperador"],
    rafaga_vf=[
        rafaga("Había un emperador al que le gustaba tanto la ropa nueva que gastaba todo su dinero en vestirse. Un día llegaron dos estafadores que dijeron ser tejedores.", [
            ("El emperador gastaba mucho dinero en ropa.", True),
            ("Los dos hombres dijeron ser médicos.", False),
            ("Los estafadores dijeron ser tejedores.", True)]),
        rafaga("Los estafadores aseguraron que su tela era invisible para los tontos. Pidieron seda e hilos de oro, pero se los guardaron en sus bolsos.", [
            ("La tela era invisible para los tontos.", True),
            ("Pidieron seda e hilos de oro.", True),
            ("Usaron todo el oro para hacer el traje.", False)]),
    ],
    emoticono_dialogo=[
        emoticono("traje_emperador_telares",
                  "Un emperador con corona, mirando asombrado dos telares vacíos con la boca abierta, junto a dos tejedores que fingen tejer.",
                  "¡No veo nada! ¿Seré yo un tonto?",
                  ["¡Qué hambre tengo, vamos a comer!", "¡Qué lindo es mi jardín!", "¡Estos telares están llenos de lana azul!"]),
        emoticono("traje_nino_grita",
                  "Un niño pequeño entre la multitud, señalando con el dedo a un emperador que desfila en ropa interior blanca bajo un palio, mientras la gente mira.",
                  "¡Pero si el emperador no lleva nada puesto!",
                  ["¡Qué traje tan hermoso lleva el emperador!", "¡Mamá, quiero un helado!", "¡Viva el emperador, qué corona tan grande!"]),
    ],
    imagen_pixelada=[
        pixelada("traje_emperador",
                 "Un emperador con corona dorada y capa roja con ribetes blancos, de pie con gesto orgulloso en un salón de palacio.",
                 "El emperador", ["El mago", "El soldado", "El tejedor", "El ministro"]),
        pixelada("traje_telar_vacio",
                 "Un telar de madera con hilos dorados tensos pero sin tela, con dos tejedores fingiendo trabajar a los lados.",
                 "El telar vacío", ["Un arpa", "Una cama", "Una ventana", "Un órgano"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 820,
            "Los estafadores pidieron seda e hilos de oro para tejer la tela invisible.",
            "La imagen contradictoria muestra a los estafadores recibiendo cubos de pintura y brochas.",
            [("traje_carrete_oro", "Carrete de hilo de oro", "Un carrete de hilo dorado brillante sobre una mesa de madera."),
             ("traje_rollos_seda", "Rollos de seda", "Tres rollos de tela de seda brillante de colores sobre una mesa."),
             ("traje_estafadores_bolsa", "Estafadores guardando el oro", "Dos hombres guardando a escondidas hilo de oro en una bolsa, mirando de reojo.")],
            ("traje_estafadores_pintura", "Estafadores con pintura", "Dos hombres recibiendo cubos de pintura y brochas de un sirviente.")),
        contradiccion(2, 830,
            "El emperador desfiló por la ciudad bajo un palio, acompañado de sus ayudantes.",
            "La imagen contradictoria muestra al emperador desfilando solo, montado en un monopatín.",
            [("traje_palio", "Palio azul y dorado", "Un palio azul con bordes dorados sostenido por cuatro hombres en una calle."),
             ("traje_ayudantes", "Ayudantes agachados", "Dos ayudantes agachados con las manos levantadas, fingiendo sostener una cola de tela."),
             ("traje_multitud", "Multitud asombrada", "Una multitud en una calle con banderas rojas, mirando con asombro hacia el desfile.")],
            ("traje_emperador_monopatin", "Emperador en monopatín", "Un emperador con corona y capa, solo, montado en un monopatín en una calle vacía.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "Los falsos tejedores", [
            "El emperador, a quien le encantan los trajes, contrata a dos supuestos tejedores.",
            "Los estafadores montan telares vacíos y piden seda e hilos de oro.",
            "El viejo ministro visita el taller, no ve nada y finge admirar la tela.",
            "Otro funcionario hace lo mismo para no pasar por tonto.",
            "Por fin, el propio emperador visita el taller y también finge ver la tela."]),
        reconstruccion(2, "El desfile", [
            "Los estafadores simulan cortar la tela y coser con agujas sin hilo.",
            "Los ayudantes del emperador lo visten con el traje invisible.",
            "El emperador sale a desfilar por la ciudad bajo un palio.",
            "Un niño grita que el emperador no lleva nada puesto.",
            "El pueblo repite lo que dijo el niño, pero el emperador sigue desfilando con orgullo."]),
    ],
    completa_dialogo=[
        completa(1, "Los estafadores dijeron que la tela era invisible para los", ".", "tontos", ["niños", "ancianos", "sirvientes"]),
        completa(2, "—¡Pero si el emperador no lleva nada", "! —gritó el niño.", "puesto", ["dicho", "escrito", "pintado"]),
    ],
    testigo_ocular=[
        testigo(1, "El taller de los tejedores", "traje_taller_interior",
                "Taller con dos telares de madera vacíos; dos hombres con gorros rojos fingiendo tejer; sobre una mesa, unas tijeras grandes y un carrete de hilo dorado; tres velas encendidas; una ventana con luna.",
                [("¿Cuántos telares había?", "Dos", ["Uno", "Tres", "Cuatro"]),
                 ("¿De qué color eran los gorros de los tejedores?", "Rojos", ["Azules", "Verdes", "Negros"]),
                 ("¿Cuántas velas estaban encendidas?", "Tres", ["Dos", "Cinco", "Una"])]),
        testigo(2, "El desfile del emperador", "traje_calle_desfile",
                "Calle de una ciudad con gente a ambos lados; el emperador con corona dorada caminando en ropa interior blanca; dos ayudantes detrás con las manos levantadas; un palio azul con bordes dorados sostenido por cuatro hombres; un niño señalando; banderas rojas en los balcones.",
                [("¿De qué color era el palio?", "Azul", ["Rojo", "Verde", "Amarillo"]),
                 ("¿Cuántos hombres sostenían el palio?", "Cuatro", ["Dos", "Tres", "Seis"]),
                 ("¿De qué color eran las banderas de los balcones?", "Rojas", ["Verdes", "Blancas", "Azules"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El taller de los tejedores",
                "En el taller de los falsos tejedores había un telar de madera, unas tijeras grandes y un carrete de hilo dorado.",
                "traje-taller-bg", "Taller antiguo con paredes de piedra, una mesa de madera y una ventana con luz cálida; espacio libre para 6 objetos.",
                [new("telar", "Telar de madera", "Telar de madera antiguo con hilos tensos, fondo transparente."),
                 new("tijeras", "Tijeras grandes", "Tijeras grandes de sastre con mango negro, fondo transparente."),
                 new("hilo-dorado", "Carrete de hilo dorado", "Carrete de hilo dorado brillante, fondo transparente."),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("laptop", "Computadora portátil", True),
                 lib("microondas", "Microondas", True)]),
        cazador(2, "El palacio del emperador",
                "En el palacio del emperador había una corona, una capa real y un cofre de oro.",
                "traje-palacio-bg", "Salón de un palacio con columnas, alfombra roja y cortinas doradas; espacio libre para 6 objetos.",
                [lib("corona-rey", "Corona del emperador"),
                 lib("capa", "Capa real"),
                 lib("cofre", "Cofre de oro"),
                 lib("tv", "Televisor de pantalla plana", True),
                 lib("calculadora", "Calculadora solar", True),
                 lib("audifonos", "Audífonos inalámbricos", True)]),
    ],
    busca_imagen=[
        busca(1, "El traje nuevo del emperador",
              "Sobre la mesa del taller, entre carretes de hilo, brillaban unas tijeras de plata del estafador.",
              "Tijeras", "traje-taller-busca",
              "Taller con una mesa de madera llena de carretes de hilo. En la parte inferior derecha, unas tijeras grandes de plata, con un destello leve que las distingue de la madera. Escena muy recargada: la mesa tiene muchos carretes de hilo, telas, agujas, cintas, otras tijeras y rollos de seda.",
              (55, 45, 50, 30)),
        busca(2, "El traje nuevo del emperador",
              "Entre la multitud del desfile, un niño pequeño señalaba con el dedo al emperador.",
              "Niño que señala", "traje-desfile-busca",
              "Calle con algunas personas mirando un desfile. En la parte izquierda, un niño pequeño señalando con el dedo, algo más iluminado y con contorno más marcado que el resto.",
              (40, 12, 20, 50)),
    ],
    comics_desordenados=[
        comic(1, "Los falsos tejedores", "traje", 1, [
            "Dos hombres llegan a la ciudad con bolsos y se presentan ante el emperador.",
            "Los tejedores montan un telar vacío y reciben seda e hilos de oro.",
            "Un viejo ministro mira el telar vacío con cara de sorpresa.",
            "El emperador visita el taller y finge ver la tela, con los tejedores a su lado."]),
        comic(2, "El desfile", "traje", 5, [
            "Los ayudantes del emperador lo visten con un traje invisible frente a un espejo.",
            "El emperador camina bajo un palio por la ciudad, con ropa interior blanca.",
            "Un niño señala al emperador entre la multitud.",
            "El pueblo ríe y el emperador sigue desfilando muy erguido."]),
    ],
)

# ============================================================================
# 3. EL SOLDADITO DE PLOMO (Andersen)
# ============================================================================
add_book(
    "El soldadito de plomo", ["soldadito de plomo", "soldadito"],
    rafaga_vf=[
        rafaga("Un niño recibió por su cumpleaños veinticinco soldaditos de plomo, hechos de una vieja cuchara. Uno de ellos solo tenía una pierna, porque no alcanzó el plomo para terminarlo.", [
            ("Los soldaditos eran de plomo.", True),
            ("Eran veinte soldaditos.", False),
            ("Uno de ellos tenía una sola pierna.", True)]),
        rafaga("Sobre la mesa había un hermoso castillo de papel. En la puerta estaba una bailarina de papel, que levantaba una pierna tan alto que el soldadito creyó que ella también tenía una sola pierna.", [
            ("La bailarina era de papel.", True),
            ("El castillo era de madera.", False),
            ("La bailarina levantaba una pierna.", True)]),
    ],
    emoticono_dialogo=[
        emoticono("soldadito_bailarina",
                  "Un soldadito de plomo de pie sobre una sola pierna, con uniforme rojo y azul, mirando enamorado a una bailarina de papel con vestido blanco y cinta azul frente a un castillo de papel.",
                  "¡Qué hermosa bailarina! Ella también tiene una sola pierna.",
                  ["¡Quiero salir a jugar a la calle!", "¡Tengo mucho sueño, me iré a dormir!", "¡Me gustaría ser un pirata del mar!"]),
        emoticono("soldadito_duende",
                  "Un duende negro que sale de una cajita de rapé con cara enfadada, mirando a un soldadito de plomo sobre una mesa de juguetes, de noche.",
                  "¡No mires tanto a la bailarina!",
                  ["¡Bienvenido a mi fiesta, soldadito!", "¡Te regalaré mi caja de música!", "¡Ya es hora de ir a nadar!"]),
    ],
    imagen_pixelada=[
        pixelada("soldadito_personaje",
                 "Un soldadito de plomo de una sola pierna, con uniforme rojo y azul y un fusil al hombro, sobre una mesa de madera.",
                 "El soldadito de plomo", ["Un muñeco de nieve", "Un cascanueces", "Un guardia real", "Un robot"]),
        pixelada("soldadito_bailarina_papel",
                 "Una bailarina de papel con vestido blanco, una cinta azul y una lentejuela dorada, de pie sobre una pierna con la otra levantada.",
                 "La bailarina de papel", ["Una muñeca de trapo", "Un hada", "Una princesa", "Una marioneta"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 840,
            "El soldadito de plomo viajó por el canal en un barquito hecho de papel.",
            "La imagen contradictoria muestra al soldadito en un barco pirata de metal.",
            [("soldadito_ninos_barquito", "Niños dejando el barquito", "Dos niños con impermeables amarillos dejando un barquito de papel sobre el agua de un canal."),
             ("soldadito_barquito_flota", "Barquito flotando", "Un barquito de papel blanco con el soldadito de pie, flotando en una acequia de piedra."),
             ("soldadito_gesto_firme", "Soldadito con gesto firme", "El soldadito de pie en el barquito, mirando al frente con gesto firme.")],
            ("soldadito_barco_pirata", "Barco pirata de metal", "El soldadito de plomo a bordo de un barco pirata de metal en un canal.")),
        contradiccion(2, 850,
            "La bailarina de papel llevaba un vestido blanco con una cinta azul y una lentejuela brillante.",
            "La imagen contradictoria muestra a una bailarina con vestido rojo y sombrero de copa.",
            [("soldadito_bailarina_pierna", "Bailarina sobre una pierna", "Una bailarina de papel con vestido blanco equilibrada sobre una pierna."),
             ("soldadito_cinta_azul", "Cinta azul", "Primer plano de una cinta azul brillante sobre un vestido blanco de papel."),
             ("soldadito_lentejuela", "Lentejuela dorada", "Primer plano de una pequeña lentejuela dorada brillante sobre papel blanco.")],
            ("soldadito_bailarina_roja", "Bailarina de rojo", "Una bailarina de papel con vestido rojo y sombrero de copa negro.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "El soldadito y la bailarina", [
            "En su cumpleaños, un niño recibe veinticinco soldaditos de plomo.",
            "El soldadito de una sola pierna se enamora de una bailarina de papel.",
            "El duende de la cajita le dice que no la mire.",
            "A la mañana siguiente, el soldadito cae por la ventana a la calle.",
            "Dos niños lo ponen en un barquito de papel y lo dejan en el agua de la acequia."]),
        reconstruccion(2, "El viaje del soldadito", [
            "El barquito entra a una alcantarilla donde una rata le pide su pasaporte.",
            "La corriente lo lleva hasta una cascada y el barquito se hunde.",
            "Un gran pez se lo traga.",
            "Pescan al pez y lo abren en una cocina; el soldadito aparece en la misma casa.",
            "El niño lo arroja a la estufa y el soldadito se derrite en forma de corazón."]),
    ],
    completa_dialogo=[
        completa(1, "El soldadito tenía una sola", "porque no alcanzó el plomo.", "pierna", ["oreja", "manga", "espada"]),
        completa(2, "Al final, el soldadito se derritió y quedó convertido en un pequeño", "de plomo.", "corazón", ["anillo", "botón", "soldado"]),
    ],
    testigo_ocular=[
        testigo(1, "La mesa de juguetes", "soldadito_mesa_juguetes",
                "Una mesa de juguetes: un castillo de papel blanco con dos torres; frente a la puerta una bailarina de papel con una pierna levantada, cinta azul y lentejuela; al lado, un espejo que parece un lago, con cisnes de cera.",
                [("¿Cuántas torres tenía el castillo?", "Dos", ["Una", "Tres", "Cuatro"]),
                 ("¿De qué color era la cinta de la bailarina?", "Azul", ["Roja", "Verde", "Amarilla"]),
                 ("¿Qué parecía un lago junto al castillo?", "Un espejo con cisnes de cera", ["Una bañera", "Un plato con agua", "Una alfombra azul"])]),
        testigo(2, "El canal de la ciudad", "soldadito_canal_lluvia",
                "Una acequia de piedra después de la lluvia; un barquito de papel blanco con el soldadito de pie; dos niños en la orilla con impermeables amarillos; una rata asomándose de un agujero; un farol de hierro.",
                [("¿De qué color eran los impermeables de los niños?", "Amarillos", ["Rojos", "Azules", "Verdes"]),
                 ("¿Qué animal asomaba por el agujero?", "Una rata", ["Un gato", "Un sapo", "Un pájaro"]),
                 ("¿De qué color era el barquito?", "Blanco", ["Rojo", "Azul", "Negro"])]),
    ],
    cazador_intrusos=[
        cazador(1, "La mesa del cuarto de juguetes",
                "Sobre la mesa estaban el soldadito de plomo, el castillo de papel y la bailarina de una sola pierna.",
                "soldadito-cuarto-bg", "Cuarto de juguetes de un niño con una mesa de madera, alfombra y una ventana; espacio libre para 6 objetos.",
                [new("soldadito-plomo", "Soldadito de plomo", "Soldadito de plomo de una sola pierna, uniforme rojo y azul, fondo transparente."),
                 new("castillo-papel", "Castillo de papel", "Castillo de papel blanco con dos torres y una puerta, fondo transparente."),
                 new("bailarina-papel", "Bailarina de papel", "Bailarina de papel sobre una pierna con cinta azul, fondo transparente."),
                 lib("consola", "Consola de videojuegos", True),
                 lib("laptop", "Computadora portátil", True),
                 lib("microondas", "Microondas", True)]),
        cazador(2, "El viaje por el canal",
                "En el canal navegaba un barquito de papel, una rata observaba desde un agujero y un gran pez esperaba bajo el agua.",
                "soldadito-canal-bg", "Canal de piedra de una ciudad antigua después de la lluvia, con agua marrón y farolas; espacio libre para 6 objetos.",
                [new("barquito-papel", "Barquito de papel", "Barquito de papel blanco visto de costado, fondo transparente."),
                 new("pez-grande", "Gran pez", "Pez grande y gris con la boca abierta, fondo transparente."),
                 new("rata", "Rata", "Rata gris de cola larga, de perfil, fondo transparente."),
                 lib("nave-espacial", "Nave espacial", True),
                 lib("submarino", "Submarino", True),
                 lib("patineta", "Patineta eléctrica", True)]),
    ],
    busca_imagen=[
        busca(1, "El soldadito de plomo",
              "Junto al castillo de papel, sobre la mesa de juguetes, una bailarina equilibrada en una pierna esperaba al soldadito.",
              "Bailarina de papel", "soldadito-mesa-busca",
              "Mesa de juguetes con un castillo de papel. En la parte central, una bailarina de papel grande sobre una pierna, más clara que el castillo y con una cinta de color apagado. Escena muy recargada: la mesa está llena de soldaditos de plomo, muñecas, cajas, bloques, un castillo de papel y otros juguetes.",
              (28, 35, 30, 50)),
        busca(2, "El soldadito de plomo",
              "Al borde de la acequia, entre las piedras mojadas, flotaba un pequeño barquito de papel.",
              "Barquito de papel", "soldadito-acequia-busca",
              "Acequia de piedra con agua oscura. En la parte inferior derecha, un barquito de papel blanco flotando, más claro que el agua y con contorno marcado.",
              (62, 40, 50, 20)),
    ],
    comics_desordenados=[
        comic(1, "El soldadito cae", "soldadito", 1, [
            "Un niño abre una caja con veinticinco soldaditos de plomo en su cumpleaños.",
            "El soldadito de una sola pierna mira a la bailarina de papel frente al castillo.",
            "De noche, el duende negro sale de su cajita y mira al soldadito con enojo.",
            "El soldadito cae por la ventana abierta hacia la calle."]),
        comic(2, "El viaje", "soldadito", 5, [
            "Dos niños ponen al soldadito en un barquito de papel sobre un canal de lluvia.",
            "El barquito pasa por una alcantarilla oscura donde una rata lo mira.",
            "Un gran pez traga al soldadito en el agua.",
            "En la estufa, el soldadito se derrite en forma de pequeño corazón, y a su lado queda la lentejuela de la bailarina."]),
    ],
)

# ============================================================================
# 4. RAPUNZEL (Grimm)
# ============================================================================
add_book(
    "Rapunzel", ["Rapunzel"],
    rafaga_vf=[
        rafaga("Un matrimonio vivía junto al jardín de una bruja. La mujer deseó tanto comer rapónchigos del jardín que su esposo los robó.", [
            ("La mujer deseaba comer rapónchigos.", True),
            ("El esposo compró un kilo de rapónchigos a la bruja.", False),
            ("El matrimonio vivía junto al jardín de una bruja.", True)]),
        rafaga("Cuando Rapunzel cumplió doce años, la bruja la encerró en una torre sin puertas y con una sola ventana. Para subir, gritaba: «Rapunzel, Rapunzel, suéltame tu cabello».", [
            ("La torre tenía una sola ventana.", True),
            ("La torre tenía una gran puerta de hierro.", False),
            ("La bruja subía trepando por el cabello de Rapunzel.", True)]),
    ],
    emoticono_dialogo=[
        emoticono("rapunzel_canta",
                  "Rapunzel con una larga trenza dorada que cae por la ventana de una torre alta, cantando con los ojos cerrados, rodeada de pájaros.",
                  "¡Qué bonito es cantar en lo alto de mi torre!",
                  ["¡Tengo tanta hambre que comeré lechugas!", "¡Voy a salir por la puerta a pasear!", "¡Quiero bañarme en el río!"]),
        emoticono("rapunzel_bruja_llama",
                  "Una bruja con capa negra al pie de una torre sin puertas, con las manos junto a la boca, llamando hacia una ventana en lo alto.",
                  "¡Rapunzel, Rapunzel, suéltame tu cabello!",
                  ["¡Hola, vengo a traerte una puerta!", "¡Rapunzel, ven a jugar al jardín!", "¡Qué bonita es la luna esta noche!"]),
    ],
    imagen_pixelada=[
        pixelada("rapunzel_personaje",
                 "Rapunzel, joven de cabello dorado larguísimo con una trenza que cae hasta el suelo, vestida con un vestido sencillo, asomada a una ventana.",
                 "Rapunzel", ["La bruja", "La princesa", "La reina", "El hada"]),
        pixelada("rapunzel_torre",
                 "Una torre alta de piedra gris sin puertas, con una sola ventana pequeña en lo alto, en medio de un bosque.",
                 "La torre sin puertas", ["Un faro", "Un castillo", "Un molino", "Un campanario"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 860,
            "Rapunzel tenía el cabello larguísimo y dorado, y lo dejaba caer por la ventana de la torre.",
            "La imagen contradictoria muestra a Rapunzel con el cabello corto y negro, asomada a la ventana.",
            [("rapunzel_trenza_ventana", "Trenza dorada por la ventana", "Una larguísima trenza dorada cayendo por la ventana de una torre hasta el suelo."),
             ("rapunzel_peinando", "Rapunzel arreglando su cabello", "Rapunzel sentada peinando su cabello dorado larguísimo que cubre el suelo del cuarto."),
             ("rapunzel_trenza_gancho", "Trenza atada al gancho", "Primer plano de una trenza dorada larga atada a un gancho de la ventana.")],
            ("rapunzel_pelo_corto", "Rapunzel de pelo corto", "Rapunzel con el cabello corto y negro, asomada a la ventana de una torre.")),
        contradiccion(2, 870,
            "La torre de Rapunzel no tenía puertas, solo una pequeña ventana en lo alto.",
            "La imagen contradictoria muestra una torre con una gran puerta roja y escaleras en la entrada.",
            [("rapunzel_torre_sin_puerta", "Torre sin puertas", "Una torre alta de piedra, sin ninguna puerta, rodeada de árboles."),
             ("rapunzel_ventana_alta", "Ventana en lo alto", "Una pequeña ventana en lo más alto de una torre de piedra gris."),
             ("rapunzel_hiedra_torre", "Hiedra en la torre", "Una torre cubierta de hiedra en su parte baja, sin puerta visible.")],
            ("rapunzel_torre_puerta_roja", "Torre con puerta roja", "Una torre de piedra con una gran puerta roja y una escalera en la entrada.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La torre", [
            "Un matrimonio espera un hijo, y la mujer desea comer rapónchigos del jardín de una bruja.",
            "El marido roba los rapónchigos y la bruja lo descubre.",
            "A cambio de perdonarlo, la bruja se queda con la niña, a quien llama Rapunzel.",
            "Cuando cumple doce años, la bruja encierra a Rapunzel en una torre sin puertas.",
            "La bruja sube cada día a la torre trepando por el largo cabello de Rapunzel."]),
        reconstruccion(2, "El príncipe", [
            "Un príncipe escucha cantar a Rapunzel mientras pasea por el bosque.",
            "Escondido, ve a la bruja subir por el cabello y repite sus palabras.",
            "Rapunzel y el príncipe se enamoran y planean escapar.",
            "La bruja se entera, corta el cabello de Rapunzel y la envía lejos.",
            "El príncipe cae entre espinas y queda ciego, pero las lágrimas de Rapunzel lo curan al reencontrarse."]),
    ],
    completa_dialogo=[
        completa(1, "—Rapunzel, Rapunzel, suéltame tu", "—gritaba la bruja.", "cabello", ["cuerda", "escalera", "pañuelo"]),
        completa(2, "La torre en la que vivía Rapunzel no tenía", "sino una pequeña ventana.", "puertas", ["techo", "cimientos", "ladrillos"]),
    ],
    testigo_ocular=[
        testigo(1, "La torre de Rapunzel", "rapunzel_torre_bosque",
                "Una torre alta de piedra gris en un bosque, sin puertas; en lo alto una ventana pequeña con cortinas rosadas; una trenza dorada que cuelga hasta el suelo; una bruja con capa negra y sombrero puntiagudo; tres pájaros azules sobre el tejado.",
                [("¿De qué color eran las cortinas de la ventana?", "Rosadas", ["Verdes", "Azules", "Blancas"]),
                 ("¿Cuántos pájaros azules había sobre el tejado?", "Tres", ["Uno", "Dos", "Cinco"]),
                 ("¿Qué llevaba la bruja en la cabeza?", "Un sombrero puntiagudo", ["Una corona", "Un pañuelo", "Nada"])]),
        testigo(2, "El jardín de la bruja", "rapunzel_jardin_bruja",
                "Un jardín rodeado por un alto muro de piedra; hileras de rapónchigos de hojas verdes; un hombre asomado sobre el muro con una cesta en la mano.",
                [("¿Qué sostenía el hombre?", "Una cesta", ["Un saco", "Una pala", "Un farol"]),
                 ("¿De qué era el muro?", "Piedra", ["Madera", "Ladrillo rojo", "Arbustos"]),
                 ("¿Qué había cultivado en hileras?", "Rapónchigos de hojas verdes", ["Tomates rojos", "Zanahorias", "Calabazas"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El jardín de la bruja",
                "En el jardín de la bruja crecían rapónchigos y flores, y colgaba su sombrero puntiagudo de un clavo.",
                "rapunzel-jardin-bg", "Jardín cercado por un muro de piedra, con tierra labrada y cielo claro; espacio libre para 6 objetos.",
                [new("raponchigos", "Rapónchigos", "Manojo de rapónchigos con hojas verdes y raíz blanca, fondo transparente."),
                 lib("flores", "Flores del jardín"),
                 new("sombrero-bruja", "Sombrero de bruja", "Sombrero negro puntiagudo de bruja con una cinta morada, fondo transparente."),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("semaforo", "Semáforo", True),
                 lib("microondas", "Microondas", True)]),
        cazador(2, "La torre de Rapunzel",
                "En la torre de Rapunzel había una larga trenza dorada, unas tijeras y una cama de madera.",
                "rapunzel-cuarto-bg", "Cuarto circular de una torre de piedra con una ventana pequeña y suelo de madera; espacio libre para 6 objetos.",
                [new("trenza-dorada", "Trenza dorada", "Larga trenza dorada enrollada, con un lazo rosado, fondo transparente."),
                 lib("tijeras", "Tijeras"),
                 lib("cama-madera", "Cama de madera"),
                 lib("tv", "Televisor de pantalla plana", True),
                 lib("laptop", "Computadora portátil", True),
                 lib("nave-espacial", "Nave espacial", True)]),
    ],
    busca_imagen=[
        busca(1, "Rapunzel",
              "En lo alto de la torre, una pequeña ventana dejaba colgar una larga trenza dorada.",
              "Trenza dorada", "rapunzel-torre-busca",
              "Torre alta de piedra en un bosque. En el centro, una trenza dorada larguísima que cuelga desde la ventana hasta el pie de la torre, con un tono apagado más claro que la piedra. Escena muy recargada: alrededor de la torre hay muchas enredaderas, pájaros, árboles, flores, ramas y una trenza falsa de hiedra.",
              (10, 45, 25, 60)),
        busca(2, "Rapunzel",
              "Cerca del muro de piedra, entre las hileras del huerto, brillaban las hojas verdes de los rapónchigos.",
              "Rapónchigos", "rapunzel-jardin-busca",
              "Jardín con un muro de piedra y varias verduras. En la parte inferior izquierda, un grupo de rapónchigos de hojas verdes apagadas que destaca levemente entre las demás plantas.",
              (62, 12, 50, 20)),
    ],
    comics_desordenados=[
        comic(1, "La promesa", "rapunzel", 1, [
            "Una mujer embarazada mira por la ventana el jardín de la bruja lleno de rapónchigos.",
            "Su esposo salta el muro del jardín y recoge rapónchigos en una cesta.",
            "La bruja aparece enfurecida con capa negra frente al hombre.",
            "La bruja se lleva a una bebé en brazos mientras los padres lloran."]),
        comic(2, "La trenza", "rapunzel", 5, [
            "Rapunzel, adolescente, canta en la ventana de la torre con su largo cabello.",
            "La bruja sube a la torre trepando por la trenza dorada.",
            "Un príncipe escondido entre los árboles observa la escena.",
            "El príncipe sube por la trenza y Rapunzel lo recibe sorprendida."]),
    ],
)

# ============================================================================
# 5. EL GIGANTE EGOÍSTA (Wilde)
# ============================================================================
add_book(
    "El gigante egoísta", ["gigante egoísta", "gigante"],
    rafaga_vf=[
        rafaga("Los niños jugaban todas las tardes en el hermoso jardín del gigante, lleno de suave césped y de duraznos en flor. Cuando el gigante regresó, después de siete años, los echó de allí.", [
            ("Los niños jugaban en el jardín del gigante.", True),
            ("El gigante regresó después de siete años.", True),
            ("El gigante invitó a los niños a quedarse.", False)]),
        rafaga("El gigante construyó un alto muro y puso un cartel de prohibida la entrada. Entonces la primavera no llegó a su jardín, y solo vivieron allí la Nieve, la Escarcha y el Viento del Norte.", [
            ("El gigante construyó un alto muro.", True),
            ("La primavera llegó pronto al jardín.", False),
            ("En el jardín vivían la Nieve y la Escarcha.", True)]),
    ],
    emoticono_dialogo=[
        emoticono("gigante_enojado",
                  "Un gigante enorme con barba y ropa de abrigo, con el ceño fruncido y el dedo señalando a un grupo de niños asustados en un jardín con flores.",
                  "¿Qué hacen en mi jardín? ¡Fuera de aquí!",
                  ["¡Bienvenidos, niños, pueden jugar todo el día!", "¡Qué lindos duraznos tengo!", "¡Vamos a jugar a la pelota juntos!"]),
        emoticono("gigante_conmovido",
                  "El gigante, de rodillas en un jardín nevado, ayudando con ternura a un niño pequeño a subir a un árbol que empieza a florecer.",
                  "¡Qué egoísta fui! Sin niños no hay primavera.",
                  ["¡Este árbol es mío y nadie lo tocará!", "¡Cerremos el jardín con otro muro más alto!", "¡Prefiero que el invierno dure para siempre!"]),
    ],
    imagen_pixelada=[
        pixelada("gigante_personaje",
                 "Un gigante enorme y barbudo, con ropa de abrigo, de pie en un jardín, mirando hacia abajo con ceño fruncido.",
                 "El gigante", ["El ogro de Cornualles", "El rey", "El leñador", "El mago"]),
        pixelada("gigante_durazno_flor",
                 "Un duraznero cubierto de flores rosadas, con un pajarito posado en una rama, sobre césped verde.",
                 "El árbol florecido", ["Un rosal", "Un pino nevado", "Un manzano rojo", "Un sauce llorón"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 880,
            "El gigante construyó un alto muro alrededor de su jardín y puso un cartel para prohibir la entrada.",
            "La imagen contradictoria muestra al gigante abriendo un portón con un cartel de bienvenida y globos.",
            [("gigante_muro_alto", "Muro alto de piedra", "Un muro alto de piedra gris que rodea un jardín nevado."),
             ("gigante_cartel_prohibido", "Cartel de prohibido", "Un cartel de madera con el dibujo de una mano alzada, clavado en el suelo junto al muro."),
             ("gigante_mira_ventana", "Gigante mirando por la ventana", "El gigante mirando serio por la ventana de su casa hacia el jardín cercado.")],
            ("gigante_bienvenida_globos", "Gigante con globos", "El gigante abriendo un portón con un cartel de bienvenida y globos de colores, sonriendo.")),
        contradiccion(2, 890,
            "Cuando los niños volvieron, el jardín se llenó de flores y de pájaros cantores.",
            "La imagen contradictoria muestra el jardín cubierto de nieve, sin flores, con niños tiritando.",
            [("gigante_ninos_agujero", "Niños entrando por el muro", "Un grupo de niños entrando al jardín por un agujero del muro de piedra."),
             ("gigante_duraznos_flor", "Duraznos en flor", "Varios árboles de durazno cubiertos de flores rosadas."),
             ("gigante_pajaros_rama", "Pájaros cantando", "Tres pájaros pequeños cantando en una rama florecida.")],
            ("gigante_jardin_nevado", "Jardín nevado", "Un jardín cubierto de nieve, sin flores, con niños abrazándose de frío.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "El muro del gigante", [
            "Los niños juegan cada tarde en el hermoso jardín del gigante.",
            "El gigante regresa tras siete años y los echa de su jardín.",
            "Construye un alto muro y coloca un cartel de prohibida la entrada.",
            "La primavera se olvida del jardín y solo llegan la nieve y la escarcha.",
            "Los niños, tristes, rondan el muro porque no tienen dónde jugar."]),
        reconstruccion(2, "La primavera vuelve", [
            "Una mañana, el gigante oye cantar a un pajarillo y mira por la ventana.",
            "Los niños han entrado por un agujero del muro y los árboles florecen.",
            "En un rincón sigue el invierno: un niño pequeño no puede subir al árbol.",
            "El gigante lo ayuda a subir y derriba el muro.",
            "Los niños juegan con el gigante todos los días."]),
    ],
    completa_dialogo=[
        completa(1, "El gigante construyó un alto muro y puso un cartel de prohibida la", ".", "entrada", ["salida", "música", "comida"]),
        completa(2, "Cuando los niños volvieron, la", "llegó por fin al jardín del gigante.", "primavera", ["nieve", "noche", "tormenta"]),
    ],
    testigo_ocular=[
        testigo(1, "El jardín de los niños", "gigante_jardin_primavera",
                "Jardín soleado con césped suave; árboles de durazno con flores rosadas; seis niños jugando; dos pájaros azules en una rama; un banco de madera bajo los árboles.",
                [("¿De qué color eran las flores de los duraznos?", "Rosadas", ["Blancas", "Amarillas", "Rojas"]),
                 ("¿Cuántos pájaros azules había en la rama?", "Dos", ["Uno", "Tres", "Cinco"]),
                 ("¿Qué había bajo los árboles?", "Un banco de madera", ["Una fuente", "Un columpio", "Una casa"])]),
        testigo(2, "El muro del gigante", "gigante_muro_nieve",
                "Un muro alto de piedra gris alrededor de un jardín cubierto de nieve; un cartel de madera con una mano alzada dibujada; tres árboles sin hojas; un niño pequeño con bufanda roja asomado por un agujero del muro.",
                [("¿Qué dibujo tenía el cartel?", "Una mano alzada", ["Una flor", "Un corazón", "Una estrella"]),
                 ("¿De qué color era la bufanda del niño?", "Roja", ["Azul", "Verde", "Amarilla"]),
                 ("¿Cuántos árboles sin hojas había?", "Tres", ["Uno", "Cuatro", "Seis"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El jardín primaveral",
                "En el jardín del gigante florecían duraznos y flores, revoloteaban las mariposas y cantaba un pajarillo.",
                "gigante-primavera-bg", "Jardín soleado con césped verde suave y cielo azul; espacio libre para 6 objetos.",
                [lib("flores", "Flores"),
                 lib("mariposa", "Mariposa"),
                 new("durazno-flor", "Árbol de durazno en flor", "Pequeño duraznero con flores rosadas, fondo transparente."),
                 new("pajarillo", "Pajarillo cantor", "Pajarillo pequeño y azul con el pico abierto, cantando, fondo transparente."),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("semaforo", "Semáforo", True)]),
        cazador(2, "El jardín del invierno",
                "Tras el muro de ladrillos, el jardín quedó cubierto de copos de nieve y con un cartel de prohibido.",
                "gigante-invierno-bg", "Jardín cubierto de nieve con árboles sin hojas y cielo gris; espacio libre para 6 objetos.",
                [lib("ladrillos", "Ladrillos del muro"),
                 new("cartel-prohibido", "Cartel de prohibido", "Cartel de madera con una mano alzada dibujada, fondo transparente."),
                 new("copo-nieve", "Copo de nieve", "Gran copo de nieve de cristal con seis puntas, fondo transparente."),
                 lib("extintor-incendios", "Extintor de incendios", True),
                 lib("microondas", "Microondas", True),
                 lib("consola", "Consola de videojuegos", True)]),
    ],
    busca_imagen=[
        busca(1, "El gigante egoísta",
              "En la rama más baja del durazno, un pajarillo cantaba entre las flores rosadas.",
              "Pajarillo", "gigante-durazno-busca",
              "Jardín en primavera con un gran duraznero florecido. En la parte central-derecha, un pajarillo azul grande posado en una rama, con un color apagado que lo distingue de las flores. Escena muy recargada: el jardín está lleno de flores de durazno, otros pájaros, niños jugando, mariposas, hojas y ramas.",
              (20, 48, 40, 37.5)),
        busca(2, "El gigante egoísta",
              "Al pie del muro de piedra, un pequeño agujero dejaba pasar a los niños al jardín.",
              "Agujero del muro", "gigante-muro-busca",
              "Muro de piedra alto cubierto de nieve. En la parte inferior izquierda, un agujero oscuro en la base del muro, con un borde algo más marcado que las piedras.",
              (58, 10, 32, 31.25)),
    ],
    comics_desordenados=[
        comic(1, "El muro", "gigante", 1, [
            "Los niños juegan felices entre árboles de durazno en flor.",
            "El gigante regresa y mira con enojo a los niños.",
            "El gigante construye un muro alto con piedras.",
            "El gigante clava un cartel con una mano alzada en el portón, mientras la nieve cubre el jardín."]),
        comic(2, "La primavera", "gigante", 5, [
            "Los niños entran por un agujero del muro y los árboles florecen.",
            "En un rincón nevado, un niño pequeño llora junto a un árbol sin flores.",
            "El gigante, conmovido, ayuda al niño a subir al árbol.",
            "El gigante derriba el muro y juega con los niños."]),
    ],
)

# ============================================================================
# 6. EL RUISEÑOR Y LA ROSA (Wilde)
# ============================================================================
add_book(
    "El ruiseñor y la rosa", ["ruiseñor"],
    rafaga_vf=[
        rafaga("Un joven estudiante lloraba porque la hija del profesor le había dicho que bailaría con él solo si le llevaba una rosa roja. Pero en su jardín no había ninguna rosa roja.", [
            ("El estudiante necesitaba una rosa roja.", True),
            ("La joven le pidió una rosa amarilla.", False),
            ("En su jardín no había rosas rojas.", True)]),
        rafaga("El ruiseñor entendió que el estudiante estaba enamorado de verdad. Para crear una rosa roja, debía cantar toda la noche con el pecho apoyado en una espina.", [
            ("El ruiseñor debía cantar toda la noche.", True),
            ("Apoyaría su pecho en una espina.", True),
            ("Bastaba con regar el rosal con agua.", False)]),
    ],
    emoticono_dialogo=[
        emoticono("ruisenor_estudiante_llora",
                  "Un joven estudiante sentado bajo un roble, con un libro cerrado y lágrimas en las mejillas, de noche, junto a un rosal sin flores.",
                  "¡No hay ninguna rosa roja en todo mi jardín!",
                  ["¡Tengo muchas rosas rojas para bailar!", "¡Qué felices estamos esta noche!", "¡Mañana iré a pescar al río!"]),
        emoticono("ruisenor_canta_espina",
                  "Un ruiseñor pequeño y marrón posado en un rosal con el pecho apoyado en una espina, cantando bajo la luna, con una rosa que empieza a enrojecer.",
                  "¡Cantaré toda la noche por el amor verdadero!",
                  ["¡Esta noche me iré a dormir temprano!", "¡Qué rico sabor tiene esta espina!", "¡Prefiero volar al mar y descansar!"]),
    ],
    imagen_pixelada=[
        pixelada("ruisenor_ave",
                 "Un ruiseñor pequeño de plumaje marrón y pecho claro, posado en la rama de un rosal, con el pico abierto.",
                 "El ruiseñor", ["Un gorrión", "Un canario", "Un colibrí", "Un mirlo"]),
        pixelada("ruisenor_rosa_roja",
                 "Una rosa roja intensa, recién abierta, con gotas de rocío y un tallo con espinas, sobre fondo oscuro.",
                 "La rosa roja", ["Una amapola", "Un clavel blanco", "Un tulipán", "Un rubí"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 900,
            "El ruiseñor apoyó su pecho contra una espina del rosal y cantó toda la noche.",
            "La imagen contradictoria muestra al ruiseñor durmiendo tranquilo en un nido, lejos del rosal.",
            [("ruisenor_ave_rosal", "Ruiseñor sobre el rosal", "Un ruiseñor posado en un rosal de espinas bajo la luz de la luna."),
             ("ruisenor_espina_luna", "Espina bajo la luna", "Primer plano de una espina larga de rosal con la luna llena al fondo."),
             ("ruisenor_canta_luna", "Ruiseñor cantando", "Un ruiseñor con el pico abierto cantando bajo la luna llena.")],
            ("ruisenor_nido_dormido", "Ruiseñor durmiendo en su nido", "Un ruiseñor durmiendo tranquilo en un nido en lo alto de un árbol, lejos del rosal.")),
        contradiccion(2, 910,
            "La joven rechazó la rosa roja porque el sobrino del chambelán le había regalado joyas.",
            "La imagen contradictoria muestra a la joven abrazando la rosa roja con alegría.",
            [("ruisenor_joven_joyas", "Joven con joyas", "Una joven con vestido azul mirando con interés un cofre abierto lleno de joyas."),
             ("ruisenor_estudiante_rosa", "Estudiante con la rosa", "El estudiante sosteniendo una rosa roja en la mano, con gesto esperanzado."),
             ("ruisenor_sobrino", "Sobrino del chambelán", "Un joven elegante con casaca dorada entregando un cofre de joyas a la joven.")],
            ("ruisenor_joven_abraza_rosa", "Joven abrazando la rosa", "La joven abrazando contra el pecho una rosa roja, sonriendo con alegría.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La búsqueda de la rosa", [
            "El estudiante se lamenta porque no tiene una rosa roja para la joven que ama.",
            "El ruiseñor escucha y decide ayudarlo, pues cree en el amor verdadero.",
            "Visita primero un rosal blanco y luego uno amarillo, pero ninguno da rosas rojas.",
            "El rosal junto a la ventana le dice que solo puede lograrlo cantando toda la noche sobre una espina.",
            "El ruiseñor canta apoyado en la espina hasta que la rosa se vuelve roja."]),
        reconstruccion(2, "El final", [
            "Al amanecer, el ruiseñor muere y la rosa roja florece.",
            "El estudiante encuentra la rosa y corre a llevársela a la joven.",
            "La joven rechaza la rosa porque prefiere las joyas del sobrino del chambelán.",
            "El estudiante arroja la rosa a la calle y un carro pasa sobre ella.",
            "El estudiante vuelve a sus libros diciendo que el amor es una tontería."]),
    ],
    completa_dialogo=[
        completa(1, "El ruiseñor debía cantar toda la noche con el pecho apoyado en una", ".", "espina", ["rama", "piedra", "hoja"]),
        completa(2, "La joven prefirió unas joyas a la rosa", ".", "roja", ["blanca", "amarilla", "rosada"]),
    ],
    testigo_ocular=[
        testigo(1, "El rosal", "ruisenor_jardin_noche",
                "Jardín de noche con tres rosales: el de la izquierda con rosas blancas, el del centro con rosas amarillas y el de la derecha, junto a una ventana, sin flores; luna llena; un ruiseñor pequeño sobre una rama; una fuente de piedra.",
                [("¿Cuántos rosales había?", "Tres", ["Uno", "Dos", "Cinco"]),
                 ("¿De qué color eran las rosas del rosal de la izquierda?", "Blancas", ["Rojas", "Rosadas", "Azules"]),
                 ("¿Qué había en el jardín además de los rosales?", "Una fuente de piedra", ["Un columpio", "Un estanque con patos", "Un invernadero"])]),
        testigo(2, "La ventana del estudiante", "ruisenor_escritorio",
                "Un estudiante joven con jersey verde sentado en un escritorio con libros apilados; una vela encendida; por la ventana se ve el rosal con una rosa roja brillante; una pluma sobre un cuaderno; un gato dormido en una silla.",
                [("¿De qué color era el jersey del estudiante?", "Verde", ["Rojo", "Azul", "Gris"]),
                 ("¿Qué había sobre el escritorio además de libros?", "Una vela", ["Un reloj", "Una taza de té", "Una lámpara eléctrica"]),
                 ("¿Qué animal dormía en la silla?", "Un gato", ["Un perro", "Un conejo", "Un loro"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El jardín del rosal",
                "Bajo la luna, el jardín tenía flores, un rosal con espinas, una rosa roja y un ruiseñor que cantaba.",
                "ruisenor-jardin-bg", "Jardín de noche con luna llena, pasto oscuro y un camino de piedra; espacio libre para 6 objetos.",
                [new("rosa-roja", "Rosa roja", "Rosa roja intensa con tallo y dos hojas, fondo transparente."),
                 new("ruisenor", "Ruiseñor", "Ruiseñor pequeño marrón posado, de perfil, fondo transparente."),
                 lib("rosal-espinas", "Rosal con espinas"),
                 lib("flores", "Flores"),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("semaforo", "Semáforo", True)]),
        cazador(2, "El estudio del estudiante",
                "En el escritorio del estudiante había una vela, un libro antiguo y una pluma con tintero.",
                "ruisenor-estudio-bg", "Habitación de estudiante con una ventana grande de noche y una mesa de madera; espacio libre para 6 objetos.",
                [lib("vela", "Vela encendida"),
                 new("libro-antiguo", "Libro antiguo", "Libro antiguo de tapa de cuero marrón, fondo transparente."),
                 new("pluma-tintero", "Pluma y tintero", "Pluma de ave dentro de un tintero de cristal, fondo transparente."),
                 lib("laptop", "Computadora portátil", True),
                 lib("impresora", "Impresora", True),
                 lib("calculadora", "Calculadora solar", True)]),
    ],
    busca_imagen=[
        busca(1, "El ruiseñor y la rosa",
              "Sobre la rama más alta del rosal, el pequeño ruiseñor cantaba bajo la luz de la luna.",
              "Ruiseñor", "ruisenor-rosal-busca",
              "Jardín de noche con un rosal alto y luna llena. En la parte superior derecha, un ruiseñor marrón grande posado en la rama más alta, con un contorno de luz suave. Escena muy recargada: el rosal está lleno de rosas blancas y amarillas, hojas, espinas, otros pájaros, estrellas y luciérnagas.",
              (8, 52, 40, 37.5)),
        busca(2, "El ruiseñor y la rosa",
              "En el empedrado de la calle, aplastada por la rueda de un carro, yacía una rosa roja.",
              "Rosa roja aplastada", "ruisenor-calle-busca",
              "Calle empedrada con un carro a lo lejos. En la parte inferior, una rosa roja aplastada sobre las piedras, con un rojo apagado que destaca levemente del empedrado.",
              (65, 30, 50, 20)),
    ],
    comics_desordenados=[
        comic(1, "La promesa del baile", "ruisenor", 1, [
            "Un estudiante lee un libro mientras la hija del profesor le habla desde un balcón.",
            "El estudiante llora junto a un rosal sin rosas rojas.",
            "Un ruiseñor lo escucha desde una rama y se conmueve.",
            "El ruiseñor vuela hacia otros rosales para buscar una rosa roja."]),
        comic(2, "La rosa roja", "ruisenor", 5, [
            "El ruiseñor canta con el pecho en una espina de un rosal, bajo la luna.",
            "Al amanecer, una rosa roja brilla en el rosal y el ruiseñor yace en la hierba.",
            "El estudiante arranca la rosa y corre a la casa de la joven.",
            "La joven rechaza la rosa con gesto de desdén y el estudiante la tira a la calle."]),
    ],
)

# ============================================================================
# 7. RUMPELSTILTSKIN (Grimm)
# ============================================================================
add_book(
    "Rumpelstiltskin", ["Rumpel", "enano salt", "Rumplestiltskin", "Rumpelstiltskin"],
    rafaga_vf=[
        rafaga("Un molinero presumió ante el rey de que su hija podía convertir la paja en oro. El rey la encerró en una habitación llena de paja y le ordenó hilar oro antes de la mañana.", [
            ("El molinero dijo que su hija hilaba oro.", True),
            ("El rey la encerró en un jardín.", False),
            ("La habitación estaba llena de paja.", True)]),
        rafaga("Un hombrecillo apareció y hiló la paja en oro a cambio de un collar. La segunda noche pidió un anillo y, la tercera noche, pidió su primer hijo.", [
            ("Primero recibió un collar.", True),
            ("La tercera noche pidió su primer hijo.", True),
            ("Siempre pidió dinero a cambio.", False)]),
    ],
    emoticono_dialogo=[
        emoticono("rumpel_molinera_llora",
                  "Una joven sentada en el suelo de una habitación llena de paja, junto a una rueca de hilar, llorando, con una pequeña ventana al fondo.",
                  "¿Cómo convertiré toda esta paja en oro?",
                  ["¡Qué linda es esta habitación de flores!", "¡Qué rica es la comida de palacio!", "¡Hilaré esta lana con mucha facilidad!"]),
        emoticono("rumpel_hombrecillo_baila",
                  "Un hombrecillo de nariz larga y gorro puntiagudo, bailando alrededor de una fogata en el bosque y cantando con alegría.",
                  "¡Qué bueno que nadie sabe que me llamo Rumpelstiltskin!",
                  ["¡Nunca he bailado en mi vida!", "¡Voy a regalar mi oro a todos los niños!", "¡Mi nombre es Pedro y vivo en el pueblo!"]),
    ],
    imagen_pixelada=[
        pixelada("rumpel_personaje",
                 "Rumpelstiltskin, un hombrecillo de barba gris, nariz larga, gorro puntiagudo rojo y ropa vieja, sentado junto a una rueca.",
                 "Rumpelstiltskin", ["El molinero", "El rey", "Un duende del bosque", "Un mago"]),
        pixelada("rumpel_rueca_oro",
                 "Una rueca de madera con un montón de hilos de oro brillante enrollados en ella, en una habitación de piedra.",
                 "La rueca con oro", ["Un arpa", "Una cesta de paja", "Un telar", "Un baúl"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 920,
            "El hombrecillo hilaba la paja y la convertía en brillante oro.",
            "La imagen contradictoria muestra al hombrecillo convirtiendo la paja en bolas de nieve.",
            [("rumpel_hombrecillo_hila", "Hombrecillo hilando", "Un hombrecillo de gorro rojo hilando junto a una rueca en una habitación con paja."),
             ("rumpel_carretes_oro", "Carretes de oro", "Tres carretes de hilo de oro brillante sobre una mesa de madera."),
             ("rumpel_paja_y_oro", "Paja y oro", "Una habitación con paja amontonada en una esquina y carretes de oro apilados en la otra.")],
            ("rumpel_paja_nieve", "Paja convertida en nieve", "Un hombrecillo hilando junto a una rueca y convirtiendo la paja en bolas de nieve.")),
        contradiccion(2, 930,
            "La reina pudo salvar a su hijo adivinando el nombre del hombrecillo.",
            "La imagen contradictoria muestra a la reina entregando al bebé al hombrecillo con una sonrisa.",
            [("rumpel_mensajero_arbol", "Mensajero espiando", "Un mensajero con sombrero emplumado escondido tras un árbol, mirando hacia una fogata."),
             ("rumpel_baila_fogata", "Hombrecillo bailando", "Un hombrecillo bailando alrededor de una fogata en un claro del bosque de noche."),
             ("rumpel_reina_hombrecillo", "Reina frente al hombrecillo", "La reina con corona y su bebé en brazos, de pie frente al hombrecillo en una sala del castillo.")],
            ("rumpel_reina_entrega_bebe", "Reina entregando al bebé", "La reina sonriendo y entregando al bebé al hombrecillo en una sala del castillo.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La paja y el oro", [
            "Un molinero presume que su hija puede convertir la paja en oro.",
            "El rey encierra a la joven en una habitación con paja y le exige hilar oro.",
            "Un hombrecillo aparece y hila el oro a cambio de su collar.",
            "La segunda noche, el hombrecillo vuelve y se lleva su anillo.",
            "La tercera noche, la joven promete su primer hijo y el rey se casa con ella."]),
        reconstruccion(2, "El nombre secreto", [
            "Cuando nace su hijo, la reina ve regresar al hombrecillo.",
            "El hombrecillo le da tres días para adivinar su nombre.",
            "La reina prueba con muchos nombres, pero ninguno es el correcto.",
            "Un mensajero ve al hombrecillo bailando y cantando su nombre junto a una fogata.",
            "La reina dice «Rumpelstiltskin» y el hombrecillo se va furioso."]),
    ],
    completa_dialogo=[
        completa(1, "El molinero presumió de que su hija podía convertir la paja en", ".", "oro", ["plata", "pan", "hilo"]),
        completa(2, "Para quedarse con su hijo, la reina debía adivinar el", "del hombrecillo.", "nombre", ["cumpleaños", "oficio", "país"]),
    ],
    testigo_ocular=[
        testigo(1, "La habitación de la paja", "rumpel_cuarto_paja",
                "Habitación de piedra con paja amontonada hasta el techo; una rueca de madera; una joven con vestido verde; una pequeña ventana con barrotes; tres carretes de oro sobre una mesa; una antorcha en la pared.",
                [("¿De qué color era el vestido de la joven?", "Verde", ["Rojo", "Azul", "Blanco"]),
                 ("¿Cuántos carretes de oro había?", "Tres", ["Uno", "Dos", "Cinco"]),
                 ("¿Qué tenía la ventana?", "Barrotes", ["Cortinas rojas", "Flores", "Un vidrio de colores"])]),
        testigo(2, "La fogata del hombrecillo", "rumpel_bosque_fogata",
                "Claro del bosque de noche con una fogata; un hombrecillo con gorro puntiagudo rojo y barba gris bailando alrededor; un caldero; un mensajero con sombrero emplumado escondido tras un árbol; luna creciente.",
                [("¿De qué color era el gorro del hombrecillo?", "Rojo", ["Azul", "Verde", "Negro"]),
                 ("¿Qué hacía el mensajero?", "Se escondía tras un árbol", ["Dormía junto al fuego", "Cocinaba", "Bailaba también"]),
                 ("¿Qué forma tenía la luna?", "Creciente", ["Llena", "Nueva", "Menguante"])]),
    ],
    cazador_intrusos=[
        cazador(1, "La habitación de la paja",
                "En la habitación del rey había paja amontonada, una rueca de hilar y un carrete de hilo de oro.",
                "rumpel-cuarto-bg", "Habitación de piedra con una pequeña ventana con barrotes y suelo de tierra; espacio libre para 6 objetos.",
                [lib("paja", "Paja"),
                 new("rueca", "Rueca de hilar", "Rueca de madera antigua con rueda, fondo transparente."),
                 lib("hilo-dorado", "Carrete de hilo de oro"),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("laptop", "Computadora portátil", True),
                 lib("microondas", "Microondas", True)]),
        cazador(2, "El collar y el anillo",
                "El hombrecillo recibió un collar y un anillo de la joven a cambio de hilar la paja en oro.",
                "rumpel-pago-bg", "Mesa de madera en un cuarto de piedra, iluminada por una vela; espacio libre para 6 objetos.",
                [new("collar", "Collar", "Collar de cuentas doradas con una piedra roja, fondo transparente."),
                 new("anillo", "Anillo", "Anillo dorado con una pequeña piedra azul, fondo transparente."),
                 lib("audifonos", "Audífonos inalámbricos", True),
                 lib("calculadora", "Calculadora solar", True),
                 lib("consola", "Consola de videojuegos", True),
                 lib("radio", "Radio a pilas", True)]),
    ],
    busca_imagen=[
        busca(1, "Rumpelstiltskin",
              "En un rincón de la habitación, bajo un gran montón de paja, esperaba la rueca de la joven molinera.",
              "Rueca", "rumpel-cuarto-busca",
              "Habitación de piedra llena de paja. En la parte inferior izquierda, una rueca de madera grande entre la paja, de tono algo más oscuro y definido. Escena muy recargada: la habitación tiene paja amontonada, carretes de oro, cestas, taburetes, telas y otras ruecas pequeñas.",
              (45, 8, 30, 50)),
        busca(2, "Rumpelstiltskin",
              "Detrás de un tronco, el mensajero espiaba al hombrecillo que bailaba alrededor de la fogata.",
              "Mensajero escondido", "rumpel-fogata-busca",
              "Bosque de noche con una fogata en el centro. En la parte derecha, un mensajero con sombrero emplumado escondido tras un tronco, algo más iluminado que el bosque.",
              (28, 70, 20, 50)),
    ],
    comics_desordenados=[
        comic(1, "Paja y oro", "rumpel", 1, [
            "El molinero habla con el rey y presume de su hija.",
            "La joven llora en una habitación llena de paja.",
            "Un hombrecillo aparece y hila la paja en un carrete de oro.",
            "El rey ve la habitación llena de carretes de oro con gesto asombrado."]),
        comic(2, "El nombre", "rumpel", 5, [
            "La reina, con su bebé en brazos, ve aparecer al hombrecillo.",
            "La reina escribe una larga lista de nombres junto a su mensajero.",
            "El mensajero espía al hombrecillo bailando alrededor de la fogata.",
            "La reina dice el nombre del hombrecillo y él patalea furioso."]),
    ],
)

# ============================================================================
# 8. RICITOS DE ORO Y LOS TRES OSOS (W. W. Denslow)
# ============================================================================
add_book(
    "Ricitos de oro y los tres osos", ["Ricitos de oro", "Ricitos", "tres osos"],
    rafaga_vf=[
        rafaga("Los tres osos prepararon avena y salieron a pasear mientras se enfriaba. Mientras tanto, Ricitos de Oro entró en su casa sin permiso.", [
            ("Los osos salieron a pasear.", True),
            ("Los osos prepararon helado.", False),
            ("Ricitos de Oro entró sin permiso.", True)]),
        rafaga("Ricitos de Oro probó tres tazones de avena. El primero estaba muy caliente, el segundo muy frío y el tercero justo bien, así que se lo comió todo.", [
            ("El primer tazón estaba muy caliente.", True),
            ("El tercer tazón estaba muy frío.", False),
            ("Ricitos de Oro se comió el tercer tazón entero.", True)]),
    ],
    emoticono_dialogo=[
        emoticono("ricitos_prueba_avena",
                  "Una niña de cabello rizado y dorado, con vestido azul y delantal, frente a una mesa con tres tazones de distintos tamaños, probando con una cuchara y con cara de gusto.",
                  "¡Esta avena está justo como me gusta!",
                  ["¡Esta avena está demasiado caliente!", "¡Esta avena está helada!", "¡No tengo hambre, me iré a casa!"]),
        emoticono("ricitos_oso_enojado",
                  "Papá Oso, grande y de pelaje marrón, de pie en su casa, mirando con asombro y enojo su tazón de avena movido sobre la mesa, con Mamá Osa y el Osito detrás.",
                  "¡Alguien ha estado probando mi avena!",
                  ["¡Qué linda sorpresa, hay una invitada!", "¡Hoy no cocinamos nada!", "¡Alguien ha cantado en mi jardín!"]),
    ],
    imagen_pixelada=[
        pixelada("ricitos_personaje",
                 "Ricitos de Oro, una niña de cabello rizado y dorado con vestido azul y delantal blanco, de pie en el bosque.",
                 "Ricitos de Oro", ["Caperucita Roja", "Hansel", "Gretel", "Blancanieves"]),
        pixelada("ricitos_osito",
                 "El Osito, un osito pequeño de pelaje marrón claro con un delantal azul, sentado en una silla pequeña.",
                 "El Osito", ["Papá Oso", "Mamá Osa", "Un oso polar", "Un panda"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 940,
            "Ricitos de Oro encontró sobre la mesa tres tazones de avena: uno grande, uno mediano y uno pequeño.",
            "La imagen contradictoria muestra a Ricitos de Oro frente a una mesa con una pizza gigante.",
            [("ricitos_tres_tazones", "Tres tazones de distinto tamaño", "Tres tazones de avena humeante, de tamaño grande, mediano y pequeño, sobre una mesa de madera."),
             ("ricitos_prueba_pequeno", "Ricitos probando el tazón pequeño", "Ricitos de Oro probando con una cuchara el tazón pequeño."),
             ("ricitos_tres_cucharas", "Tres cucharas", "Tres cucharas de madera de distinto tamaño sobre una mesa.")],
            ("ricitos_pizza", "Ricitos con una pizza gigante", "Ricitos de Oro de pie frente a una mesa con una pizza gigante.")),
        contradiccion(2, 950,
            "Ricitos de Oro se quedó dormida en la camita pequeña del Osito.",
            "La imagen contradictoria muestra a Ricitos de Oro durmiendo en una hamaca colgada de un árbol.",
            [("ricitos_tres_camas", "Tres camas", "Tres camas de distinto tamaño (grande, mediana y pequeña) en un dormitorio."),
             ("ricitos_dormida_pequena", "Ricitos dormida", "Ricitos de Oro dormida en la cama más pequeña, con una colcha verde a rayas."),
             ("ricitos_osos_miran", "Osos mirando", "Los tres osos de pie junto a la cama pequeña, mirando a Ricitos dormida.")],
            ("ricitos_hamaca", "Ricitos en una hamaca", "Ricitos de Oro durmiendo en una hamaca colgada entre dos árboles del bosque.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La casa de los osos", [
            "Los tres osos dejan sus tazones de avena enfriándose y salen a pasear.",
            "Ricitos de Oro llega a la casa y entra sin pedir permiso.",
            "Prueba tres tazones y se come la avena del Osito.",
            "Se sienta en tres sillas y rompe la sillita del Osito.",
            "Sube a la habitación y se queda dormida en la camita del Osito."]),
        reconstruccion(2, "El regreso de los osos", [
            "Los osos regresan y notan que sus tazones han sido tocados.",
            "Papá Oso ve que alguien ha movido su silla.",
            "El Osito encuentra su sillita rota.",
            "Los osos suben y descubren a Ricitos de Oro dormida en la camita.",
            "Ricitos de Oro despierta, salta por la ventana y escapa corriendo."]),
    ],
    completa_dialogo=[
        completa(1, "—¡Alguien ha probado mi", "! —gruñó Papá Oso.", "avena", ["pastel", "jugo", "pan"]),
        completa(2, "La avena del tercer tazón no estaba ni muy caliente ni muy fría, estaba", ".", "perfecta", ["helada", "quemada", "amarga"]),
    ],
    testigo_ocular=[
        testigo(1, "La mesa de los osos", "ricitos_mesa_osos",
                "Una mesa de madera con tres tazones: uno grande azul, uno mediano rojo y uno pequeño amarillo; sube vapor de los tazones; tres sillas; una ventana con cortinas a cuadros; un reloj de cuco en la pared.",
                [("¿De qué color era el tazón pequeño?", "Amarillo", ["Azul", "Rojo", "Verde"]),
                 ("¿Cuántas sillas había?", "Tres", ["Dos", "Cuatro", "Seis"]),
                 ("¿Qué había colgado en la pared?", "Un reloj de cuco", ["Un espejo", "Un cuadro de flores", "Una estantería"])]),
        testigo(2, "El dormitorio de los osos", "ricitos_dormitorio_osos",
                "Dormitorio con tres camas de distinto tamaño; en la cama más pequeña duerme una niña de cabello dorado; colcha verde a rayas; ventana abierta con luna; alfombra redonda de color naranja.",
                [("¿En qué cama dormía la niña?", "En la más pequeña", ["En la más grande", "En la mediana", "En el suelo"]),
                 ("¿Cómo era la colcha?", "Verde a rayas", ["Roja lisa", "Azul con flores", "Amarilla"]),
                 ("¿Qué forma tenía la alfombra?", "Redonda", ["Cuadrada", "Triangular", "Ovalada"])]),
    ],
    cazador_intrusos=[
        cazador(1, "La cocina de los osos",
                "En la casita de los osos había tazones de avena, sillas de madera, una cama de madera y una manta roja.",
                "ricitos-cocina-bg", "Interior de una casita de bosque, con chimenea, ventana pequeña y piso de madera; espacio libre para 6 objetos.",
                [new("tazon-avena", "Tazón de avena", "Tazón de cerámica con avena humeante y una cuchara de madera, fondo transparente."),
                 new("silla-madera", "Silla de madera", "Silla de madera sencilla de respaldo bajo, fondo transparente."),
                 lib("cama-madera", "Cama de madera"),
                 lib("manta-roja", "Manta roja"),
                 lib("microondas", "Microondas", True),
                 lib("tv", "Televisor de pantalla plana", True)]),
        cazador(2, "El bosque de los osos",
                "Alrededor de la casa de los osos crecían flores, volaban mariposas y se alzaba una casa de madera.",
                "ricitos-bosque-bg", "Claro de bosque soleado con árboles altos y pasto verde; espacio libre para 6 objetos.",
                [lib("flores", "Flores"),
                 lib("mariposa", "Mariposa"),
                 new("casa-osos", "Casa de madera de los osos", "Casita de madera con techo de paja y chimenea, fondo transparente."),
                 lib("semaforo", "Semáforo", True),
                 lib("nave-espacial", "Nave espacial", True),
                 lib("monopatin", "Monopatín", True)]),
    ],
    busca_imagen=[
        busca(1, "Ricitos de oro y los tres osos",
              "Sobre la mesa de la cocina, el tazón más pequeño humeaba junto a una cuchara de madera.",
              "Tazón pequeño", "ricitos-mesa-busca",
              "Cocina de la casa de los osos con una mesa de madera. En el centro, un tazón pequeño humeante, de color amarillo apagado, junto a dos tazones más grandes. Escena muy recargada: la mesa tiene muchos platos, jarras, cucharas, frutas, manteles, tazones de distintos tamaños y una vela.",
              (45, 35, 40, 37.5)),
        busca(2, "Ricitos de oro y los tres osos",
              "Junto a la ventana del dormitorio, la sillita rota del Osito esperaba ser arreglada.",
              "Sillita rota", "ricitos-dormitorio-busca",
              "Dormitorio de la casa de los osos con tres camas. En la parte inferior derecha, una sillita de madera rota con una pata suelta, algo más clara que el suelo.",
              (55, 65, 25, 40)),
    ],
    comics_desordenados=[
        comic(1, "La avena", "ricitos", 1, [
            "Tres osos salen de su casa en el bosque dejando la avena enfriándose.",
            "Ricitos de Oro llega a la casa y mira por la ventana.",
            "Ricitos de Oro prueba la avena del tazón pequeño con una cuchara.",
            "Ricitos de Oro se sienta en la sillita del Osito, que se rompe."]),
        comic(2, "La camita", "ricitos", 5, [
            "Ricitos de Oro duerme en la camita del Osito.",
            "Los tres osos regresan y miran sorprendidos la mesa.",
            "Los osos entran al dormitorio y ven a Ricitos durmiendo.",
            "Ricitos de Oro salta por la ventana y escapa."]),
    ],
)

# ============================================================================
# 9. LA PRINCESA Y EL GUISANTE (Andersen)
# ============================================================================
add_book(
    "La princesa y el guisante", ["princesa y el guisante", "guisante"],
    rafaga_vf=[
        rafaga("Un príncipe quería casarse con una princesa de verdad, pero no lograba encontrarla. Una noche de tormenta, una joven empapada llamó a la puerta del castillo y dijo que era una princesa.", [
            ("El príncipe buscaba una princesa verdadera.", True),
            ("La joven llegó en un día soleado.", False),
            ("La joven dijo ser una princesa.", True)]),
        rafaga("La reina puso un guisante en la cama de la joven y encima apiló veinte colchones. Por la mañana, la joven dijo que había dormido muy mal.", [
            ("La reina puso un guisante en la cama.", True),
            ("Se usaron cinco colchones.", False),
            ("La joven durmió mal.", True)]),
    ],
    emoticono_dialogo=[
        emoticono("guisante_princesa_empapada",
                  "Una joven empapada por la lluvia, con el cabello mojado y el vestido arrugado, en la puerta de un castillo de noche, con relámpagos en el cielo.",
                  "¡Soy una princesa de verdad! ¿Me dan refugio?",
                  ["¡Vengo a vender manzanas!", "¡Hoy es un día muy soleado!", "¡Busco a mi gato perdido!"]),
        emoticono("guisante_princesa_cama",
                  "Una princesa en camisón sentada sobre una pila altísima de colchones, con cara de cansancio y algunas marcas moradas en los brazos, junto a la reina.",
                  "No pude dormir, había algo duro en mi cama.",
                  ["¡Dormí como un angelito toda la noche!", "¡Esta cama es demasiado pequeña!", "¡Quiero más almohadas!"]),
    ],
    imagen_pixelada=[
        pixelada("guisante_pequeno",
                 "Un pequeño guisante verde y redondo sobre un cojín de terciopelo rojo.",
                 "El guisante", ["Una perla", "Una canica", "Una uva", "Una esmeralda"]),
        pixelada("guisante_colchones",
                 "Una pila altísima de colchones y edredones de colores, con una pequeña escalera de madera apoyada a un lado.",
                 "La pila de colchones", ["Una torre de libros", "Una escalera", "Un pastel", "Una montaña"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 960,
            "La reina puso un pequeño guisante en la cama y lo cubrió con veinte colchones.",
            "La imagen contradictoria muestra a la reina poniendo una gran piedra en la cama.",
            [("guisante_verde_cojin", "Guisante verde", "Un guisante verde y brillante sobre una tabla de madera."),
             ("guisante_reina_colchones", "Reina con colchones", "La reina con vestido morado indicando a los criados que apilen colchones."),
             ("guisante_pila_alta", "Pila alta de colchones", "Una pila de colchones tan alta que casi llega al techo de la habitación.")],
            ("guisante_reina_piedra", "Reina con una piedra", "La reina colocando una gran piedra gris sobre una cama.")),
        contradiccion(2, 970,
            "La joven llegó a la puerta del castillo en una noche de tormenta, empapada por la lluvia.",
            "La imagen contradictoria muestra a la joven llegando en un día soleado con una sombrilla y el vestido seco.",
            [("guisante_relampago_castillo", "Relámpago sobre el castillo", "Un relámpago iluminando un castillo con dos torres en una noche de tormenta."),
             ("guisante_joven_mojada", "Joven mojada", "Una joven con vestido azul empapado de lluvia en la puerta de un castillo."),
             ("guisante_rey_farol", "Rey con farol", "El rey con corona abriendo la puerta con un farol en la mano bajo la lluvia.")],
            ("guisante_joven_sombrilla", "Joven con sombrilla en un día soleado", "Una joven con vestido seco y una sombrilla, llegando al castillo en un día de sol.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La princesa verdadera", [
            "Un príncipe viaja por el mundo buscando una princesa verdadera.",
            "Regresa al castillo sin encontrarla y se siente muy triste.",
            "Una noche de tormenta, una joven empapada llama a la puerta del castillo.",
            "La joven asegura ser una princesa y el rey la deja pasar.",
            "La reina decide ponerla a prueba."]),
        reconstruccion(2, "El guisante", [
            "La reina coloca un guisante en una cama vacía.",
            "Encima del guisante, apila veinte colchones y veinte edredones.",
            "La joven sube por una escalera a dormir en la cama.",
            "Por la mañana dice que no pudo dormir por algo duro.",
            "El príncipe se casa con ella y el guisante se guarda en un museo."]),
    ],
    completa_dialogo=[
        completa(1, "La reina puso un pequeño", "debajo de veinte colchones.", "guisante", ["anillo", "botón", "zapato"]),
        completa(2, "—No pude dormir en toda la noche; había algo muy", "en mi cama.", "duro", ["blando", "dulce", "pequeño"]),
    ],
    testigo_ocular=[
        testigo(1, "La puerta del castillo", "guisante_puerta_tormenta",
                "Noche de tormenta; un castillo con dos torres; una joven con vestido azul empapado y zapatos con barro; el rey con corona dorada sostiene un farol encendido; un relámpago amarillo en el cielo; charcos en el suelo.",
                [("¿De qué color era el vestido de la joven?", "Azul", ["Rojo", "Verde", "Blanco"]),
                 ("¿Qué sostenía el rey?", "Un farol", ["Un paraguas", "Una espada", "Un libro"]),
                 ("¿Cuántas torres tenía el castillo?", "Dos", ["Una", "Tres", "Cuatro"])]),
        testigo(2, "La cama alta", "guisante_dormitorio_alto",
                "Habitación con una cama altísima formada por muchos colchones apilados; una escalera de madera apoyada a un lado; la reina con vestido morado; una vela encendida sobre una mesita; ventana con luna.",
                [("¿Cómo se subía a la cama?", "Con una escalera de madera", ["Con una cuerda", "Con un taburete", "De un salto"]),
                 ("¿De qué color era el vestido de la reina?", "Morado", ["Rojo", "Verde", "Amarillo"]),
                 ("¿Qué había sobre la mesita?", "Una vela", ["Un florero", "Un reloj", "Un libro"])]),
    ],
    cazador_intrusos=[
        cazador(1, "La habitación de la princesa",
                "En el dormitorio de la prueba había un guisante, una pila de colchones, una escalera de madera y una vela.",
                "guisante-dormitorio-bg", "Dormitorio de castillo con ventana alta, paredes de piedra y alfombra; espacio libre para 6 objetos.",
                [new("guisante", "Guisante", "Guisante verde y redondo, fondo transparente."),
                 new("colchones", "Pila de colchones", "Pila alta de colchones de colores, fondo transparente."),
                 new("escalera-madera", "Escalera de madera", "Escalera de madera pequeña de seis peldaños, fondo transparente."),
                 lib("vela", "Vela encendida"),
                 lib("laptop", "Computadora portátil", True),
                 lib("telefono-movil", "Teléfono móvil", True)]),
        cazador(2, "El castillo en la tormenta",
                "Bajo la tormenta, en la entrada del castillo, aparecían una corona, una capa de viaje y un farol encendido.",
                "guisante-castillo-bg", "Entrada de un castillo en una noche lluviosa, con puerta de madera y charcos; espacio libre para 6 objetos.",
                [lib("corona-rey", "Corona del rey"),
                 lib("capa", "Capa de viaje"),
                 new("farol", "Farol", "Farol antiguo de hierro con una vela encendida dentro, fondo transparente."),
                 lib("nave-espacial", "Nave espacial", True),
                 lib("radio", "Radio a pilas", True),
                 lib("impresora", "Impresora", True)]),
    ],
    busca_imagen=[
        busca(1, "La princesa y el guisante",
              "En la base de la gigantesca pila de colchones, entre las tablas de la cama, descansaba un pequeño guisante verde.",
              "Guisante", "guisante-cama-busca",
              "Primer plano de la base de una cama altísima de madera. En la parte inferior, entre las tablas, un guisante verde apagado, enorme en este primer plano, que destaca levemente de la madera. Escena muy recargada: el suelo está lleno de colchones, edredones, almohadas, bolas de lana, botones y cuentas redondas verdes.",
              (55, 30, 40, 37.5)),
        busca(2, "La princesa y el guisante",
              "Junto a la puerta del castillo, un farol encendido iluminaba la lluvia.",
              "Farol", "guisante-puerta-busca",
              "Puerta de castillo de noche con lluvia. En la parte derecha, un farol de hierro alto con la vela encendida, cuyo resplandor cálido lo distingue de la pared.",
              (20, 68, 20, 50)),
    ],
    comics_desordenados=[
        comic(1, "Una noche de tormenta", "guisante", 1, [
            "Un príncipe mira por la ventana del castillo, triste, sin haber encontrado una princesa verdadera.",
            "Un relámpago ilumina a una joven empapada frente a la puerta.",
            "El rey abre la puerta con un farol en la mano.",
            "La joven entra al castillo, cubierta con una manta, ante la mirada de la reina."]),
        comic(2, "El guisante", "guisante", 5, [
            "La reina coloca un guisante sobre la cama vacía.",
            "Los criados apilan veinte colchones sobre el guisante.",
            "La joven sube por una escalera a la altísima cama.",
            "A la mañana siguiente, la joven bosteza y cuenta que no durmió, mientras el príncipe sonríe."]),
    ],
)


# ----------------------------------------------------------------------------
# Exportar la lista de imágenes (formato del docente): "### N. nombre [ext:1024x1024]"
# ----------------------------------------------------------------------------
IMG_SIZE = "1024x1024"
_PATH_KEYS = {
    "emotionImage": "imageDescription", "imageSrc": "imageDescription",
    "imageUrl": "imageDescription", "image": "imageDescription",
    "bgImageUrl": "bgImageDescription",
}


def _walk(node, out, game):
    if isinstance(node, dict):
        for pk, dk in _PATH_KEYS.items():
            if pk in node and dk in node:
                out.append((node[pk], node[dk], node.get("targetArea"), game))
        for v in node.values():
            _walk(v, out, game)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out, game)


STYLE_BASE = (
    "Estilo: caricatura antigua de los años 30 (animación clásica tipo Cuphead), personajes «rubber hose» "
    "con ojos grandes, manos con guantes blancos y extremidades curvas y flexibles, contorno negro grueso, "
    "sombreado con tramado de líneas finas, textura de papel envejecido con grano y pequeñas manchas, "
    "dentro de un marco negro de esquinas redondeadas."
)
STYLE_SEPIA = (
    " Paleta en tonos sepia, crema y marrón con rojo terroso como único acento."
    " Sin ningún texto, letras, números ni logotipos."
)
STYLE_COLOR = (
    " Paleta base sepia, crema y marrón, pero los objetos o personajes clave de la descripción (los que tienen "
    "un color o una característica visual que el jugador debe identificar) deben pintarse con su color propio en "
    "tono apagado o mate, sin brillos saturados; el resto de la escena queda en sepia."
    " Sin ningún texto, letras, números ni logotipos."
)
STYLE_ITEM = (
    "Estilo: caricatura antigua de los años 30 (tipo Cuphead), un solo objeto centrado, contorno negro grueso, "
    "sombreado con tramado de líneas finas, paleta sepia y marrón (si la descripción menciona un color, píntalo "
    "en tono apagado o mate), sin marco, sin sombra proyectada, fondo transparente. "
    "Sin ningún texto, letras ni números."
)
# Juegos donde hay que identificar un color u otra característica visual
COLOR_GAMES = {"testigo_ocular", "encuentra_contradiccion", "imagen_pixelada", "busca_imagen"}
BUSCA_REGLA = (
    " Regla del juego: el objeto a encontrar debe ocupar exactamente el {pct}% del área total de la imagen "
    "(ni más ni menos: {w}% de ancho x {h}% de alto) y diferenciarse levemente del entorno "
    "(un poco más de contraste, un contorno algo más marcado o un leve brillo), sin verse pegado. {modo}"
)
BUSCA_MODO = {
    15: "Modalidad: objeto del 15% en una escena recargada, con muchos elementos de fondo que compiten por la atención.",
    10: "Modalidad: objeto del 10% en una escena estándar, con pocos elementos de fondo.",
}


def export_images(datasets, path="imagenes_por_crear.md", with_folders=True):
    """datasets: lista de diccionarios NEW_DATASET (se numeran de corrido).
    with_folders=True -> el nombre incluye la carpeta (emoticono/xxx) para que cada imagen
    se cree en su carpeta dentro de assets/images/. with_folders=False -> solo el nombre."""
    rows, seen = [], set()
    for ds in datasets:
        for games in ds.values():
            for game in GAME_CODES:
                _walk(games[game], rows, game)
    blocks, n = [], 0
    for p, d, area, game in rows:
        if p in seen:
            continue
        seen.add(p)
        n += 1
        rel = p[len(IMG):] if p.startswith(IMG) else os.path.basename(p)
        name, ext = os.path.splitext(rel if with_folders else os.path.basename(rel))
        transparente = "fondo transparente" in d
        d = d.replace(", fondo transparente.", ".").replace(", estilo ilustración infantil", "")
        extra = ""
        if area:
            extra = (f" Zona donde debe quedar el objeto a encontrar: {area['top']}% desde arriba, "
                     f"{area['left']}% desde la izquierda, ocupando {area['width']}% de ancho y {area['height']}% de alto."
                     + BUSCA_REGLA.format(pct=round(area["width"] * area["height"] / 100), w=area["width"],
                                          h=area["height"], modo=BUSCA_MODO[round(area["width"] * area["height"] / 100)]))
        if transparente:
            style = " " + STYLE_ITEM
        else:
            style = " " + STYLE_BASE + (STYLE_COLOR if game in COLOR_GAMES else STYLE_SEPIA)
        blocks.append(f"### {n}. {name} [{ext.lstrip('.')}:{IMG_SIZE}]\n{d}{extra}{style}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
    print(f"✓ {n} imágenes descritas en {path}")


def _load_first_batch():
    """Carga el primer lote (populate_minigames_nuevos_libros.py) si está en la misma carpeta."""
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "populate_minigames_nuevos_libros.py")
    if not os.path.exists(p):
        return {}
    spec = importlib.util.spec_from_file_location("lote1", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.NEW_DATASET


# ----------------------------------------------------------------------------
# Carga en la base de datos
# ----------------------------------------------------------------------------
def _setup_django():
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()


def run():
    _setup_django()
    from catalog.models import Book
    from games.models import BookMinigame, Minigame

    print("=== POBLANDO MINIJUEGOS DE LOS 9 LIBROS NUEVOS (LOTE 2) ===")
    created_count = 0

    for book_title, game_types in NEW_DATASET.items():
        book = None
        for kw in KEYWORDS[book_title]:
            book = Book.objects.filter(title__icontains=kw).first()
            if book:
                break
        if not book:
            print(f"[ERROR] '{book_title}' no existe en la BD (probé: {KEYWORDS[book_title]}).")
            continue
        print(f"✓ '{book_title}' -> '{book.title}' (ID {book.id})")

        # Solo se borran los minijuegos DE ESTE libro
        deleted, _ = BookMinigame.objects.filter(book=book).delete()
        if deleted:
            print(f"   🗑️ {deleted} registros anteriores de este libro eliminados.")

        for game_code, samples in game_types.items():
            minigame, _ = Minigame.objects.get_or_create(
                code=game_code,
                defaults={
                    "name": game_code.replace("_", " ").title(),
                    "description": f"Minijuego tipo {game_code}",
                },
            )
            for idx, sample_data in enumerate(samples, start=1):
                BookMinigame.objects.create(
                    book=book,
                    minigame=minigame,
                    config_data=sample_data,
                    title=f"Desafío {minigame.name} #{idx}",
                )
                created_count += 1

    print(f"\n✓ Proceso finalizado. Se insertaron {created_count} registros.")


if __name__ == "__main__":
    if "--export-images" in sys.argv:
        # Un solo documento con las imágenes de AMBOS lotes (lote 1 primero)
        export_images([_load_first_batch(), NEW_DATASET], with_folders="--flat" not in sys.argv)
    else:
        run()
