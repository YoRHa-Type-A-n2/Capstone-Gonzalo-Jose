"""
populate_minigames_nuevos_libros.py
===================================
Pobla los minijuegos de 10 libros nuevos (2 desafíos x 10 tipos de juego = 20 por libro).

Uso:
    python populate_minigames_nuevos_libros.py                  # inserta en la BD
    python populate_minigames_nuevos_libros.py --export-images  # genera imagenes_por_crear.md (nombres con carpeta)
    python populate_minigames_nuevos_libros.py --export-images --flat  # nombres sin carpeta

Diferencias importantes con populate_minigames.py:
  * NO borra todos los BookMinigame. Solo reemplaza los de estos 10 libros
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
# 1. LA SIRENITA (Andersen)
# ============================================================================
add_book(
    "La sirenita", ["sirenita"],
    rafaga_vf=[
        rafaga("La sirenita era la más joven de las seis hijas del rey del mar. Su abuela les contaba historias del mundo de los humanos", [
            ("La sirenita era la menor de seis hermanas.", True),
            ("La sirenita era hija del carpintero del mar.", False),
            ("La abuela les hablaba del mundo de los humanos.", True)]),
        rafaga("Durante una tormenta, el barco del príncipe se hundió. La sirenita lo sostuvo sobre las olas y lo dejó en la orilla, cerca d eun templo.", [
            ("La sirenita salvó al príncipe de ahogarse.", True),
            ("Lo dejó en la orilla, cerca de un templo.", True),
            ("El príncipe se fue a vivir al fondo del mar.", False)]),
    ],
    emoticono_dialogo=[
        emoticono("sirenita_asombrada",
                  "La sirenita (cola de pez verde, cabello largo castaño) asomada sobre las olas de noche, con los ojos muy abiertos, mirando un gran barco iluminado con farolillos de colores.",
                  "¡Nunca había visto un barco tan hermoso, lleno de luces!",
                  ["¡Qué hambre tengo, voy a pescar algo!", "¡Quiero volver a dormir en mi concha!", "¡Mi abuela me llama para cenar!"]),
        emoticono("bruja_del_mar",
                  "La bruja del mar, de aspecto misterioso, rodeada de serpientes de agua y pulpos, con una sonrisa maliciosa frente a un caldero burbujeante en una cueva submarina.",
                  "Te daré piernas, pero a cambio me entregarás tu hermosa voz.",
                  ["¡Toma mi corona de perlas, es un regalo!", "¡Bienvenida a mi fiesta de cumpleaños!", "¡Qué lindo día para nadar con los delfines!"]),
    ],
    imagen_pixelada=[
        pixelada("sirenita_principe_cubierta",
                 "Joven príncipe de pie en la cubierta de su barco, de noche, con ropa elegante de fiesta y una capa azul, rodeado de farolillos de colores.",
                 "El príncipe", ["El rey del mar", "El capitán del barco", "La bruja del mar", "Un marinero"]),
        pixelada("sirenita_palacio_coral",
                 "Palacio submarino de coral y conchas de colores, con torres de caracolas y algas ondulando alrededor, peces de colores nadando, luz azulada del fondo del mar.",
                 "El palacio del rey del mar", ["Un castillo en la montaña", "El barco del príncipe", "La cueva de la bruja", "Un templo en la orilla"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 600,
            "La sirenita salvó al príncipe y lo dejó tendido sobre la arena de la orilla.",
            "La imagen contradictoria muestra a la sirenita dejando al príncipe en la copa de un árbol en lugar de en la arena.",
            [("sirenita_nadando_principe", "La sirenita nadando con el príncipe", "La sirenita nadando entre olas llevando al príncipe inconsciente con la cabeza fuera del agua."),
             ("sirenita_principe_arena", "El príncipe tendido en la arena", "El príncipe dormido o inconsciente sobre la arena de una playa, con espuma de mar tocando sus pies."),
             ("sirenita_templo_orilla", "Templo blanco junto a la orilla", "Un templo blanco con columnas junto a la playa, al amanecer.")],
            ("sirenita_principe_arbol", "El príncipe sobre un árbol", "La sirenita en el agua, mirando hacia arriba, mientras el príncipe está acostado sobre la copa de un árbol cerca de la costa.")),
        contradiccion(2, 610,
            "La bruja del mar vivía en un lugar oscuro del fondo del océano, rodeada de pulpos y plantas viscosas.",
            "La imagen contradictoria muestra la casa de la bruja soleada, con un jardín lleno de flores de colores.",
            [("sirenita_pulpos", "Pulpos en el fondo oscuro", "Pulpos gigantes de tentáculos largos enredados entre algas oscuras en aguas muy oscuras."),
             ("sirenita_caldero", "Caldero burbujeante", "Un gran caldero negro hirviendo con burbujas verdes sobre un fuego azul, en una cueva."),
             ("sirenita_camino_algas", "Camino de algas viscosas", "Un sendero sombrío entre algas verdes oscuras y pólipos viscosos en el fondo marino.")],
            ("sirenita_casa_flores", "Casa soleada con flores", "Una casita luminosa y alegre con un jardín de flores rosadas y amarillas, bajo un sol brillante.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La sirenita conoce al príncipe", [
            "La sirenita cumple quince años y por fin puede subir a la superficie del mar.",
            "Desde el agua observa un gran barco donde se celebra el cumpleaños de un apuesto príncipe.",
            "Una terrible tormenta hunde el barco y el príncipe cae al mar.",
            "La sirenita lo sostiene sobre las olas y lo deja a salvo en la orilla.",
            "Una joven del templo cercano encuentra al príncipe y lo ayuda."]),
        reconstruccion(2, "El trato con la bruja", [
            "La sirenita no puede olvidar al príncipe y desea vivir entre los humanos.",
            "Viaja hasta la cueva de la bruja del mar, atravesando aguas peligrosas.",
            "La bruja le prepara una poción a cambio de su hermosa voz.",
            "La sirenita bebe la poción y su cola de pez se convierte en piernas.",
            "El príncipe la encuentra en la playa y la lleva a su palacio."]),
    ],
    completa_dialogo=[
        completa(1, "La sirenita tenía la voz más", "de todo el océano.", "hermosa", ["ronca", "débil", "grave"]),
        completa(2, "—Te daré piernas para caminar, pero a cambio me entregarás tu", "—dijo la bruja del mar.", "voz", ["corona", "anillo", "collar"]),
    ],
    testigo_ocular=[
        testigo(1, "El barco del príncipe", "sirenita_barco_noche",
                "De noche, un gran barco de tres mástiles con velas blancas, iluminado por muchos farolillos de colores; en la cubierta, un príncipe de cabello oscuro con una capa azul; en el mar, la sirenita asomada mirando.",
                [("¿Qué iluminaba el barco?", "Farolillos de colores", ["Antorchas rojas", "Un faro gigante", "Velas blancas pequeñas"]),
                 ("¿Cuántos mástiles tenía el barco?", "Tres", ["Uno", "Dos", "Cuatro"]),
                 ("¿De qué color era la capa del príncipe?", "Azul", ["Roja", "Verde", "Negra"])]),
        testigo(2, "El jardín de la sirenita", "sirenita_jardin_estatua",
                "Jardín submarino en el fondo del mar, con una estatua de mármol blanco de un joven en el centro, rodeada de flores de coral rojas; tres peces pequeños amarillos nadando; la sirenita sentada junto a la estatua.",
                [("¿De qué material era la estatua?", "Mármol blanco", ["Madera", "Oro", "Hierro"]),
                 ("¿De qué color eran las flores alrededor?", "Rojas", ["Azules", "Amarillas", "Blancas"]),
                 ("¿Cuántos peces amarillos se veían?", "Tres", ["Uno", "Dos", "Cinco"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El jardín de la sirenita",
                "En el fondo del mar, el jardín de la sirenita brillaba con estrellas de mar, corales rojos, un cofre hundido lleno de tesoros y una concha con una perla.",
                "sirenita-jardin-bg", "Fondo marino azul turquesa con rayos de luz desde la superficie, arena clara y algas suaves, sin objetos en primer plano (espacio libre para colocar 6 objetos).",
                [new("estrella-mar", "Estrella de mar", "Estrella de mar anaranjada de cinco puntas, estilo ilustración infantil, fondo transparente."),
                 new("coral-rojo", "Coral rojo", "Rama de coral rojo brillante con varias ramificaciones, fondo transparente."),
                 lib("cofre", "Cofre del tesoro"),
                 new("concha-perla", "Concha con perla", "Concha marina rosada abierta con una perla blanca brillante en el centro, fondo transparente."),
                 lib("submarino", "Submarino", True),
                 lib("telefono-movil", "Teléfono móvil", True)]),
        cazador(2, "La fiesta en el barco",
                "En la cubierta del barco del príncipe había gruesas cuerdas, tablones de madera pulida y farolillos de colores que alumbraban la fiesta.",
                "sirenita-barco-bg", "Cubierta de un barco antiguo de noche, con mástil y velas blancas al fondo y cielo estrellado; piso de madera vacío para colocar objetos.",
                [lib("cuerda", "Cuerda de barco"),
                 lib("tablones", "Tablones de madera"),
                 new("farolillos", "Farolillos de colores", "Tres farolillos de papel de colores (rojo, amarillo y azul) encendidos, colgando de una cuerda, fondo transparente."),
                 lib("nave-espacial", "Nave espacial", True),
                 lib("radio", "Radio a pilas", True),
                 lib("patineta", "Patineta eléctrica", True)]),
    ],
    busca_imagen=[
        busca(1, "La sirenita",
              "Entre las rocas de la orilla, medio cubierto por la espuma de las olas, asomaba el techo blanco del templo donde la sirenita dejó al príncipe.",
              "Templo blanco", "sirenita-orilla",
              "Playa al amanecer con rocas, espuma y olas, y un barco lejano a la derecha. El templo blanco con columnas es grande y ocupa la parte superior izquierda, apoyado sobre las rocas; su blanco es algo más claro y su contorno más marcado que el resto de la playa. Escena muy recargada: la orilla está llena de conchas, estrellas de mar, cangrejos, gaviotas, otras rocas de formas parecidas, un velero cercano y varias olas con espuma.",
              (15, 10, 30, 50)),
        busca(2, "La sirenita",
              "Sobre el suelo arenoso de la gruta de la bruja, entre las algas oscuras, descansaba el caldero donde preparaba la poción.",
              "Caldero de la bruja", "sirenita-gruta-bruja",
              "Gruta submarina oscura con algas y algunos huesos blancos. En la parte inferior derecha, un caldero negro con burbujas verdes, con un leve resplandor verdoso que lo distingue del fondo.",
              (58, 55, 32, 31.25)),
    ],
    comics_desordenados=[
        comic(1, "El rescate del príncipe", "sirenita", 1, [
            "La sirenita asoma sobre las olas de noche y mira un barco iluminado con farolillos de colores.",
            "Una tormenta con rayos y olas gigantes hunde el barco; el príncipe cae al agua.",
            "La sirenita nada llevando al príncipe inconsciente sobre las olas.",
            "La sirenita deja al príncipe sobre la arena, junto a un templo blanco, y se esconde tras la espuma."]),
        comic(2, "El precio de las piernas", "sirenita", 5, [
            "La sirenita entra a la cueva oscura de la bruja del mar, con un caldero al centro.",
            "La bruja le entrega una poción brillante dentro de un frasco, y la sirenita le entrega su voz en forma de luz.",
            "La sirenita bebe la poción sobre una playa, con su cola de pez brillando.",
            "La sirenita, ya con piernas, de pie en la playa, mientras el príncipe se acerca sorprendido."]),
    ],
)

# ============================================================================
# 2. LOS HERMANOS DE MOWGLI (Kipling)
# ============================================================================
add_book(
    "Los hermanos de Mowgli", ["Mowgli", "hermanos de Mowgli"],
    rafaga_vf=[
        rafaga("Una noche, un pequeño cachorro de hombre llegó gateando hasta la cueva de los lobos. Madre Loba lo cuidó como a uno de sus propios cachorros y lo llamó Mowgli, que significa «la rana».", [
            ("Mowgli era un cachorro de hombre.", True),
            ("Madre Loba lo cuidó como a uno de sus hijos.", True),
            ("Mowgli llegó a la cueva de los osos.", False)]),
        rafaga("El tigre Shere Khan quería llevarse al cachorro de hombre, pero Madre Loba no se lo permitió. La pantera Bagheera ofreció un toro recién cazado para que Mowgli pudiera quedarse.", [
            ("Shere Khan era un tigre.", True),
            ("Bagheera era un oso pardo.", False),
            ("Bagheera ofreció un toro para salvar a Mowgli.", True)]),
    ],
    emoticono_dialogo=[
        emoticono("mowgli_madre_loba",
                  "Madre Loba, una loba gris de ojos brillantes, protegiendo con su cuerpo a un bebé humano dentro de una cueva y mostrando los colmillos hacia la entrada.",
                  "¡El cachorro de hombre es mío! ¡No te lo llevarás!",
                  ["¡Tigre, pasa y cena con nosotros!", "¡Qué sueño tengo, me iré a dormir!", "¡Aquí tienes al cachorro, llévatelo!"]),
        emoticono("mowgli_shere_khan",
                  "Un gran tigre de Bengala que cojea de una pata trasera, rugiendo furioso en la entrada de una cueva, con la selva de fondo.",
                  "¡Entregadme al cachorro de hombre, es mi presa!",
                  ["¡Qué linda cueva, me quedaré a vivir aquí!", "¡Les traje un regalo para el cachorro!", "¡Me siento muy solo y triste!"]),
    ],
    imagen_pixelada=[
        pixelada("mowgli_baloo",
                 "Baloo, un oso pardo grande y simpático, sentado en la selva, sonriendo, con hojas y lianas detrás.",
                 "Baloo", ["Bagheera", "Akela", "Shere Khan", "Tabaqui"]),
        pixelada("mowgli_bagheera",
                 "Bagheera, una pantera negra elegante, sentada sobre una rama gruesa en la selva, con ojos verdes brillantes.",
                 "Bagheera", ["Baloo", "Shere Khan", "Akela", "Madre Loba"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 620,
            "Shere Khan era un enorme tigre que cojeaba de una pata.",
            "La imagen contradictoria muestra a Shere Khan como un pequeño gatito doméstico con un cascabel.",
            [("mowgli_tigre_grande", "Tigre enorme en la selva", "Un tigre de Bengala enorme caminando con una pata trasera coja entre la hierba alta."),
             ("mowgli_huellas_tigre", "Huellas de tigre irregulares", "Huellas de tigre grandes en el barro, con una de ellas más corta que las demás, en la orilla del río."),
             ("mowgli_ojos_tigre", "Ojos de tigre en la oscuridad", "Dos ojos amarillos brillando entre los arbustos de la selva de noche.")],
            ("mowgli_gatito", "Gatito con cascabel", "Un gatito doméstico pequeño y atigrado con un collar con cascabel, sentado entre la hierba de la selva.")),
        contradiccion(2, 630,
            "Mowgli, el cachorro de hombre, era criado por una familia de lobos dentro de una cueva.",
            "La imagen contradictoria muestra a Mowgli durmiendo en un nido de águilas en la cima de un árbol.",
            [("mowgli_juega_lobeznos", "Mowgli jugando con lobeznos", "Un niño pequeño de pelo negro jugando con cachorros de lobo sobre la tierra frente a una cueva."),
             ("mowgli_madre_loba_lame", "Madre Loba cuidando a Mowgli", "Una loba gris lamiendo la cabeza de un niño sentado entre sus cachorros."),
             ("mowgli_cueva_lobos", "Cueva entre rocas", "La entrada de una cueva entre rocas grandes con tres lobos descansando adentro.")],
            ("mowgli_nido_aguilas", "Mowgli en un nido de águilas", "Un niño de pelo negro durmiendo dentro de un enorme nido de ramas en la copa de un árbol altísimo, con águilas alrededor.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La llegada del cachorro de hombre", [
            "Al caer la noche, Padre Lobo despierta y escucha las palabras del chacal Tabaqui.",
            "Tabaqui le avisa que el tigre Shere Khan anda cazando cerca de la cueva.",
            "Un niño pequeño llega gateando hasta la cueva de los lobos.",
            "Shere Khan reclama al niño, pero Madre Loba lo defiende con fiereza.",
            "Madre Loba decide criarlo junto a sus propios cachorros y lo llama Mowgli."]),
        reconstruccion(2, "La Flor Roja", [
            "Los años pasan y Mowgli crece fuerte, aprendiendo la Ley de la Selva con Baloo.",
            "Akela, el viejo jefe, falla al cazar y la manada se prepara para quitarle el mando.",
            "Bagheera le dice a Mowgli que debe traer la Flor Roja, el fuego, de la aldea de los hombres.",
            "Mowgli llena una vasija de barro con brasas y regresa a la selva.",
            "Con una rama encendida, Mowgli enfrenta a Shere Khan y se despide de la manada."]),
    ],
    completa_dialogo=[
        completa(1, "—¡El cachorro de hombre es", "! —gritó Madre Loba al tigre.", "mío", ["tuyo", "de nadie", "perdido"]),
        completa(2, "Bagheera le explicó que la Flor Roja era en realidad el", ".", "fuego", ["agua", "viento", "hielo"]),
    ],
    testigo_ocular=[
        testigo(1, "El Consejo de la manada", "mowgli_consejo",
                "De noche, sobre una roca grande y plana, un lobo gris viejo; alrededor, doce lobos sentados en círculo bajo una luna llena; a un costado, una pantera negra; junto a un niño pequeño, un oso pardo de pie.",
                [("¿Qué astro iluminaba la escena?", "La luna llena", ["El sol", "Una estrella fugaz", "Un eclipse"]),
                 ("¿Qué animal negro estaba a un costado?", "Una pantera", ["Un oso negro", "Un caballo", "Un gato doméstico"]),
                 ("¿Qué animal estaba de pie junto al niño?", "Un oso pardo", ["Un elefante", "Un mono", "Un ciervo"])]),
        testigo(2, "La aldea de los hombres", "mowgli_aldea",
                "Atardecer en una aldea; una cabaña de barro con techo de paja; frente a la puerta, una vasija de barro con brasas encendidas; un niño de pelo negro y largo mira escondido tras un arbusto; un perro flaco junto a la cabaña.",
                [("¿De qué estaba hecha la vasija con fuego?", "Barro", ["Metal", "Madera", "Vidrio"]),
                 ("¿De qué era el techo de la cabaña?", "Paja", ["Tejas rojas", "Madera", "Piedra"]),
                 ("¿Qué animal flaco aparece junto a la cabaña?", "Un perro", ["Un cerdo", "Una cabra", "Un gato"])]),
    ],
    cazador_intrusos=[
        cazador(1, "La selva de Seeonee",
                "La selva estaba llena de flores, mariposas y juncos junto al río, y entre las sombras se movía la silueta elegante de Bagheera, la pantera negra.",
                "mowgli-selva-bg", "Selva densa y verde con un río al fondo y luz filtrada entre los árboles; suelo con hierba y espacio libre para colocar 6 objetos.",
                [lib("flores", "Flores de la selva"),
                 lib("mariposa", "Mariposa"),
                 lib("juncos", "Juncos del río"),
                 new("pantera-negra", "Pantera negra", "Pantera negra elegante sentada, de perfil, con ojos verdes brillantes, fondo transparente."),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("semaforo", "Semáforo", True)]),
        cazador(2, "La Flor Roja",
                "Mowgli corrió a la aldea y volvió con una vasija de barro llena de brasas y una rama encendida; Shere Khan, el tigre, lo esperaba entre la maleza.",
                "mowgli-flor-roja-bg", "Claro de la selva de noche, con luna llena, rocas y arbustos; suelo de tierra con espacio libre para colocar 6 objetos.",
                [new("vasija-brasas", "Vasija de barro con brasas", "Vasija de barro marrón con brasas anaranjadas brillando en su interior, fondo transparente."),
                 new("rama-encendida", "Rama encendida", "Rama de árbol con la punta ardiendo con llamas naranjas, fondo transparente."),
                 new("tigre-bengala", "Tigre Shere Khan", "Tigre de Bengala grande, de pie y de perfil, con gesto de rugido, fondo transparente."),
                 lib("extintor-incendios", "Extintor de incendios", True),
                 lib("microondas", "Microondas", True),
                 lib("secador-pelo", "Secador de pelo", True)]),
    ],
    busca_imagen=[
        busca(1, "Los hermanos de Mowgli",
              "Sobre la gran Roca del Consejo, bajo la luz de la luna, el viejo lobo Akela esperaba en silencio.",
              "Lobo Akela", "mowgli-roca-consejo",
              "Selva de noche con luna llena y una gran roca plana. Sobre la roca, en la parte central superior, un lobo gris viejo de pie, con un contorno de luz suave que lo distingue; abajo, otros lobos más pequeños sentados en círculo. Escena muy recargada: alrededor de la roca hay muchos lobos, lianas, helechos, luciérnagas, una pantera y un oso entre los árboles, y otras rocas redondeadas.",
              (10, 35, 30, 50)),
        busca(2, "Los hermanos de Mowgli",
              "Cerca de un tronco caído, junto al río, ardían las brasas de la vasija de barro de Mowgli.",
              "Vasija de barro con brasas", "mowgli-orilla-rio",
              "Orilla de un río en la selva con un tronco caído y helechos. En la parte inferior izquierda, una vasija de barro con brasas anaranjadas brillando, que destaca levemente del terreno.",
              (55, 15, 32, 31.25)),
    ],
    comics_desordenados=[
        comic(1, "Un niño en la cueva", "mowgli", 1, [
            "El chacal Tabaqui habla con Padre Lobo a la entrada de una cueva, al atardecer.",
            "Un bebé humano gatea hacia la cueva, entre cachorros de lobo.",
            "Shere Khan asoma su enorme cabeza por la entrada y Madre Loba lo enfrenta.",
            "Madre Loba abraza al niño entre sus cachorros mientras el tigre se aleja."]),
        comic(2, "La Flor Roja", "mowgli", 5, [
            "Mowgli, ya mayor, escucha a Bagheera junto a una roca, de noche.",
            "Mowgli corre hacia una aldea y llena una vasija de barro con brasas.",
            "En el Consejo, Mowgli levanta una rama encendida frente a Shere Khan y los lobos.",
            "Mowgli se aleja de la selva hacia la aldea mientras Baloo y Bagheera lo miran."]),
    ],
)

# ============================================================================
# 3. RATÓN PÉREZ (Luis Coloma)
# ============================================================================
add_book(
    "Ratón Pérez", ["Ratón Pérez", "Raton Perez", "Pérez"],
    rafaga_vf=[
        rafaga("Al rey Buby se le cayó su primer diente. Siguiendo la costumbre, escribió una atenta carta a Ratón Pérez y puso la carta con el diente bajo su almohada.", [
            ("El rey Buby escribió una carta a Ratón Pérez.", True),
            ("Buby puso el diente bajo la almohada.", True),
            ("Buby guardó el diente en un cajón de su escritorio.", False)]),
        rafaga("Ratón Pérez vivía con su familia en una caja de galletas, en el sótano de la confitería Prast. Era un ratón muy elegante, con sombrero de paja y lentes de oro.", [
            ("Ratón Pérez vivía en una caja de galletas.", True),
            ("Ratón Pérez usaba sombrero de paja.", True),
            ("Ratón Pérez vivía en un castillo de piedra.", False)]),
    ],
    emoticono_dialogo=[
        emoticono("raton_perez_buby_asustado",
                  "El pequeño rey Buby, con pijama y una corona, sentado en su cama con los ojos muy abiertos y asustado, mirando a un ratoncito con sombrero de paja y lentes que está de pie sobre su almohada.",
                  "¡Hay un ratón con sombrero y lentes de oro sobre mi almohada!",
                  ["¡Qué rico estuvo el desayuno de hoy!", "¡Mañana iré de paseo al campo con mi madre!", "¡Por fin terminé mis tareas del colegio!"]),
        emoticono("raton_perez_reverencia",
                  "Ratón Pérez, un ratoncito con sombrero de paja, lentes dorados, zapatos de tela y una cartera roja al hombro, quitándose el sombrero con una gran reverencia frente al rey, de noche.",
                  "Buenas noches, Majestad; vengo a recoger su diente.",
                  ["¡Fuera de aquí, ratón, no quiero verte!", "¡Vengo a ayudarte a hornear una torta!", "¡Tengo frío, préstame tu abrigo!"]),
    ],
    imagen_pixelada=[
        pixelada("raton_perez_personaje",
                 "Ratón Pérez: ratoncito gris de pie, con sombrero de paja, lentes de oro redondos, zapatos de tela cruda y cartera roja cruzada en la espalda.",
                 "Ratón Pérez", ["Un gato atigrado", "El rey Buby", "Gilito", "La Reina Madre"]),
        pixelada("raton_perez_caja_galletas",
                 "Gran caja de galletas de lata redonda, con una puertita y ventanitas pequeñas, convertida en casa de ratones, dentro de un sótano con estantes de dulces.",
                 "Caja de galletas", ["Palacio Real", "Casa de muñecas", "Botella de vidrio", "Castillo de arena"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 640,
            "Ratón Pérez llevaba un sombrero de paja, lentes de oro y una cartera roja.",
            "La imagen contradictoria muestra a Ratón Pérez con casco de bombero y una mochila verde.",
            [("raton_perez_sombrero_paja", "Sombrero de paja", "Un ratoncito gris con un sombrero de paja sobre la cabeza, de frente."),
             ("raton_perez_lentes_oro", "Lentes de oro", "Primer plano de la cara de un ratón con lentes redondos dorados."),
             ("raton_perez_cartera_roja", "Cartera roja", "Un ratón visto de espaldas con una cartera roja cruzada sobre la espalda.")],
            ("raton_perez_casco_bombero", "Ratón con casco de bombero", "Un ratoncito con casco rojo de bombero y mochila verde, de pie.")),
        contradiccion(2, 650,
            "El rey Buby era un niño muy pequeño que vivía en un palacio de Madrid.",
            "La imagen contradictoria muestra a Buby como un anciano de barba larga viviendo en una cabaña del bosque.",
            [("raton_perez_buby_palacio", "Buby en el palacio", "Un niño pequeño con corona de rey, parado en un gran salón de palacio con cortinas rojas."),
             ("raton_perez_buby_reina", "Buby con su madre", "Un niño con corona abrazando a una reina con vestido azul y corona pequeña."),
             ("raton_perez_palacio_madrid", "Palacio Real", "Fachada de un gran palacio de piedra clara con balcones y banderas, de día.")],
            ("raton_perez_anciano_cabana", "Anciano en cabaña", "Un anciano de barba blanca larga y corona dorada sentado frente a una cabaña de madera en el bosque.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "El diente del rey", [
            "Al rey Buby se le cae su primer diente de leche.",
            "La Reina Madre le aconseja escribir una atenta carta a Ratón Pérez.",
            "Buby coloca la carta con el diente bajo su almohada y se queda esperando.",
            "Ratón Pérez aparece sobre la almohada y saluda con una reverencia.",
            "El rey, asombrado, se acerca a conversar con el ratoncito."]),
        reconstruccion(2, "El viaje por Madrid", [
            "Ratón Pérez explica que debe ir a recoger el diente de otro niño llamado Gilito.",
            "El rey se vuelve tan pequeño como un ratón y sigue a Pérez por un agujero.",
            "Ratón Pérez lo guía por agujeros y tuberías hasta el sótano de la confitería Prast.",
            "Llegan a la caja de galletas, donde Buby conoce a la familia de Pérez.",
            "Después van a la pobre casa de Gilito para recoger su diente."]),
    ],
    completa_dialogo=[
        completa(1, "Ratón Pérez se quitó el", "hasta los pies y saludó al rey con una reverencia.", "sombrero", ["zapato", "abrigo", "guante"]),
        completa(2, "Ratón Pérez vivía en una caja de galletas, en el sótano de la confitería", ".", "Prast", ["Palacio", "Luna", "Dulce"]),
    ],
    testigo_ocular=[
        testigo(1, "La habitación del rey", "raton_perez_dormitorio",
                "Dormitorio de un niño rey, de noche: cama grande con dosel azul; sobre la almohada una carta cerrada con sello rojo y un pequeño diente; sobre la mesita de noche, una vela encendida; a los pies de la cama, un osito de peluche.",
                [("¿De qué color era el dosel de la cama?", "Azul", ["Rojo", "Verde", "Amarillo"]),
                 ("¿Qué había sobre la mesita de noche?", "Una vela encendida", ["Un reloj despertador", "Un vaso de leche", "Una lámpara eléctrica"]),
                 ("¿Qué había a los pies de la cama?", "Un osito de peluche", ["Un perro", "Un balón", "Un violín"])]),
        testigo(2, "La casa de Ratón Pérez", "raton_perez_casa_interior",
                "Interior de una caja de galletas de lata convertida en casa de ratones: una ratona con delantal azul sirve la mesa, con trozos de queso; dos ratoncitas hijas (una con vestido rosa cantando, otra con lazo amarillo); una lámpara hecha con un dedal.",
                [("¿De qué color era el delantal de la ratona?", "Azul", ["Rojo", "Blanco", "Verde"]),
                 ("¿Qué comida había sobre la mesa?", "Trozos de queso", ["Pescados", "Frutas", "Sopa"]),
                 ("¿De qué estaba hecha la lámpara?", "De un dedal", ["De una taza", "De una cuchara", "De una nuez"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El dormitorio del rey Buby",
                "En el dormitorio del pequeño rey había una cama de madera, una corona dorada y una carta con un diente esperando bajo la almohada.",
                "raton-perez-dormitorio-bg", "Dormitorio infantil de palacio, de noche, con una ventana grande y una alfombra roja en el suelo, sin objetos pequeños (espacio libre para 6 objetos).",
                [lib("cama-madera", "Cama de madera"),
                 new("corona-rey", "Corona del rey", "Corona dorada con pequeñas joyas rojas y azules, tamaño pequeño, fondo transparente."),
                 new("carta-diente", "Carta con diente", "Carta cerrada con sello rojo y un diente pequeño apoyado sobre ella, fondo transparente."),
                 lib("tv", "Televisor de pantalla plana", True),
                 lib("laptop", "Computadora portátil", True),
                 lib("consola", "Consola de videojuegos", True)]),
        cazador(2, "La casa de Ratón Pérez",
                "En el sótano de la confitería, la casa de Ratón Pérez se veía rodeada de su sombrero de paja, sus lentes de oro y la gran caja de galletas.",
                "raton-perez-sotano-bg", "Sótano de una confitería con estantes de madera y frascos de dulces, penumbra cálida, suelo de piedra con espacio libre para 6 objetos.",
                [new("sombrero-paja", "Sombrero de paja", "Pequeño sombrero de paja con cinta marrón, fondo transparente."),
                 new("lentes-oro", "Lentes de oro", "Lentes redondos con montura dorada, fondo transparente."),
                 new("caja-galletas", "Caja de galletas", "Caja de galletas de lata redonda y decorada, con una puertita pequeña recortada, fondo transparente."),
                 lib("microondas", "Microondas", True),
                 lib("impresora", "Impresora", True),
                 lib("semaforo", "Semáforo", True)]),
    ],
    busca_imagen=[
        busca(1, "Ratón Pérez",
              "Bajo la almohada del rey, apenas asomaba una carta cerrada con un diente dentro.",
              "Carta con diente", "raton-perez-cama",
              "Cama grande de rey vista desde arriba, con mantas azules y almohada blanca. En el centro-derecha, bajo la almohada, asoma una carta cerrada con sello rojo y un diente apoyado encima, con un contorno algo más marcado que las mantas. Escena muy recargada: la cama está llena de almohadones, peluches, libros, una corona, mantas con distintos dibujos y juguetes esparcidos.",
              (35, 45, 50, 30)),
        busca(2, "Ratón Pérez",
              "En un rincón del sótano de la confitería, entre estantes de dulces, brillaba la caja de galletas donde vivía Ratón Pérez.",
              "Caja de galletas", "raton-perez-sotano",
              "Sótano de confitería con estantes de frascos de dulces. En la parte inferior izquierda, una caja de galletas de lata con una puertita, de un tono algo más claro que el suelo y los estantes.",
              (55, 10, 32, 31.25)),
    ],
    comics_desordenados=[
        comic(1, "La carta al ratón", "raton_perez", 1, [
            "El rey Buby, un niño con corona, muestra con sorpresa su diente caído a su madre la reina.",
            "Buby escribe una carta con una pluma en su escritorio.",
            "Buby coloca la carta con el diente bajo su almohada y se acuesta.",
            "Ratón Pérez aparece sobre la almohada, con sombrero de paja y lentes de oro, y se inclina ante el rey."]),
        comic(2, "La visita a la casa de Pérez", "raton_perez", 5, [
            "Ratón Pérez toma de la mano al rey Buby, ya del tamaño de un ratón, junto a un agujero en la pared.",
            "Los dos caminan por una cañería oscura y estrecha.",
            "Llegan a una caja de galletas donde espera la familia de Pérez.",
            "Buby saluda a la ratona y a sus dos hijas, que lo reciben con alegría."]),
    ],
)

# ============================================================================
# 4. LOS CISNES SALVAJES (Andersen)
# ============================================================================
add_book(
    "Los cisnes salvajes", ["cisnes salvajes", "cisnes"],
    rafaga_vf=[
        rafaga("Elisa tenía once hermanos príncipes. Su cruel madrastra, la reina, los convirtió en cisnes salvajes que volaban de día y recuperaban su forma humana al caer la noche.", [
            ("Elisa tenía once hermanos.", True),
            ("La madrastra convirtió a los príncipes en cisnes.", True),
            ("Los príncipes eran cisnes solo durante la noche.", False)]),
        rafaga("Para salvar a sus hermanos, Elisa tejió once camisas con ortigas, unas plantas que queman las manos. Mientras trabajaba, no podía pronunciar ni una sola palabra.", [
            ("Las camisas se tejieron con ortigas.", True),
            ("Elisa podía hablar mientras tejía.", False),
            ("Elisa tejió veinte camisas.", False)]),
    ],
    emoticono_dialogo=[
        emoticono("cisnes_elisa_reconoce",
                  "Elisa, una joven de cabello largo y vestido sencillo verde, en un bosque al atardecer, mirando hacia el cielo con lágrimas de emoción a once cisnes blancos que vuelan con coronas doradas.",
                  "¡Son mis hermanos! ¡Esos once cisnes son mis hermanos!",
                  ["¡Qué lindo día para pescar!", "¡Estoy muy feliz de vivir en el palacio del rey!", "¡Nunca he visto un cisne en mi vida!"]),
        emoticono("cisnes_reina_malvada",
                  "La reina madrastra, con corona y vestido oscuro y mirada fría, con los brazos extendidos lanzando un hechizo hacia once jóvenes en el patio de un palacio.",
                  "¡Volad como cisnes salvajes y alejaos de este castillo!",
                  ["¡Bienvenidos, mis queridos hijos, a cenar!", "¡Les regalo un baile para esta noche!", "¡Qué felices estamos todos en el palacio!"]),
    ],
    imagen_pixelada=[
        pixelada("cisnes_elisa",
                 "Elisa, joven de cabello largo castaño y vestido sencillo verde, de pie en un bosque con luz suave, con expresión dulce y triste.",
                 "Elisa", ["La reina madrastra", "La anciana del bosque", "El hada Morgana", "Una princesa del reino vecino"]),
        pixelada("cisnes_once_cisnes",
                 "Once cisnes blancos, cada uno con una pequeña corona dorada en la cabeza, volando juntos sobre el mar al atardecer.",
                 "Los once cisnes", ["Una bandada de gansos", "Un grupo de gaviotas", "Los patos del estanque", "Un barco de velas blancas"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 660,
            "Elisa tejía camisas con ortigas verdes que le quemaban las manos.",
            "La imagen contradictoria muestra a Elisa tejiendo con lana blanca y suave, sentada junto al fuego, sin ningún dolor.",
            [("cisnes_ortigas_cementerio", "Ortigas junto al cementerio", "Ortigas verdes altas creciendo entre lápidas de un cementerio, de noche."),
             ("cisnes_manos_rojas", "Manos enrojecidas de Elisa", "Primer plano de dos manos de niña enrojecidas y llenas de ronchas, sosteniendo ortigas."),
             ("cisnes_camisa_verde", "Camisa verde tejida", "Una camisa de color verde grisáceo, hecha de ortigas, doblada sobre el regazo de Elisa.")],
            ("cisnes_elisa_lana", "Elisa con lana blanca", "Elisa sentada en un sillón junto a una chimenea encendida, tejiendo lana blanca y sonriendo tranquila.")),
        contradiccion(2, 670,
            "Los once hermanos eran príncipes por la noche y cisnes durante el día.",
            "La imagen contradictoria muestra a los hermanos convertidos en cisnes en plena noche, bajo la luna, cuando en el cuento volvían a ser príncipes.",
            [("cisnes_bandada_dia", "Cisnes volando de día", "Once cisnes volando bajo un cielo azul y soleado sobre el mar."),
             ("cisnes_principes_noche", "Príncipes al anochecer", "Once jóvenes con coronas doradas sentados en una cueva junto a Elisa al anochecer."),
             ("cisnes_amanecer", "Cisnes al amanecer", "Cisnes blancos despegando desde la playa cuando sale el sol, el cielo es anaranjado.")],
            ("cisnes_cisnes_noche", "Cisnes bajo la luna", "Once cisnes con coronas durmiendo sobre las rocas de una playa, bajo una luna llena y cielo estrellado.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La maldición de la reina", [
            "El rey viudo se casa con una reina malvada que no quiere a sus hijos.",
            "La reina convierte a los once príncipes en cisnes salvajes y los echa del castillo.",
            "Elisa es enviada a vivir con una familia campesina, lejos del palacio.",
            "Al cumplir quince años, Elisa regresa al castillo, pero su padre no la reconoce.",
            "Elisa huye al bosque en busca de sus hermanos."]),
        reconstruccion(2, "Las camisas de ortigas", [
            "Los once cisnes cargan a Elisa en una red y la llevan volando sobre el mar.",
            "En sueños, un hada le revela que debe tejer camisas con ortigas del cementerio.",
            "Elisa teje en silencio y un rey que cazaba en el bosque se enamora de ella.",
            "Acusada de bruja, Elisa es llevada a la hoguera mientras termina las camisas.",
            "Los cisnes llegan volando, Elisa les lanza las camisas y los hermanos recuperan su forma humana."]),
    ],
    completa_dialogo=[
        completa(1, "La cruel madrastra convirtió a los once príncipes en", "salvajes.", "cisnes", ["patos", "águilas", "cuervos"]),
        completa(2, "Para romper el hechizo, Elisa debía tejer once camisas con", "y no hablar hasta terminarlas.", "ortigas", ["lana", "seda", "algodón"]),
    ],
    testigo_ocular=[
        testigo(1, "Los cisnes y Elisa", "cisnes_red_cisnes",
                "Atardecer sobre el mar; once cisnes blancos con una pequeña corona dorada en la cabeza vuelan llevando una red hecha de juncos en la que viaja Elisa, con un vestido verde; el sol rojo baja sobre el horizonte.",
                [("¿Qué llevaban los cisnes sobre la cabeza?", "Una pequeña corona dorada", ["Un sombrero de plumas", "Un lazo rojo", "Nada"]),
                 ("¿En qué llevaban a Elisa?", "En una red de juncos", ["En una canasta de mimbre", "En una barca", "En una manta"]),
                 ("¿De qué color era el vestido de Elisa?", "Verde", ["Azul", "Rojo", "Blanco"])]),
        testigo(2, "El cementerio de las ortigas", "cisnes_cementerio_noche",
                "Un cementerio antiguo de noche con luna; lápidas de piedra grises; ortigas verdes altas entre las tumbas; Elisa arrodillada recogiendo ortigas con las manos enrojecidas; un búho posado sobre una lápida.",
                [("¿Qué animal estaba sobre una lápida?", "Un búho", ["Un cuervo", "Un gato negro", "Un murciélago"]),
                 ("¿Qué recogía Elisa?", "Ortigas", ["Flores blancas", "Setas", "Manzanas"]),
                 ("¿Cómo estaban las manos de Elisa?", "Rojas e hinchadas", ["Cubiertas con guantes", "Sucias de barro", "Vendadas"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El lago del bosque",
                "Cerca del lago, los juncos se mecían, los lirios flotaban sobre el agua y un cisne blanco nadaba entre las flores silvestres.",
                "cisnes-lago-bg", "Lago tranquilo en un bosque al amanecer, con orilla de pasto y agua clara, árboles al fondo; espacio libre para 6 objetos.",
                [lib("cisne", "Cisne blanco"),
                 lib("juncos", "Juncos"),
                 lib("lirios", "Lirios de agua"),
                 lib("flores", "Flores silvestres"),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("nave-espacial", "Nave espacial", True)]),
        cazador(2, "El cementerio de las ortigas",
                "De noche, entre las tumbas del cementerio, crecían las ortigas que Elisa debía recoger para tejer las camisas de sus hermanos.",
                "cisnes-cementerio-bg", "Cementerio antiguo de noche con luna llena, niebla suave y suelo de tierra; espacio libre para 6 objetos.",
                [new("ortigas", "Ortigas", "Manojo de ortigas verdes con hojas dentadas, fondo transparente."),
                 new("lapida-piedra", "Lápida de piedra", "Lápida de piedra gris antigua con una pequeña cruz y musgo, fondo transparente."),
                 lib("audifonos", "Audífonos inalámbricos", True),
                 lib("impresora", "Impresora", True),
                 lib("patineta", "Patineta eléctrica", True),
                 lib("laptop", "Computadora portátil", True)]),
    ],
    busca_imagen=[
        busca(1, "Los cisnes salvajes",
              "Sobre una roca de la orilla, entre la espuma de las olas, una corona dorada brillaba sobre la cabeza del cisne más pequeño.",
              "Corona del cisne", "cisnes-orilla",
              "Playa rocosa al atardecer con varios cisnes blancos y el mar al fondo. En la parte derecha, un cisne más pequeño con una corona dorada, cuyo brillo lo hace destacar levemente del resto de la bandada. Escena muy recargada: hay once cisnes blancos y muchos otros pájaros, rocas, algas, espuma, nubes y velas lejanas.",
              (38, 60, 30, 50)),
        busca(2, "Los cisnes salvajes",
              "Detrás de las altas ortigas del cementerio, un viejo búho observaba a Elisa con ojos amarillos.",
              "Búho", "cisnes-cementerio-busca",
              "Cementerio de noche con ortigas y algunas lápidas. En la parte superior derecha, un búho marrón de ojos amarillos posado sobre una lápida, con un contorno algo más marcado que las ortigas.",
              (15, 65, 25, 40)),
    ],
    comics_desordenados=[
        comic(1, "Los príncipes se vuelven cisnes", "cisnes", 1, [
            "La reina madrastra, de pie en el patio del castillo, extiende los brazos frente a once príncipes.",
            "Los once príncipes se transforman en cisnes con coronas doradas entre una nube de plumas.",
            "Los cisnes salen volando por encima del castillo.",
            "Los cisnes vuelan sobre el bosque rumbo al mar mientras la reina sonríe desde una torre."]),
        comic(2, "La hoguera", "cisnes", 5, [
            "Elisa, con vestido gris, teje en silencio una camisa de ortigas.",
            "Un rey montado a caballo ve a Elisa en el bosque y se enamora de ella.",
            "Elisa, en una carreta rumbo a la hoguera, lleva las camisas verdes bajo la mirada de la multitud.",
            "Once cisnes bajan del cielo; Elisa les lanza las camisas y aparecen once príncipes, el menor con un ala de cisne en lugar de un brazo."]),
    ],
)

# ============================================================================
# 5. EL CUENTO DE PERICO EL CONEJO / LA ARDILLA NOGALINA (Beatrix Potter)
#    Desafío 1 de cada juego -> Perico | Desafío 2 -> Nogalina
# ============================================================================
add_book(
    "El cuento de Perico el Conejo / La ardilla Nogalina", ["Perico", "Nogalina"],
    rafaga_vf=[
        rafaga("Mamá Coneja advirtió a Perico y a sus hermanas que no fueran al huerto del señor McGregor, porque allí su padre había tenido un accidente. Pero Perico, muy desobediente, se coló por debajo de la cerca.", [
            ("Perico fue al huerto del señor McGregor.", True),
            ("Mamá Coneja le dio permiso para entrar al huerto.", False),
            ("Perico pasó por debajo de la cerca.", True)]),
        rafaga("Nogalina y sus hermanos ardillas navegaron en balsas hasta la isla del Viejo Brown, el búho. Los demás le llevaban regalos y le pedían permiso con respeto, pero Nogalina lo molestaba cantándole adivinanzas.", [
            ("Las ardillas viajaron hasta la isla del búho.", True),
            ("Nogalina fue respetuoso con el búho.", False),
            ("Nogalina le cantaba adivinanzas al búho.", True)]),
    ],
    emoticono_dialogo=[
        emoticono("perico_asustado",
                  "Perico, un conejito marrón con chaqueta azul de botones dorados, corriendo aterrado entre hileras de lechugas en un huerto, con el señor McGregor detrás de él con un rastrillo.",
                  "¡Socorro, el señor McGregor me persigue!",
                  ["¡Qué día tan tranquilo para dormir la siesta!", "¡Mamá, ya terminé mi tarea!", "¡Hoy invité a mis amigos a tomar el té!"]),
        emoticono("nogalina_viejo_brown_enojado",
                  "El Viejo Brown, un búho grande y enojado, con las plumas erizadas y los ojos amarillos muy abiertos, sobre la rama de un roble hueco, mirando fijamente a una pequeña ardilla roja.",
                  "¡Ya no aguanto más tus travesuras, Nogalina!",
                  ["¡Qué lindo es tu baile, quédate a cenar!", "¡Gracias por tus regalos, los guardaré!", "¡Esta noche iré a pescar al río!"]),
    ],
    imagen_pixelada=[
        pixelada("perico_conejo",
                 "Perico, un conejito marrón de orejas largas, con una chaqueta azul de botones dorados, sentado sobre la hierba de un huerto.",
                 "Perico", ["Colita de Algodón", "Mamá Coneja", "El señor McGregor", "Nogalina"]),
        pixelada("nogalina_viejo_brown",
                 "Un búho gris grande, de plumaje en tonos marrones y ojos amarillos, posado en la rama de un roble antiguo.",
                 "Viejo Brown", ["Nogalina", "Un halcón", "Un gallo", "Un cuervo"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 680,
            "Perico llevaba una chaqueta azul con botones dorados cuando entró al huerto.",
            "La imagen contradictoria muestra a Perico con una chaqueta roja de lunares y un sombrero de copa.",
            [("perico_chaqueta_azul", "Perico con chaqueta azul", "Perico, conejo marrón, pasando bajo una cerca de madera, con una chaqueta azul de botones dorados."),
             ("perico_espantapajaros", "Chaqueta azul en el espantapájaros", "Un espantapájaros en un huerto vestido con una pequeña chaqueta azul de botones dorados y zapatos diminutos."),
             ("perico_botones_dorados", "Botones dorados", "Primer plano de una tela azul con tres botones dorados brillantes.")],
            ("perico_chaqueta_lunares", "Perico con chaqueta de lunares", "Perico, conejo marrón, con chaqueta roja de lunares blancos y un sombrero de copa negro.")),
        contradiccion(2, 690,
            "Nogalina era una ardilla de pelaje rojizo y cola larga y esponjosa.",
            "La imagen contradictoria muestra a una ardilla verde con una cola corta y lisa como la de un ratón.",
            [("nogalina_ardilla_roja", "Ardilla roja", "Una ardilla de pelaje rojizo sentada sobre una rama, con una cola larga y esponjosa."),
             ("nogalina_cola_esponjosa", "Cola esponjosa", "Primer plano de una cola de ardilla roja larga y muy esponjosa."),
             ("nogalina_ardillas_balsa", "Ardillas en balsa", "Tres ardillas rojas navegando en una balsa de ramas sobre un lago, usando sus colas como velas.")],
            ("nogalina_ardilla_verde", "Ardilla verde de cola corta", "Una ardilla de pelaje verde con una cola corta, delgada y sin pelo, sentada sobre una rama.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "Perico en el huerto", [
            "Mamá Coneja prohíbe a sus hijos entrar al huerto del señor McGregor.",
            "Perico se cuela bajo la cerca y se come lechugas, judías y rábanos.",
            "El señor McGregor lo descubre y lo persigue con un rastrillo; Perico pierde su chaqueta y sus zapatos.",
            "Perico se esconde en una regadera y estornuda, pero logra escapar.",
            "Cansado y enfermo, vuelve a casa y su mamá le da una taza de té de manzanilla."]),
        reconstruccion(2, "El castigo de Nogalina", [
            "Las ardillas llegan a la isla del Viejo Brown en balsas de ramas.",
            "Cada día le llevan un regalo al búho y le piden permiso para recoger nueces.",
            "Nogalina, en lugar de obedecer, le canta adivinanzas y se burla de él.",
            "El Viejo Brown lo atrapa y lo lleva a su árbol hueco.",
            "Nogalina logra escapar, pero pierde su cola en la huida."]),
    ],
    completa_dialogo=[
        completa(1, "Mamá Coneja le dio a Perico una taza de té de", "para su dolor de barriga.", "manzanilla", ["chocolate", "limón", "menta"]),
        completa(2, "Las ardillas navegaron hasta la isla del búho usando sus", "como velas.", "colas", ["chaquetas", "bufandas", "sombreros"]),
    ],
    testigo_ocular=[
        testigo(1, "El huerto del señor McGregor", "perico_huerto",
                "Huerto soleado con hileras de lechugas verdes y zanahorias; en primer plano una regadera roja sobre el suelo; un espantapájaros con una chaqueta azul y zapatos pequeños; al fondo una cerca blanca de madera con dos gorriones encima.",
                [("¿Qué llevaba puesto el espantapájaros?", "Una chaqueta azul y zapatos pequeños", ["Un sombrero rojo", "Una capa negra", "Un delantal"]),
                 ("¿De qué color era la regadera?", "Roja", ["Azul", "Verde", "Amarilla"]),
                 ("¿Cuántos gorriones había sobre la cerca?", "Dos", ["Uno", "Tres", "Cuatro"])]),
        testigo(2, "La isla del Viejo Brown", "nogalina_isla",
                "Una pequeña isla con un gran roble de tronco hueco; en una rama frente al hueco, un búho gris; tres ardillas rojas en la orilla junto a una balsa de ramas; una ardilla lleva una cesta con escarabajos; cielo nublado.",
                [("¿Dónde vivía el búho?", "En el hueco de un roble", ["En una cueva", "En un nido en el suelo", "En una cabaña"]),
                 ("¿Cuántas ardillas había en la orilla?", "Tres", ["Una", "Cinco", "Siete"]),
                 ("¿Qué llevaba una ardilla en la cesta?", "Escarabajos", ["Nueces", "Manzanas", "Pescados"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El huerto del señor McGregor",
                "En el huerto crecían lechugas y rábanos, y en un rincón colgaba la chaqueta azul que Perico perdió en su huida.",
                "perico-huerto-bg", "Huerto soleado con cerca de madera al fondo y tierra labrada; espacio libre para colocar 6 objetos.",
                [new("lechuga", "Lechuga", "Lechuga verde fresca y grande, fondo transparente."),
                 new("rabano", "Rábano", "Dos rábanos rojos con hojas verdes, fondo transparente."),
                 new("chaqueta-azul-botones", "Chaqueta azul con botones", "Chaqueta azul pequeña con botones dorados, fondo transparente."),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("semaforo", "Semáforo", True),
                 lib("microondas", "Microondas", True)]),
        cazador(2, "La isla del búho",
                "Las ardillas llegaron en una balsa de ramas hasta la isla del búho, donde juntaron nueces bajo los robles.",
                "nogalina-isla-bg", "Orilla de una isla con robles antiguos, hojas secas en el suelo y un lago al fondo; espacio libre para 6 objetos.",
                [new("balsa-ramas", "Balsa de ramas", "Pequeña balsa hecha de ramas atadas, vista de costado, fondo transparente."),
                 new("nueces", "Nueces", "Tres nueces marrones, una de ellas abierta, fondo transparente."),
                 lib("submarino", "Submarino", True),
                 lib("nave-espacial", "Nave espacial", True),
                 lib("esqui", "Pista de esquí", True),
                 lib("raqueta", "Raqueta de tenis", True)]),
    ],
    busca_imagen=[
        busca(1, "Perico el Conejo",
              "Colgada de un espantapájaros, la chaqueta azul de botones dorados de Perico se mecía con la brisa.",
              "Chaqueta azul", "perico-espantapajaros-busca",
              "Huerto soleado con hileras de verduras y un espantapájaros de paja. En la parte central-derecha, sobre el espantapájaros, una chaqueta azul grande con botones dorados que destaca levemente del huerto. Escena muy recargada: el huerto tiene muchas hileras de lechugas, repollos, zanahorias, regaderas, cestas, gorriones, conejos pequeños y varios espantapájaros cercanos.",
              (25, 50, 40, 37.5)),
        busca(2, "La ardilla Nogalina",
              "Junto a la orilla, entre las ramas, una pequeña balsa esperaba a las ardillas.",
              "Balsa de ramas", "nogalina-orilla",
              "Orilla de un lago en otoño con cañas y unas pocas ramas caídas. En la parte inferior, una balsa de ramas atadas, de tono algo más claro que la orilla y con contorno más marcado.",
              (65, 25, 50, 20)),
    ],
    comics_desordenados=[
        comic(1, "La travesura de Perico", "perico", 1, [
            "Mamá Coneja advierte a Perico y a sus hermanas en la puerta de su madriguera.",
            "Perico se cuela bajo la cerca del huerto.",
            "El señor McGregor persigue a Perico con un rastrillo.",
            "Perico, agotado, toma té de manzanilla en la cama mientras su mamá lo cuida."]),
        comic(2, "Nogalina y el búho", "perico", 5, [
            "Varias ardillas rojas navegan en balsas de ramas usando sus colas como velas.",
            "Las ardillas entregan regalos al Viejo Brown frente a su árbol.",
            "Nogalina baila y canta frente al búho, mientras las otras ardillas lo miran preocupadas.",
            "Nogalina huye veloz del árbol, sin su cola, que queda en la garra del búho."]),
    ],
)
# --- Perico y Nogalina son DOS libros distintos: se separan el desafío 1 (Perico) y el 2 (Nogalina) ---
_JUNTO = "El cuento de Perico el Conejo / La ardilla Nogalina"
_PERICO = "El cuento de Perico el Conejo"
_NOGALINA = "El cuento de la ardilla Nogalina"
_nuevo = {}
for _titulo, _juegos in NEW_DATASET.items():
    if _titulo == _JUNTO:
        _nuevo[_PERICO] = {g: [lst[0]] for g, lst in _juegos.items()}
        _nuevo[_NOGALINA] = {g: [lst[1]] for g, lst in _juegos.items()}
    else:
        _nuevo[_titulo] = _juegos
NEW_DATASET.clear()
NEW_DATASET.update(_nuevo)
KEYWORDS.pop(_JUNTO)
KEYWORDS[_PERICO] = ["Perico"]
KEYWORDS[_NOGALINA] = ["Nogalina"]

# ============================================================================
# 6. PULGARCITO (Perrault)
# ============================================================================
add_book(
    "Pulgarcito", ["Pulgarcito"],
    rafaga_vf=[
        rafaga("Pulgarcito era el menor de siete hermanos y era muy pequeño. Una noche escuchó que sus padres, por la pobreza, planeaban abandonar a los niños en el bosque. Por eso llenó sus bolsillos con piedrecitas blancas.", [
            ("Pulgarcito era el menor de siete hermanos.", True),
            ("Llenó sus bolsillos con piedrecitas blancas.", True),
            ("Sus padres eran muy ricos.", False)]),
        rafaga("Los niños llegaron a la casa de un ogro. Pulgarcito cambió los gorros de sus hermanos por las coronas de oro de las siete hijas del ogro, y así el ogro se equivocó en la oscuridad.", [
            ("El ogro tenía siete hijas.", True),
            ("Las hijas del ogro llevaban coronas de oro.", True),
            ("El ogro reconoció a los niños en la oscuridad.", False)]),
    ],
    emoticono_dialogo=[
        emoticono("pulgarcito_planea",
                  "Pulgarcito, un niño diminuto con gorro rojo, escondido bajo un banco de la cocina, escuchando con cara de preocupación a sus padres que hablan tristes junto a una mesa pobre.",
                  "Voy a llenar mis bolsillos con piedrecitas para encontrar el camino.",
                  ["¡Qué rica cena, quiero más sopa!", "¡Me iré a dormir, no escuché nada!", "¡Mañana pintaremos la casa de rojo!"]),
        emoticono("pulgarcito_ogro",
                  "Un ogro grande y barbudo con ojos rojos, de pie en la puerta de su casa en el bosque, oliendo el aire con la nariz levantada y un cuchillo grande en la mano.",
                  "¡Huelo carne fresca de niños!",
                  ["¡Qué buen día para pasear por el campo!", "¡Bienvenidos a mi fiesta, pequeños amigos!", "¡Acabo de comer pastel de manzana!"]),
    ],
    imagen_pixelada=[
        pixelada("pulgarcito_personaje",
                 "Pulgarcito, un niño diminuto del tamaño de un pulgar, con gorro rojo y ropa sencilla, de pie sobre una piedra en el bosque.",
                 "Pulgarcito", ["El leñador", "El hijo mayor", "El ogro", "El príncipe"]),
        pixelada("pulgarcito_botas",
                 "Un par de grandes botas de cuero marrón con hebillas doradas y destellos mágicos a su alrededor.",
                 "Las botas de siete leguas", ["Unas botas de lluvia", "Zapatos de baile", "Unas pantuflas", "Unos zuecos de madera"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 700,
            "Pulgarcito dejó caer piedrecitas blancas para marcar el camino de regreso a casa.",
            "La imagen contradictoria muestra a Pulgarcito soltando plumas de colores en lugar de piedrecitas blancas.",
            [("pulgarcito_bolsillos_piedras", "Bolsillos con piedrecitas", "Pulgarcito mostrando sus bolsillos llenos de piedrecitas blancas."),
             ("pulgarcito_camino_blanco", "Camino de piedrecitas blancas", "Un sendero de piedrecitas blancas brillando bajo la luna en un bosque oscuro."),
             ("pulgarcito_regreso_casa", "Niños siguiendo el camino", "Siete niños siguiendo un camino de piedrecitas blancas hacia una casa de campo iluminada.")],
            ("pulgarcito_plumas", "Pulgarcito soltando plumas", "Pulgarcito caminando por el bosque y dejando caer plumas de colores en el suelo.")),
        contradiccion(2, 710,
            "El ogro usaba unas botas mágicas que le permitían recorrer siete leguas de un solo paso.",
            "La imagen contradictoria muestra al ogro con zapatillas de ballet rosadas.",
            [("pulgarcito_ogro_paso", "Ogro dando un paso enorme", "Un ogro dando un paso gigante por encima de montañas y valles."),
             ("pulgarcito_botas_magicas", "Botas mágicas", "Un par de botas de cuero grandes con destellos y rayos de luz dorados."),
             ("pulgarcito_ogro_dormido", "Ogro dormido sobre una roca", "Un ogro durmiendo sentado sobre una roca, con las botas puestas, bajo la luz de la luna.")],
            ("pulgarcito_ogro_ballet", "Ogro con zapatillas de ballet", "Un ogro grande y barbudo con zapatillas de ballet rosadas y un tutú, bailando.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "Perdidos en el bosque", [
            "Pulgarcito escucha a sus padres planear que abandonarán a los niños por la falta de comida.",
            "Pulgarcito llena sus bolsillos de piedrecitas blancas.",
            "El leñador lleva a sus hijos al bosque, y Pulgarcito va dejando caer las piedrecitas.",
            "Siguiendo las piedrecitas brillantes, los niños vuelven a casa.",
            "Más tarde, en otra salida al bosque, usa migas de pan, pero los pájaros se las comen."]),
        reconstruccion(2, "La casa del ogro", [
            "Los niños, perdidos, ven una luz y llegan a una casa donde vive un ogro.",
            "La esposa del ogro los esconde, pero el ogro huele carne fresca.",
            "Pulgarcito cambia los gorros de sus hermanos por las coronas de las hijas del ogro.",
            "Por la noche, los niños escapan mientras el ogro se equivoca en la oscuridad.",
            "El ogro los persigue con sus botas de siete leguas, pero se duerme y Pulgarcito se las quita."]),
    ],
    completa_dialogo=[
        completa(1, "Pulgarcito llenó sus bolsillos de piedrecitas", "para encontrar el camino de regreso.", "blancas", ["negras", "rojas", "azules"]),
        completa(2, "El ogro usaba unas botas de siete", "que le permitían caminar muy rápido.", "leguas", ["metros", "pasos", "días"]),
    ],
    testigo_ocular=[
        testigo(1, "La casa del ogro", "pulgarcito_cocina_ogro",
                "Cocina rústica y oscura: una gran mesa de madera con una olla humeante y un cuchillo grande; una chimenea encendida; una mujer con delantal gris y pañuelo rojo en la cabeza; siete niños escondidos tras un baúl; en la pared, un par de botas grandes colgando.",
                [("¿Qué había sobre la mesa?", "Una olla humeante y un cuchillo", ["Un pastel y una vela", "Una jarra con flores", "Un libro abierto"]),
                 ("¿De qué color era el pañuelo de la mujer?", "Rojo", ["Azul", "Verde", "Negro"]),
                 ("¿Cuántos niños se escondían tras el baúl?", "Siete", ["Tres", "Cinco", "Diez"])]),
        testigo(2, "El camino de piedrecitas", "pulgarcito_sendero_luna",
                "Bosque de noche iluminado por luna llena; un sendero de piedrecitas blancas brillantes; Pulgarcito, diminuto, con gorro rojo, al inicio del sendero; seis niños lo siguen; un búho en una rama baja.",
                [("¿De qué color era el gorro de Pulgarcito?", "Rojo", ["Azul", "Verde", "Amarillo"]),
                 ("¿Cuántos niños seguían a Pulgarcito?", "Seis", ["Cuatro", "Siete", "Ocho"]),
                 ("¿Qué animal estaba en la rama?", "Un búho", ["Un cuervo", "Una ardilla", "Un murciélago"])]),
    ],
    cazador_intrusos=[
        cazador(1, "La cabaña del leñador",
                "En la humilde cabaña del leñador había un hacha, tablones de madera, una cesta con un poco de pan y una cama sencilla.",
                "pulgarcito-cabana-bg", "Interior de una cabaña humilde de madera con chimenea apagada y piso de tablas; espacio libre para 6 objetos.",
                [new("hacha", "Hacha del leñador", "Hacha de leñador con mango de madera y hoja de hierro, fondo transparente."),
                 lib("tablones", "Tablones de madera"),
                 lib("cesta-pan", "Cesta de pan"),
                 lib("cama-madera", "Cama de madera"),
                 lib("tv", "Televisor de pantalla plana", True),
                 lib("laptop", "Computadora portátil", True)]),
        cazador(2, "La casa del ogro",
                "En la casa del ogro había unas botas de siete leguas, una corona de oro de sus hijas y un cofre repleto de tesoros.",
                "pulgarcito-casa-ogro-bg", "Interior oscuro de una casa de ogro, con piedras y una chimenea al fondo, piso de piedra; espacio libre para 6 objetos.",
                [lib("botas", "Botas de siete leguas"),
                 new("corona-oro", "Corona de oro", "Pequeña corona dorada con puntas simples, fondo transparente."),
                 lib("cofre", "Cofre de tesoros"),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("radio", "Radio a pilas", True),
                 lib("impresora", "Impresora", True)]),
    ],
    busca_imagen=[
        busca(1, "Pulgarcito",
              "Entre las raíces de un viejo árbol, brillaba una de las piedrecitas blancas que Pulgarcito había dejado caer.",
              "Piedrecita blanca", "pulgarcito-bosque",
              "Primer plano del suelo de un bosque de noche, con luna y raíces gruesas de árboles. En la parte inferior, entre las raíces, una piedra blanca grande y lisa que brilla levemente bajo la luna. Escena muy recargada: el suelo está lleno de hojas, hongos, otras piedras de colores y formas parecidas, ramitas, migas de pan y pequeñas flores.",
              (55, 30, 40, 37.5)),
        busca(2, "Pulgarcito",
              "Colgadas junto a la chimenea de la casa del ogro, las enormes botas de siete leguas esperaban en la penumbra.",
              "Botas de siete leguas", "pulgarcito-casa-ogro-busca",
              "Interior de la casa del ogro con una chimenea y una olla. En la parte derecha, un par de botas de cuero colgando de la pared, con un leve destello mágico que las distingue de la penumbra.",
              (30, 68, 25, 40)),
    ],
    comics_desordenados=[
        comic(1, "Las piedrecitas blancas", "pulgarcito", 1, [
            "Pulgarcito, escondido bajo el banco, escucha a sus padres hablar tristes en la cocina.",
            "Pulgarcito llena sus bolsillos con piedrecitas blancas junto a un arroyo.",
            "Los siete hermanos caminan por el bosque con el leñador; Pulgarcito deja caer piedrecitas.",
            "Los niños regresan a casa siguiendo el camino de piedrecitas brillantes a la luz de la luna."]),
        comic(2, "Las botas del ogro", "pulgarcito", 5, [
            "El ogro de ojos rojos persigue a los niños dando pasos enormes con sus botas de siete leguas.",
            "El ogro, cansado, duerme sentado sobre una gran roca.",
            "Pulgarcito, diminuto, tira de las botas del ogro dormido.",
            "Pulgarcito se pone las botas gigantes, que se ajustan mágicamente, y se aleja corriendo."]),
    ],
)

# ============================================================================
# 7. BARBA AZUL (Perrault)
# ============================================================================
add_book(
    "Barba Azul", ["Barba Azul"],
    rafaga_vf=[
        rafaga("Un hombre muy rico tenía una barba azul que asustaba a todos. Pidió casarse con una joven del vecindario y ella aceptó después de visitar su magnífico castillo.", [
            ("Barba Azul era un hombre rico.", True),
            ("Su barba era de color rojo.", False),
            ("La joven se casó con él después de visitar su castillo.", True)]),
        rafaga("Antes de partir de viaje, Barba Azul le entregó a su esposa las llaves de todo el castillo. Le permitió abrir cualquier puerta menos la de una pequeña habitación, cuya llave era diminuta.", [
            ("Barba Azul le entregó las llaves del castillo.", True),
            ("Le prohibió abrir una pequeña habitación.", True),
            ("Le prohibió salir al jardín.", False)]),
    ],
    emoticono_dialogo=[
        emoticono("barba_azul_esposa_curiosa",
                  "Una joven esposa con vestido azul claro, sosteniendo una pequeña llave dorada frente a una puerta cerrada de madera, con expresión de curiosidad y nervios, en un pasillo de castillo.",
                  "¿Qué habrá dentro de esta habitación prohibida?",
                  ["¡Qué lindo jardín tiene el castillo!", "¡Por fin terminé de cocinar el almuerzo!", "¡Voy a guardar esta llave y olvidarme de ella!"]),
        emoticono("barba_azul_furioso",
                  "Un hombre alto con larga barba azul y capa oscura, con el rostro enfurecido y una espada en la mano, en el vestíbulo de un castillo.",
                  "¿Por qué la llave está manchada? ¡Abriste la puerta prohibida!",
                  ["¡Qué alegría volver a verte, querida!", "¡Te traje un regalo de mi viaje!", "¡Vamos a comer, tengo mucha hambre!"]),
    ],
    imagen_pixelada=[
        pixelada("barba_azul_personaje",
                 "Barba Azul: hombre alto y elegante con una larga barba de color azul oscuro, ropa lujosa de terciopelo y mirada seria.",
                 "Barba Azul", ["El rey", "El mago", "Un pirata", "El caballero"]),
        pixelada("barba_azul_llave",
                 "Una pequeña llave dorada con manchas rojas, apoyada sobre un cojín de terciopelo azul.",
                 "La llave manchada", ["La corona real", "Un collar de perlas", "Un reloj antiguo", "Una vela roja"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 720,
            "Barba Azul le entregó a su esposa un manojo de llaves para abrir los baúles y habitaciones del castillo.",
            "La imagen contradictoria muestra a Barba Azul entregando un ramo de flores amarillas en lugar de las llaves.",
            [("barba_azul_manojo_llaves", "Manojo de llaves", "Un gran manojo de llaves antiguas de hierro y una pequeña dorada, sobre una mesa."),
             ("barba_azul_baul_joyas", "Baúl con joyas", "Un baúl antiguo abierto, lleno de collares y monedas de oro."),
             ("barba_azul_esposa_castillo", "La esposa recorriendo el castillo", "Una joven con vestido azul y llaves en la mano, caminando por una galería con cuadros.")],
            ("barba_azul_ramo_flores", "Barba Azul con ramo de flores", "Barba Azul entregando un ramo de flores amarillas a su esposa, sonriendo.")),
        contradiccion(2, 730,
            "Barba Azul tenía una larga barba azul que asustaba a todos.",
            "La imagen contradictoria muestra a un hombre de barba rubia, corta y rizada, que sonríe amablemente.",
            [("barba_azul_a_caballo", "Barba Azul a caballo", "Un hombre de barba larga azul y capa oscura montando un caballo negro."),
             ("barba_azul_ninos_asustados", "Niños asustados", "Niños del pueblo escondidos tras una pared mirando con miedo a un hombre de barba azul."),
             ("barba_azul_retrato", "Retrato de Barba Azul", "Retrato pintado de un hombre con la barba azul peinada en dos puntas.")],
            ("barba_azul_barba_rubia", "Hombre de barba rubia", "Un hombre de barba rubia corta y rizada, vestido con ropa lujosa, sonriendo.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La llave prohibida", [
            "Barba Azul se casa con una joven y la lleva a vivir a su gran castillo.",
            "Barba Azul debe partir de viaje y le deja a su esposa todas las llaves.",
            "La esposa invita a sus amigas a recorrer el castillo y todas admiran sus riquezas.",
            "Vencida por la curiosidad, abre la puerta prohibida con la pequeña llave.",
            "Dentro de la habitación descubre el terrible secreto y la llave cae manchada."]),
        reconstruccion(2, "El rescate", [
            "Barba Azul regresa de improviso y le pide las llaves a su esposa.",
            "Al ver la llave manchada, Barba Azul comprende que ella abrió la puerta prohibida.",
            "La esposa pide un cuarto de hora para rezar y sube a la torre con su hermana Ana.",
            "Ana vigila desde la torre y por fin ve a los hermanos acercarse a caballo.",
            "Los hermanos llegan al castillo y ponen fin a Barba Azul."]),
    ],
    completa_dialogo=[
        completa(1, "Barba Azul tenía una barba de color", "que asustaba a todos.", "azul", ["roja", "verde", "blanca"]),
        completa(2, "La esposa subió a la torre con su hermana", "para esperar a sus hermanos.", "Ana", ["Laura", "María", "Rosa"]),
    ],
    testigo_ocular=[
        testigo(1, "El salón del castillo", "barba_azul_salon",
                "Lujoso salón de un castillo: una gran mesa cubierta con mantel rojo; un candelabro de cinco velas encendidas; un sofá de terciopelo verde; una ventana alta con cortinas azules; sobre la mesa, un manojo de llaves.",
                [("¿Cuántas velas tenía el candelabro?", "Cinco", ["Tres", "Siete", "Cuatro"]),
                 ("¿De qué color era el sofá?", "Verde", ["Rojo", "Azul", "Amarillo"]),
                 ("¿Qué había sobre la mesa?", "Un manojo de llaves", ["Un florero", "Un libro", "Una bandeja de frutas"])]),
        testigo(2, "La torre del castillo", "barba_azul_torre_ana",
                "Torre de piedra con una ventana alta; en ella, la esposa con vestido rosa y su hermana Ana con vestido amarillo, mirando un camino de tierra; a lo lejos una nube de polvo y dos jinetes con capas rojas; sol brillante y colinas verdes.",
                [("¿De qué color era el vestido de Ana?", "Amarillo", ["Rosa", "Verde", "Blanco"]),
                 ("¿Cuántos jinetes se veían a lo lejos?", "Dos", ["Uno", "Tres", "Cuatro"]),
                 ("¿De qué color eran las capas de los jinetes?", "Rojas", ["Azules", "Negras", "Verdes"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El tesoro del castillo",
                "En la sala del tesoro de Barba Azul brillaban un cofre de joyas, una copa de oro, una jarra de plata y un manojo de llaves antiguas.",
                "barba-azul-tesoro-bg", "Sala de un castillo con paredes de piedra, alfombra roja y estantes de madera vacíos; espacio libre para 6 objetos.",
                [lib("cofre", "Cofre de joyas"),
                 lib("copa", "Copa de oro"),
                 lib("jarra-plata", "Jarra de plata"),
                 new("llaves-antiguas", "Manojo de llaves", "Manojo de llaves antiguas de hierro con una llave pequeña dorada, fondo transparente."),
                 lib("microondas", "Microondas", True),
                 lib("telefono-movil", "Teléfono móvil", True)]),
        cazador(2, "El camino a la torre",
                "Desde la torre se veían llegar los hermanos con sus capas y sus espadas, galopando por el camino polvoriento.",
                "barba-azul-camino-bg", "Camino de tierra entre colinas verdes visto desde una torre, cielo azul con nubes; espacio libre para 6 objetos.",
                [lib("capa", "Capa de jinete"),
                 new("espada-caballero", "Espada de caballero", "Espada recta de caballero con empuñadura dorada, fondo transparente."),
                 lib("nave-espacial", "Nave espacial", True),
                 lib("consola", "Consola de videojuegos", True),
                 lib("monopatin", "Monopatín", True),
                 lib("semaforo", "Semáforo", True)]),
    ],
    busca_imagen=[
        busca(1, "Barba Azul",
              "Sobre una mesita del salón, junto al jarrón de flores, brillaba una pequeña llave dorada olvidada.",
              "Pequeña llave dorada", "barba-azul-salon-busca",
              "Primer plano de una mesita de un salón lujoso, con un jarrón de flores. En la parte central-inferior, una llave dorada grande sobre la mesa, cuyo brillo la distingue del mantel. Escena muy recargada: la mesita está llena de candelabros, copas, platos, otras llaves de distintos tamaños, joyas, cartas y adornos de porcelana.",
              (50, 25, 50, 30)),
        busca(2, "Barba Azul",
              "En lo alto de la torre, la hermana Ana miraba el horizonte con un largo catalejo de bronce.",
              "Catalejo", "barba-azul-torre-busca",
              "Torre de piedra con una ventana alta que da al campo. En la parte superior, Ana sostiene un catalejo de bronce, con un destello leve que lo distingue de la piedra.",
              (18, 42, 50, 20)),
    ],
    comics_desordenados=[
        comic(1, "La llave prohibida", "barba_azul", 1, [
            "Barba Azul entrega un manojo de llaves a su esposa en el vestíbulo y se despide con una maleta.",
            "La esposa, sola, recorre las salas del castillo con las llaves.",
            "Frente a una puerta pequeña, la esposa duda con la llave dorada en la mano.",
            "La esposa abre la puerta con la llave temblando de miedo."]),
        comic(2, "Los hermanos al rescate", "barba_azul", 5, [
            "Barba Azul regresa y mira furioso la llave que la esposa le entrega.",
            "La esposa y su hermana Ana suben a la torre.",
            "Desde la torre, Ana ve a lo lejos dos jinetes que galopan levantando polvo.",
            "Los dos hermanos llegan al patio del castillo con las espadas en alto."]),
    ],
)

# ============================================================================
# 8. LOS ZAPATOS ROJOS (Andersen)
# ============================================================================
add_book(
    "Los zapatos rojos", ["zapatos rojos"],
    rafaga_vf=[
        rafaga("Karen era una niña muy pobre que andaba descalza. Un zapatero le hizo con retazos de paño rojo unos zapatitos toscos. Los usó en el funeral de su madre.", [
            ("Karen era una niña pobre.", True),
            ("Karen tenía muchos zapatos de cuero.", False),
            ("Karen usó los zapatos rojos en el funeral de su madre.", True)]),
        rafaga("Karen fue adoptada por una anciana rica. Cuando fue a su confirmación, eligió unos zapatos rojos de charol brillante, aunque no era correcto usarlos en la iglesia.", [
            ("Una anciana adoptó a Karen.", True),
            ("Karen eligió zapatos rojos para su confirmación.", True),
            ("Karen eligió zapatos negros para la iglesia.", False)]),
    ],
    emoticono_dialogo=[
        emoticono("zapatos_karen_baila",
                  "Karen, una niña con vestido blanco y zapatos rojos brillantes, bailando sin control en un campo, con una cara de miedo y las manos extendidas.",
                  "¡No puedo parar de bailar, los zapatos no me obedecen!",
                  ["¡Qué lindo día para tomar una siesta!", "¡Estoy tan feliz de andar descalza!", "¡Voy a hacer un picnic con mis amigos!"]),
        emoticono("zapatos_angel",
                  "Un ángel con túnica blanca, alas y una espada brillante, serio, de pie ante la puerta de una iglesia frente a Karen.",
                  "¡Bailarás con tus zapatos rojos hasta quedar pálida y fría!",
                  ["¡Bienvenida a la fiesta, Karen!", "¡Te regalo unos zapatos nuevos de oro!", "¡Entra a comer pastel!"]),
    ],
    imagen_pixelada=[
        pixelada("zapatos_par_rojo",
                 "Un par de zapatos rojos brillantes de charol, con un pequeño lazo, sobre el suelo de piedra de una iglesia.",
                 "Los zapatos rojos", ["Unas botas de nieve", "Unas zapatillas deportivas", "Unas pantuflas azules", "Unos zuecos de madera"]),
        pixelada("zapatos_soldado",
                 "Un viejo soldado de barba roja larga y rizada, con un abrigo viejo, apoyado en una muleta junto a la puerta de una iglesia.",
                 "El soldado de barba roja", ["El zapatero", "El pastor", "El ángel", "El verdugo"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 740,
            "Karen se puso los zapatos rojos y no podía dejar de bailar por campos y bosques.",
            "La imagen contradictoria muestra a Karen sentada, tranquila, leyendo un libro con los zapatos puestos.",
            [("zapatos_baila_campo", "Karen bailando en el campo", "Karen bailando con los brazos extendidos en un campo de trigo, con zapatos rojos."),
             ("zapatos_saltan_pasto", "Zapatos que saltan", "Un par de zapatos rojos brillantes saltando sobre el pasto, con las piernas de Karen en el aire."),
             ("zapatos_baila_bosque", "Karen bailando entre árboles", "Karen con zapatos rojos bailando entre los árboles de un bosque en otoño.")],
            ("zapatos_karen_lee", "Karen leyendo tranquila", "Karen sentada en un banco leyendo un libro con zapatos rojos puestos, con expresión tranquila.")),
        contradiccion(2, 750,
            "Un ángel con una espada se le apareció a Karen delante de la iglesia.",
            "La imagen contradictoria muestra a un payaso con globos de colores frente a Karen.",
            [("zapatos_angel_espada", "Ángel con espada", "Un ángel con túnica blanca y una espada brillante frente a la puerta de una iglesia."),
             ("zapatos_angel_alas", "Ángel con alas desplegadas", "Un ángel con las alas abiertas sobre el tejado de una iglesia, rodeado de luz."),
             ("zapatos_karen_asustada", "Karen mirando al ángel", "Karen con zapatos rojos mirando hacia arriba con miedo, delante de un ángel.")],
            ("zapatos_payaso", "Payaso con globos", "Un payaso con globos de colores parado frente a Karen y la puerta de una iglesia.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "El primer baile", [
            "Karen, una niña pobre, recibe unos zapatitos rojos cosidos por un zapatero.",
            "Una anciana rica la adopta y le compra unos hermosos zapatos rojos nuevos.",
            "Karen los usa en la iglesia, pensando solo en ellos y no en rezar.",
            "Un viejo soldado de barba roja toca las suelas y los zapatos empiezan a bailar solos.",
            "Karen no puede detenerse y baila por campos y bosques."]),
        reconstruccion(2, "El castigo y el perdón", [
            "Un ángel con espada le dice que bailará hasta quedar pálida y fría.",
            "Karen llega a la casa del verdugo y le pide que le corte los pies con los zapatos.",
            "Los zapatos siguen bailando solos por el bosque, mientras Karen recibe pies de madera.",
            "Karen trabaja sirviendo en la casa del pastor y se arrepiente sinceramente.",
            "Con el corazón humilde, Karen reza, la luz inunda su alma y encuentra la paz."]),
    ],
    completa_dialogo=[
        completa(1, "Karen eligió unos zapatos", "porque le parecían los más hermosos.", "rojos", ["negros", "blancos", "azules"]),
        completa(2, "El viejo soldado dijo: «¡Qué hermosos zapatos de", "!»", "baile", ["trabajo", "lluvia", "nieve"]),
    ],
    testigo_ocular=[
        testigo(1, "La iglesia", "zapatos_iglesia_interior",
                "Interior de una iglesia antigua: bancos de madera con personas vestidas de negro; Karen de pie con vestido blanco y zapatos rojos brillantes que destacan; una anciana con bastón y vestido negro; un gran ventanal con vitrales azules.",
                [("¿De qué color eran los zapatos de Karen?", "Rojos", ["Negros", "Azules", "Blancos"]),
                 ("¿Qué llevaba la anciana en la mano?", "Un bastón", ["Un libro", "Un paraguas", "Una cesta"]),
                 ("¿De qué color eran los vitrales?", "Azules", ["Verdes", "Amarillos", "Rosados"])]),
        testigo(2, "El camino del bosque", "zapatos_bosque_otono",
                "Camino de otoño en un bosque con hojas naranjas; un par de zapatos rojos bailando en el aire con piernas de niña; un cuervo negro sobre una rama; un zorro rojizo mirando entre los arbustos; sol bajo entre los árboles.",
                [("¿Qué estación parecía ser?", "Otoño", ["Invierno", "Primavera", "Verano"]),
                 ("¿Qué animal negro estaba en la rama?", "Un cuervo", ["Un gato", "Un búho", "Una paloma"]),
                 ("¿Qué animal rojizo miraba entre los arbustos?", "Un zorro", ["Un lobo", "Un conejo", "Un ciervo"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El taller del zapatero",
                "En el taller del zapatero había unos zapatos rojos terminados, retazos de paño rojo y un par de botas de cuero.",
                "zapatos-taller-bg", "Taller de zapatero rústico con estante de madera, mesa de trabajo y ventana con luz cálida; espacio libre para 6 objetos.",
                [new("zapatos-rojos", "Zapatos rojos", "Par de zapatos rojos brillantes con un lazo pequeño, fondo transparente."),
                 new("tela-roja", "Retazos de paño rojo", "Tres trozos de tela roja doblados y apilados, fondo transparente."),
                 lib("botas", "Botas de cuero"),
                 lib("laptop", "Computadora portátil", True),
                 lib("impresora", "Impresora", True),
                 lib("extintor-incendios", "Extintor de incendios", True)]),
        cazador(2, "La iglesia del pueblo",
                "En la iglesia del pueblo había flores en el altar, velas encendidas y una campana en lo alto de la torre.",
                "zapatos-iglesia-bg", "Entrada de una iglesia de piedra con puerta de madera grande y escalones, sin objetos pequeños; espacio libre para 6 objetos.",
                [lib("flores", "Flores del altar"),
                 new("vela", "Vela encendida", "Vela blanca encendida con una pequeña llama, fondo transparente."),
                 new("campana", "Campana de iglesia", "Campana de bronce antigua, fondo transparente."),
                 lib("semaforo", "Semáforo", True),
                 lib("consola", "Consola de videojuegos", True),
                 lib("tv", "Televisor de pantalla plana", True)]),
    ],
    busca_imagen=[
        busca(1, "Los zapatos rojos",
              "Sobre el escalón de la entrada de la iglesia, un par de zapatos rojos brillaba bajo el sol.",
              "Zapatos rojos", "zapatos-iglesia-busca",
              "Entrada de una iglesia de piedra con tres escalones. En la parte inferior, un par de zapatos rojos grandes sobre el escalón, que destacan levemente por su color rojo apagado frente a la piedra sepia. Escena muy recargada: la entrada tiene muchos zapatos de distintos tipos, flores, velas, bancos, personas de espaldas y farolillos.",
              (62, 25, 50, 30)),
        busca(2, "Los zapatos rojos",
              "En la rama más alta de un árbol del camino, un cuervo observaba a Karen en silencio.",
              "Cuervo", "zapatos-camino-busca",
              "Camino de otoño con unos pocos árboles de hojas anaranjadas. En la parte superior derecha, un cuervo negro posado en una rama, con un contorno algo más marcado que el follaje.",
              (12, 58, 32, 31.25)),
    ],
    comics_desordenados=[
        comic(1, "Los zapatos de baile", "zapatos", 1, [
            "Un zapatero cose unos zapatitos rojos de tela para una niña pobre.",
            "Karen entra a la iglesia con los zapatos rojos nuevos, mirando solo sus pies.",
            "Un soldado de barba roja golpea las suelas diciendo que son zapatos de baile.",
            "Los zapatos empiezan a bailar con Karen por las calles del pueblo."]),
        comic(2, "La paz de Karen", "zapatos", 5, [
            "Un ángel con espada detiene a Karen ante la puerta de una iglesia.",
            "Karen, con pies de madera y muletas, trabaja como sirvienta en la casa del pastor.",
            "Karen reza con humildad en una habitación sencilla y una luz brillante entra por la ventana.",
            "Karen sonríe en paz mientras la luz la rodea."]),
    ],
)

# ============================================================================
# 9. BLANCANIEVES (Hermanos Grimm)
# ============================================================================
add_book(
    "Blancanieves", ["Blancanieves"],
    rafaga_vf=[
        rafaga("Blancanieves era una niña de piel blanca como la nieve y cabello negro como el ébano. Su madrastra, la reina, tenía un espejo mágico que siempre decía la verdad.", [
            ("Blancanieves tenía el cabello negro como el ébano.", True),
            ("El espejo mágico de la reina mentía.", False),
            ("La reina era la madrastra de Blancanieves.", True)]),
        rafaga("Cuando el espejo dijo que Blancanieves era más bella, la reina ordenó a un cazador llevarla al bosque. El cazador sintió lástima y la dejó escapar.", [
            ("La reina ordenó a un cazador llevarse a Blancanieves.", True),
            ("El cazador cumplió la orden sin dudar.", False),
            ("Blancanieves logró escapar.", True)]),
    ],
    emoticono_dialogo=[
        emoticono("blancanieves_reina_espejo",
                  "Una reina con corona negra y dorada y vestido morado, frente a un espejo mágico de marco dorado en el que brilla un rostro; la reina tiene el ceño fruncido.",
                  "¡Espejito, espejito, dime quién es la más bella del reino!",
                  ["¡Espejito, necesito que me prestes tu marco!", "¡Hoy haré un pastel de chocolate!", "¡Qué lindo día para salir a pasear!"]),
        emoticono("blancanieves_enanitos",
                  "Siete enanitos con gorros de colores, de pie junto a una mesa pequeña con siete platitos, mirando asombrados a una niña dormida en una de sus camitas.",
                  "¿Quién ha estado durmiendo en nuestras camitas?",
                  ["¡Ya es hora de dormir todos juntos!", "¡Mañana pintaremos la casa de azul!", "¡Qué rico huele el pastel de zanahoria!"]),
    ],
    imagen_pixelada=[
        pixelada("blancanieves_espejo",
                 "Un espejo mágico de marco dorado y adornos de flores, con un rostro de niebla verdosa brillando en su superficie, sobre una pared de piedra.",
                 "El espejo mágico", ["Un cuadro del rey", "Una ventana del palacio", "La puerta del castillo", "Un reloj de pared"]),
        pixelada("blancanieves_siete_enanitos",
                 "Siete enanitos con gorros de colores diferentes, cada uno con un pico o un farol, caminando en fila por un bosque.",
                 "Los siete enanitos", ["Los tres cerditos", "Los cuatro músicos", "Los dos hermanos", "Los cinco duendes"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 760,
            "La reina, disfrazada de anciana, le ofreció a Blancanieves una manzana roja envenenada.",
            "La imagen contradictoria muestra a la anciana ofreciendo una banana verde en lugar de una manzana roja.",
            [("blancanieves_anciana_cesta", "Anciana con cesta de manzanas", "Una anciana encorvada con capa oscura sostiene una cesta llena de manzanas rojas."),
             ("blancanieves_manzana_roja", "Manzana roja brillante", "Una manzana roja brillante con una pequeña mordida, sobre el suelo del bosque."),
             ("blancanieves_ventana_cabana", "Blancanieves en la ventana", "Blancanieves asomada a la ventana de una cabaña, con curiosidad.")],
            ("blancanieves_anciana_banana", "Anciana ofreciendo una banana", "Una anciana con capa oscura ofreciendo una banana verde a Blancanieves en la ventana.")),
        contradiccion(2, 770,
            "Los siete enanitos trabajaban cada día en una mina buscando oro y piedras preciosas.",
            "La imagen contradictoria muestra a los siete enanitos jugando fútbol en un campo de pasto.",
            [("blancanieves_enanitos_mina", "Enanitos entrando a la mina", "Siete enanitos con picos al hombro entrando a una mina por una boca oscura entre rocas."),
             ("blancanieves_carretilla_gemas", "Carretilla con gemas", "Una carretilla de madera llena de piedras preciosas de colores brillantes."),
             ("blancanieves_enanitos_faroles", "Enanitos con faroles", "Enanitos con faroles encendidos caminando por un túnel de roca.")],
            ("blancanieves_enanitos_futbol", "Enanitos jugando fútbol", "Siete enanitos con gorros de colores jugando fútbol con un balón en un campo de pasto.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "La huida al bosque", [
            "La reina le pregunta al espejo mágico quién es la más bella y este responde que Blancanieves.",
            "La reina ordena a un cazador llevarla al bosque.",
            "El cazador se compadece y deja que Blancanieves huya.",
            "Blancanieves encuentra una casita y se queda dormida en las camitas de los enanitos.",
            "Los siete enanitos regresan de la mina y la acogen."]),
        reconstruccion(2, "La manzana envenenada", [
            "La reina descubre que Blancanieves sigue viva y vive con los enanitos.",
            "Disfrazada de anciana, la reina visita la casita con una cesta de manzanas.",
            "Blancanieves muerde la manzana envenenada y cae como muerta.",
            "Los enanitos la colocan en un ataúd de cristal.",
            "Un príncipe la ve y, al moverse el ataúd, el pedazo de manzana sale de su garganta y ella despierta."]),
    ],
    completa_dialogo=[
        completa(1, "—Espejito, espejito, ¿quién es la más", "del reino? —preguntó la reina.", "bella", ["fuerte", "rápida", "joven"]),
        completa(2, "Blancanieves vivía con los siete", "en una casita del bosque.", "enanitos", ["gigantes", "cazadores", "caballeros"]),
    ],
    testigo_ocular=[
        testigo(1, "La casita de los enanitos", "blancanieves_casita_interior",
                "Interior de una casita: una mesa pequeña con siete platitos y siete vasitos; siete camitas pequeñas contra la pared, cada una con una colcha de color distinto; una ventana con cortinas verdes; Blancanieves dormida en una de las camas; una chimenea con una olla.",
                [("¿Cuántos platitos había sobre la mesa?", "Siete", ["Cinco", "Seis", "Ocho"]),
                 ("¿De qué color eran las cortinas?", "Verdes", ["Rojas", "Azules", "Blancas"]),
                 ("¿Dónde estaba Blancanieves?", "Dormida en una de las camitas", ["Sentada a la mesa", "Cocinando", "Mirando por la ventana"])]),
        testigo(2, "La reina y la manzana", "blancanieves_anciana_ventana",
                "Fachada de una cabaña de enanitos con una ventana abierta; Blancanieves asomada con cara curiosa; una anciana encorvada con capa negra sostiene una cesta de mimbre llena de manzanas rojas y ofrece una; un gato negro a sus pies.",
                [("¿Qué llevaba la anciana en la cesta?", "Manzanas rojas", ["Panes", "Peras amarillas", "Flores"]),
                 ("¿Qué animal estaba a los pies de la anciana?", "Un gato negro", ["Un perro", "Un conejo", "Una rata"]),
                 ("¿Dónde estaba Blancanieves?", "Asomada a una ventana", ["Sentada en el suelo", "Dentro de la cesta", "Subida a un árbol"])]),
    ],
    cazador_intrusos=[
        cazador(1, "La cocina de los enanitos",
                "En la casita de los enanitos había camitas de madera, una cesta de pan, platitos de madera y una colcha roja sobre la cama.",
                "blancanieves-cocina-bg", "Interior de una casita de bosque, con chimenea, ventana pequeña y piso de madera; espacio libre para 6 objetos.",
                [lib("cama-madera", "Camita de madera"),
                 lib("cesta-pan", "Cesta de pan"),
                 new("platitos", "Platitos de madera", "Tres platitos pequeños de madera, apilados, fondo transparente."),
                 lib("manta-roja", "Colcha roja"),
                 lib("tv", "Televisor de pantalla plana", True),
                 lib("lampara-led", "Lámpara LED", True)]),
        cazador(2, "El bosque encantado",
                "En el bosque, Blancanieves recogía flores y miraba las mariposas, sin saber que una manzana roja la esperaba.",
                "blancanieves-bosque-bg", "Claro del bosque soleado con árboles altos y pasto verde; espacio libre para 6 objetos.",
                [lib("flores", "Flores del bosque"),
                 lib("mariposa", "Mariposa"),
                 new("manzana-roja", "Manzana roja", "Manzana roja brillante con una hoja verde, fondo transparente."),
                 lib("semaforo", "Semáforo", True),
                 lib("microondas", "Microondas", True),
                 lib("audifonos", "Audífonos inalámbricos", True)]),
    ],
    busca_imagen=[
        busca(1, "Blancanieves",
              "Detrás de la puerta de madera de la casita, colgaba un pequeño pico de minero.",
              "Pico de minero", "blancanieves-casita-busca",
              "Entrada de una casita de enanitos con la puerta de madera abierta. En la parte izquierda, un pico de minero grande colgado de un clavo, de tono algo más claro que la puerta. Escena muy recargada: junto a la puerta hay muchas herramientas, faroles, gorros, botas, cestas, picos y palas de distintos tamaños.",
              (30, 8, 30, 50)),
        busca(2, "Blancanieves",
              "En el salón del castillo, el espejo mágico de marco dorado brillaba tras una cortina de terciopelo.",
              "Espejo mágico", "blancanieves-castillo-busca",
              "Salón del castillo de la reina con cortinas de terciopelo. En la parte derecha, un espejo de marco dorado alto con un brillo verdoso, que destaca levemente de la pared.",
              (20, 70, 20, 50)),
    ],
    comics_desordenados=[
        comic(1, "La huida de Blancanieves", "blancanieves", 1, [
            "La reina frunce el ceño frente al espejo mágico.",
            "Un cazador lleva a Blancanieves por el bosque oscuro.",
            "El cazador baja su arma y le indica a Blancanieves que huya.",
            "Blancanieves corre entre árboles hasta llegar a una casita pequeña con siete camitas."]),
        comic(2, "La manzana", "blancanieves", 5, [
            "La reina se disfraza de anciana en una torre llena de frascos de pociones.",
            "La anciana ofrece una manzana a Blancanieves en la ventana de la casita.",
            "Blancanieves cae dormida con la manzana a su lado y los enanitos llegan corriendo.",
            "Los enanitos lloran junto al ataúd de cristal en el bosque y un príncipe se acerca."]),
    ],
)

# ============================================================================
# 10. LA CENICIENTA (Hermanos Grimm)
# ============================================================================
add_book(
    "La Cenicienta", ["Cenicienta"],
    rafaga_vf=[
        rafaga("Cenicienta vivía con su madrastra y sus dos hermanastras, que la obligaban a hacer todo el trabajo de la casa. Todas las noches dormía junto al fogón, cubierta de cenizas.", [
            ("Cenicienta dormía junto al fogón.", True),
            ("Sus hermanastras la trataban con cariño.", False),
            ("Cenicienta tenía dos hermanastras.", True)]),
        rafaga("Cenicienta plantó una ramita de avellano sobre la tumba de su madre y la regó con sus lágrimas. Creció un árbol y un pajarito blanco le concedía lo que ella deseaba.", [
            ("Cenicienta plantó una ramita de avellano.", True),
            ("Un pajarito blanco le concedía sus deseos.", True),
            ("El árbol creció en el jardín del príncipe.", False)]),
    ],
    emoticono_dialogo=[
        emoticono("cenicienta_fogon",
                  "Cenicienta, joven con vestido gris sucio y delantal, sentada junto al fogón con cenizas, mirando con tristeza un plato de lentejas mezcladas con cenizas.",
                  "Nunca terminaré de separar las lentejas de las cenizas...",
                  ["¡Qué rica es la cena de esta noche!", "¡Mañana iré de paseo en carruaje!", "¡Estoy muy feliz de limpiar toda la casa!"]),
        emoticono("cenicienta_principe_zapatilla",
                  "El príncipe, con ropa elegante, sosteniendo una zapatilla dorada en las manos frente a una joven sentada en un banquito; detrás, las hermanastras observan con ansiedad.",
                  "¡Esta zapatilla dorada solo le calzará a mi verdadera novia!",
                  ["¡Quiero ir a pescar al río!", "¡Mi zapato favorito es el de cuero!", "¡No me interesa ningún zapato!"]),
    ],
    imagen_pixelada=[
        pixelada("cenicienta_personaje",
                 "Cenicienta, joven de cabello rubio recogido y vestido gris con delantal, con ceniza en las mejillas, sosteniendo una escoba.",
                 "Cenicienta", ["La madrastra", "Una hermanastra", "La reina", "Blancanieves"]),
        pixelada("cenicienta_zapatilla",
                 "Una zapatilla dorada brillante de tacón bajo, apoyada sobre un cojín rojo.",
                 "La zapatilla dorada", ["Una bota de cuero", "Una sandalia de playa", "Un zueco de madera", "Un zapato rojo"]),
    ],
    encuentra_contradiccion=[
        contradiccion(1, 780,
            "Cenicienta fue al baile con un vestido de oro y plata y zapatillas doradas.",
            "La imagen contradictoria muestra a Cenicienta en el baile con un disfraz de pirata con parche.",
            [("cenicienta_baja_escalera", "Cenicienta bajando la escalera", "Cenicienta con vestido de oro y plata bajando una gran escalera de mármol de un palacio."),
             ("cenicienta_zapatilla_escalon", "Zapatilla dorada en el escalón", "Una zapatilla dorada sobre un escalón de mármol blanco, de noche."),
             ("cenicienta_baila_principe", "Baile con el príncipe", "Cenicienta con vestido de oro y plata bailando con el príncipe en un gran salón iluminado.")],
            ("cenicienta_pirata", "Cenicienta disfrazada de pirata", "Cenicienta con sombrero de pirata, parche en el ojo y un loro en el hombro, en un salón de baile.")),
        contradiccion(2, 790,
            "El árbol de avellano de Cenicienta creció sobre la tumba de su madre.",
            "La imagen contradictoria muestra el árbol creciendo en la cima de un volcán en erupción.",
            [("cenicienta_tumba_ramita", "Ramita regada con lágrimas", "Una pequeña tumba con una ramita recién plantada, y Cenicienta llorando a su lado."),
             ("cenicienta_arbol_pajaro", "Árbol con pajarito blanco", "Un avellano grande y frondoso con un pajarito blanco posado en una rama sobre una tumba."),
             ("cenicienta_deseo_arbol", "Cenicienta pidiendo un deseo", "Cenicienta de pie bajo el avellano con las manos juntas, mirando hacia el pajarito blanco.")],
            ("cenicienta_arbol_volcan", "Árbol en un volcán", "Un avellano creciendo en la cima de un volcán en erupción, con lava naranja alrededor.")),
    ],
    reconstruccion_manuscrito=[
        reconstruccion(1, "El baile del príncipe", [
            "El rey anuncia una fiesta de tres días para que su hijo elija novia.",
            "La madrastra pone a prueba a Cenicienta con lentejas entre las cenizas, y las palomas y tórtolas la ayudan.",
            "Cenicienta pide un deseo al avellano y recibe un vestido de oro y plata.",
            "En el baile, el príncipe no quiere bailar con nadie más que con ella.",
            "Al caer la noche, Cenicienta escapa corriendo y se esconde en el palomar."]),
        reconstruccion(2, "La zapatilla dorada", [
            "En la tercera noche, Cenicienta huye tan rápido que pierde una zapatilla dorada en la escalera.",
            "El príncipe recoge la zapatilla y declara que se casará con quien le calce.",
            "Las hermanastras intentan probarse la zapatilla, pero no les cabe.",
            "Cenicienta se prueba la zapatilla y le queda perfectamente.",
            "El príncipe la reconoce y se casan."]),
    ],
    completa_dialogo=[
        completa(1, "Sobre la tumba de su madre, Cenicienta plantó una rama de", "y la regó con sus lágrimas.", "avellano", ["manzano", "roble", "pino"]),
        completa(2, "El príncipe se casaría con la joven a quien le calzara la zapatilla", ".", "dorada", ["roja", "negra", "azul"]),
    ],
    testigo_ocular=[
        testigo(1, "El fogón de Cenicienta", "cenicienta_cocina_fogon",
                "Cocina pobre: un fogón con brasas y ceniza; Cenicienta con vestido gris y delantal sentada en el suelo; un cuenco de madera con lentejas; una paloma blanca y dos tórtolas posadas sobre la repisa; un caldero negro colgando sobre el fuego.",
                [("¿Qué había en el cuenco de madera?", "Lentejas", ["Arroz", "Nueces", "Harina"]),
                 ("¿Cuántas aves había sobre la repisa?", "Tres", ["Dos", "Cuatro", "Seis"]),
                 ("¿De qué color era el vestido de Cenicienta?", "Gris", ["Rojo", "Azul", "Rosado"])]),
        testigo(2, "La escalera del palacio", "cenicienta_escalera_noche",
                "Gran escalera de mármol blanco con alfombra roja; en los escalones una zapatilla dorada; al pie de la escalera, el príncipe con capa azul sosteniendo un farol; un guardia con casco plateado; luna llena en el cielo.",
                [("¿De qué color era la alfombra de la escalera?", "Roja", ["Azul", "Verde", "Dorada"]),
                 ("¿Qué objeto había en los escalones?", "Una zapatilla dorada", ["Un abanico", "Una corona", "Un guante"]),
                 ("¿Qué sostenía el príncipe?", "Un farol", ["Una espada", "Un ramo de flores", "Un libro"])]),
    ],
    cazador_intrusos=[
        cazador(1, "El árbol de avellano",
                "Junto a la tumba de su madre creció el avellano, rodeado de flores y visitado por un pajarito blanco que cumplía los deseos de Cenicienta.",
                "cenicienta-avellano-bg", "Jardín tranquilo con una pequeña tumba de piedra y pasto verde, cielo claro; espacio libre para 6 objetos.",
                [new("avellano", "Árbol de avellano", "Árbol de avellano joven con hojas verdes y avellanas, fondo transparente."),
                 new("pajarito-blanco", "Pajarito blanco", "Pajarito blanco de pico pequeño y ojos negros, posado, fondo transparente."),
                 lib("flores", "Flores"),
                 lib("telefono-movil", "Teléfono móvil", True),
                 lib("radio", "Radio a pilas", True),
                 lib("patineta", "Patineta eléctrica", True)]),
        cazador(2, "El baile en el palacio",
                "En el gran salón del palacio había una zapatilla dorada, un vestido de oro y plata, copas de cristal y jarras de plata.",
                "cenicienta-salon-bg", "Gran salón de baile de un palacio con suelo de mármol y columnas, iluminado por candelabros; espacio libre para 6 objetos.",
                [new("zapatilla-dorada", "Zapatilla dorada", "Zapatilla dorada brillante de tacón bajo, fondo transparente."),
                 new("vestido-oro-plata", "Vestido de oro y plata", "Vestido de gala dorado con detalles plateados, fondo transparente."),
                 lib("copa", "Copa de cristal"),
                 lib("jarra-plata", "Jarra de plata"),
                 lib("audifonos", "Audífonos inalámbricos", True),
                 lib("calculadora", "Calculadora solar", True)]),
    ],
    busca_imagen=[
        busca(1, "La Cenicienta",
              "Entre las ramas del avellano, un pajarito blanco observaba a Cenicienta en silencio.",
              "Pajarito blanco", "cenicienta-avellano-busca",
              "Gran avellano con muchas hojas en un jardín. En la parte superior derecha, un pajarito blanco grande posado entre las ramas, más claro que el follaje y con contorno más marcado. Escena muy recargada: el avellano está lleno de hojas, avellanas, otros pajaritos de colores, nidos, lazos y flores.",
              (15, 50, 40, 37.5)),
        busca(2, "La Cenicienta",
              "En un rincón del fogón, escondido entre las cenizas, un cuenco de madera guardaba las lentejas que Cenicienta debía limpiar.",
              "Cuenco de lentejas", "cenicienta-fogon-busca",
              "Cocina pobre con fogón y cenizas. En la parte inferior izquierda, un cuenco de madera con lentejas, medio cubierto de cenizas, de tono algo más oscuro y definido que el suelo.",
              (65, 15, 50, 20)),
    ],
    comics_desordenados=[
        comic(1, "Un deseo bajo el avellano", "cenicienta", 1, [
            "Cenicienta llora junto a la tumba de su madre y planta una ramita de avellano.",
            "Con el tiempo, el avellano crece y un pajarito blanco se posa en sus ramas.",
            "Cenicienta pide un deseo y el pajarito le deja un vestido de oro y plata.",
            "Cenicienta, con el vestido, camina hacia el palacio iluminado por la luna."]),
        comic(2, "La zapatilla", "cenicienta", 5, [
            "Cenicienta corre por la escalera del palacio dejando atrás una zapatilla dorada.",
            "El príncipe recoge la zapatilla de la escalera.",
            "Las hermanastras intentan calzarse la zapatilla sin éxito.",
            "La zapatilla calza perfectamente en el pie de Cenicienta y el príncipe sonríe."]),
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


# ----------------------------------------------------------------------------
# Carga en la base de datos
# ----------------------------------------------------------------------------
def _setup_django():
    # Misma ruta que en populate_minigames.py (ajusta si mueves el archivo)
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()


def run():
    _setup_django()
    from catalog.models import Book
    from games.models import BookMinigame, Minigame

    print("=== POBLANDO MINIJUEGOS DE LOS 10 LIBROS NUEVOS ===")
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

        # Solo se borran los minijuegos DE ESTE libro (los demás libros no se tocan)
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
        export_images([NEW_DATASET], with_folders="--flat" not in sys.argv)
    else:
        run()
