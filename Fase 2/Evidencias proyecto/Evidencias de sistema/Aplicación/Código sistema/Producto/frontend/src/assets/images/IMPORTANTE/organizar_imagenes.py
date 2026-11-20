#!/usr/bin/env python3
"""
organizar_imagenes.py
=====================
Ordena las 561 imágenes nuevas dentro de assets/images/<carpeta>/ (emoticono, pixelado, contra,
testigo, cazador-intrusos, busca-imagen, comics), según las rutas que usan los minijuegos.

Uso (desde la raíz del frontend, donde está assets/):
    python organizar_imagenes.py RUTA_CON_LAS_IMAGENES              # COPIA los archivos
    python organizar_imagenes.py RUTA_CON_LAS_IMAGENES --move       # los MUEVE
    python organizar_imagenes.py RUTA_CON_LAS_IMAGENES --dry-run    # solo muestra qué haría

Opciones:
    --dest assets/images   carpeta base de destino (por defecto assets/images)
    --overwrite            reemplaza archivos que ya existen en el destino
    --no-recursive         no busca en subcarpetas de RUTA_CON_LAS_IMAGENES

Reconoce el nombre aunque venga con número delante ("12. sirenita_asombrada.png"), con sufijo
"(1)", en mayúsculas, o con guion en vez de guion bajo. Si la extensión no coincide con la esperada
(por ejemplo llegó .jpg y se espera .png) la convierte automáticamente si Pillow está instalado
(pip install pillow); si no, la copia tal cual y te avisa.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# carpeta/archivo esperado (561 imágenes)
EXPECTED = [
    "busca-imagen/barba-azul-salon-busca.jpg",
    "busca-imagen/barba-azul-torre-busca.jpg",
    "busca-imagen/bella-seto-busca.jpg",
    "busca-imagen/bella-torre-busca.jpg",
    "busca-imagen/blancanieves-casita-busca.jpg",
    "busca-imagen/blancanieves-castillo-busca.jpg",
    "busca-imagen/cenicienta-avellano-busca.jpg",
    "busca-imagen/cenicienta-fogon-busca.jpg",
    "busca-imagen/cisnes-cementerio-busca.jpg",
    "busca-imagen/cisnes-orilla.jpg",
    "busca-imagen/gigante-durazno-busca.jpg",
    "busca-imagen/gigante-muro-busca.jpg",
    "busca-imagen/guisante-cama-busca.jpg",
    "busca-imagen/guisante-puerta-busca.jpg",
    "busca-imagen/mowgli-orilla-rio.jpg",
    "busca-imagen/mowgli-roca-consejo.jpg",
    "busca-imagen/nogalina-orilla.jpg",
    "busca-imagen/perico-espantapajaros-busca.jpg",
    "busca-imagen/pulgarcito-bosque.jpg",
    "busca-imagen/pulgarcito-casa-ogro-busca.jpg",
    "busca-imagen/rapunzel-jardin-busca.jpg",
    "busca-imagen/rapunzel-torre-busca.jpg",
    "busca-imagen/raton-perez-cama.jpg",
    "busca-imagen/raton-perez-sotano.jpg",
    "busca-imagen/ricitos-dormitorio-busca.jpg",
    "busca-imagen/ricitos-mesa-busca.jpg",
    "busca-imagen/ruisenor-calle-busca.jpg",
    "busca-imagen/ruisenor-rosal-busca.jpg",
    "busca-imagen/rumpel-cuarto-busca.jpg",
    "busca-imagen/rumpel-fogata-busca.jpg",
    "busca-imagen/sirenita-gruta-bruja.jpg",
    "busca-imagen/sirenita-orilla.jpg",
    "busca-imagen/soldadito-acequia-busca.jpg",
    "busca-imagen/soldadito-mesa-busca.jpg",
    "busca-imagen/traje-desfile-busca.jpg",
    "busca-imagen/traje-taller-busca.jpg",
    "busca-imagen/zapatos-camino-busca.jpg",
    "busca-imagen/zapatos-iglesia-busca.jpg",
    "cazador-intrusos/anillo.png",
    "cazador-intrusos/avellano.png",
    "cazador-intrusos/bailarina-papel.png",
    "cazador-intrusos/balsa-ramas.png",
    "cazador-intrusos/barba-azul-camino-bg.jpg",
    "cazador-intrusos/barba-azul-tesoro-bg.jpg",
    "cazador-intrusos/barquito-papel.png",
    "cazador-intrusos/bella-jardin-bg.jpg",
    "cazador-intrusos/bella-torre-bg.jpg",
    "cazador-intrusos/blancanieves-bosque-bg.jpg",
    "cazador-intrusos/blancanieves-cocina-bg.jpg",
    "cazador-intrusos/caja-galletas.png",
    "cazador-intrusos/campana.png",
    "cazador-intrusos/carta-diente.png",
    "cazador-intrusos/cartel-prohibido.png",
    "cazador-intrusos/casa-osos.png",
    "cazador-intrusos/castillo-papel.png",
    "cazador-intrusos/cenicienta-avellano-bg.jpg",
    "cazador-intrusos/cenicienta-salon-bg.jpg",
    "cazador-intrusos/chaqueta-azul-botones.png",
    "cazador-intrusos/cisnes-cementerio-bg.jpg",
    "cazador-intrusos/cisnes-lago-bg.jpg",
    "cazador-intrusos/colchones.png",
    "cazador-intrusos/collar.png",
    "cazador-intrusos/concha-perla.png",
    "cazador-intrusos/copo-nieve.png",
    "cazador-intrusos/coral-rojo.png",
    "cazador-intrusos/corona-oro.png",
    "cazador-intrusos/corona-rey.png",
    "cazador-intrusos/durazno-flor.png",
    "cazador-intrusos/escalera-madera.png",
    "cazador-intrusos/espada-caballero.png",
    "cazador-intrusos/estrella-mar.png",
    "cazador-intrusos/farol.png",
    "cazador-intrusos/farolillos.png",
    "cazador-intrusos/gigante-invierno-bg.jpg",
    "cazador-intrusos/gigante-primavera-bg.jpg",
    "cazador-intrusos/guisante-castillo-bg.jpg",
    "cazador-intrusos/guisante-dormitorio-bg.jpg",
    "cazador-intrusos/guisante.png",
    "cazador-intrusos/hacha.png",
    "cazador-intrusos/hilo-dorado.png",
    "cazador-intrusos/huso.png",
    "cazador-intrusos/lapida-piedra.png",
    "cazador-intrusos/lechuga.png",
    "cazador-intrusos/lentes-oro.png",
    "cazador-intrusos/libro-antiguo.png",
    "cazador-intrusos/llave-oxidada.png",
    "cazador-intrusos/llaves-antiguas.png",
    "cazador-intrusos/manzana-roja.png",
    "cazador-intrusos/mowgli-flor-roja-bg.jpg",
    "cazador-intrusos/mowgli-selva-bg.jpg",
    "cazador-intrusos/nogalina-isla-bg.jpg",
    "cazador-intrusos/nueces.png",
    "cazador-intrusos/ortigas.png",
    "cazador-intrusos/pajarillo.png",
    "cazador-intrusos/pajarito-blanco.png",
    "cazador-intrusos/pantera-negra.png",
    "cazador-intrusos/perico-huerto-bg.jpg",
    "cazador-intrusos/pez-grande.png",
    "cazador-intrusos/platitos.png",
    "cazador-intrusos/pluma-tintero.png",
    "cazador-intrusos/pulgarcito-cabana-bg.jpg",
    "cazador-intrusos/pulgarcito-casa-ogro-bg.jpg",
    "cazador-intrusos/rabano.png",
    "cazador-intrusos/rama-encendida.png",
    "cazador-intrusos/raponchigos.png",
    "cazador-intrusos/rapunzel-cuarto-bg.jpg",
    "cazador-intrusos/rapunzel-jardin-bg.jpg",
    "cazador-intrusos/rata.png",
    "cazador-intrusos/raton-perez-dormitorio-bg.jpg",
    "cazador-intrusos/raton-perez-sotano-bg.jpg",
    "cazador-intrusos/ricitos-bosque-bg.jpg",
    "cazador-intrusos/ricitos-cocina-bg.jpg",
    "cazador-intrusos/rosa-roja.png",
    "cazador-intrusos/rosal-espinas.png",
    "cazador-intrusos/rueca.png",
    "cazador-intrusos/ruisenor-estudio-bg.jpg",
    "cazador-intrusos/ruisenor-jardin-bg.jpg",
    "cazador-intrusos/ruisenor.png",
    "cazador-intrusos/rumpel-cuarto-bg.jpg",
    "cazador-intrusos/rumpel-pago-bg.jpg",
    "cazador-intrusos/silla-madera.png",
    "cazador-intrusos/sirenita-barco-bg.jpg",
    "cazador-intrusos/sirenita-jardin-bg.jpg",
    "cazador-intrusos/soldadito-canal-bg.jpg",
    "cazador-intrusos/soldadito-cuarto-bg.jpg",
    "cazador-intrusos/soldadito-plomo.png",
    "cazador-intrusos/sombrero-bruja.png",
    "cazador-intrusos/sombrero-paja.png",
    "cazador-intrusos/tazon-avena.png",
    "cazador-intrusos/tela-roja.png",
    "cazador-intrusos/telar.png",
    "cazador-intrusos/tigre-bengala.png",
    "cazador-intrusos/tijeras.png",
    "cazador-intrusos/traje-palacio-bg.jpg",
    "cazador-intrusos/traje-taller-bg.jpg",
    "cazador-intrusos/trenza-dorada.png",
    "cazador-intrusos/vasija-brasas.png",
    "cazador-intrusos/vela.png",
    "cazador-intrusos/vestido-oro-plata.png",
    "cazador-intrusos/zapatilla-dorada.png",
    "cazador-intrusos/zapatos-iglesia-bg.jpg",
    "cazador-intrusos/zapatos-rojos.png",
    "cazador-intrusos/zapatos-taller-bg.jpg",
    "comics/barba_azul1.png",
    "comics/barba_azul2.png",
    "comics/barba_azul3.png",
    "comics/barba_azul4.png",
    "comics/barba_azul5.png",
    "comics/barba_azul6.png",
    "comics/barba_azul7.png",
    "comics/barba_azul8.png",
    "comics/bella1.png",
    "comics/bella2.png",
    "comics/bella3.png",
    "comics/bella4.png",
    "comics/bella5.png",
    "comics/bella6.png",
    "comics/bella7.png",
    "comics/bella8.png",
    "comics/blancanieves1.png",
    "comics/blancanieves2.png",
    "comics/blancanieves3.png",
    "comics/blancanieves4.png",
    "comics/blancanieves5.png",
    "comics/blancanieves6.png",
    "comics/blancanieves7.png",
    "comics/blancanieves8.png",
    "comics/cenicienta1.png",
    "comics/cenicienta2.png",
    "comics/cenicienta3.png",
    "comics/cenicienta4.png",
    "comics/cenicienta5.png",
    "comics/cenicienta6.png",
    "comics/cenicienta7.png",
    "comics/cenicienta8.png",
    "comics/cisnes1.png",
    "comics/cisnes2.png",
    "comics/cisnes3.png",
    "comics/cisnes4.png",
    "comics/cisnes5.png",
    "comics/cisnes6.png",
    "comics/cisnes7.png",
    "comics/cisnes8.png",
    "comics/gigante1.png",
    "comics/gigante2.png",
    "comics/gigante3.png",
    "comics/gigante4.png",
    "comics/gigante5.png",
    "comics/gigante6.png",
    "comics/gigante7.png",
    "comics/gigante8.png",
    "comics/guisante1.png",
    "comics/guisante2.png",
    "comics/guisante3.png",
    "comics/guisante4.png",
    "comics/guisante5.png",
    "comics/guisante6.png",
    "comics/guisante7.png",
    "comics/guisante8.png",
    "comics/mowgli1.png",
    "comics/mowgli2.png",
    "comics/mowgli3.png",
    "comics/mowgli4.png",
    "comics/mowgli5.png",
    "comics/mowgli6.png",
    "comics/mowgli7.png",
    "comics/mowgli8.png",
    "comics/perico1.png",
    "comics/perico2.png",
    "comics/perico3.png",
    "comics/perico4.png",
    "comics/perico5.png",
    "comics/perico6.png",
    "comics/perico7.png",
    "comics/perico8.png",
    "comics/pulgarcito1.png",
    "comics/pulgarcito2.png",
    "comics/pulgarcito3.png",
    "comics/pulgarcito4.png",
    "comics/pulgarcito5.png",
    "comics/pulgarcito6.png",
    "comics/pulgarcito7.png",
    "comics/pulgarcito8.png",
    "comics/rapunzel1.png",
    "comics/rapunzel2.png",
    "comics/rapunzel3.png",
    "comics/rapunzel4.png",
    "comics/rapunzel5.png",
    "comics/rapunzel6.png",
    "comics/rapunzel7.png",
    "comics/rapunzel8.png",
    "comics/raton_perez1.png",
    "comics/raton_perez2.png",
    "comics/raton_perez3.png",
    "comics/raton_perez4.png",
    "comics/raton_perez5.png",
    "comics/raton_perez6.png",
    "comics/raton_perez7.png",
    "comics/raton_perez8.png",
    "comics/ricitos1.png",
    "comics/ricitos2.png",
    "comics/ricitos3.png",
    "comics/ricitos4.png",
    "comics/ricitos5.png",
    "comics/ricitos6.png",
    "comics/ricitos7.png",
    "comics/ricitos8.png",
    "comics/ruisenor1.png",
    "comics/ruisenor2.png",
    "comics/ruisenor3.png",
    "comics/ruisenor4.png",
    "comics/ruisenor5.png",
    "comics/ruisenor6.png",
    "comics/ruisenor7.png",
    "comics/ruisenor8.png",
    "comics/rumpel1.png",
    "comics/rumpel2.png",
    "comics/rumpel3.png",
    "comics/rumpel4.png",
    "comics/rumpel5.png",
    "comics/rumpel6.png",
    "comics/rumpel7.png",
    "comics/rumpel8.png",
    "comics/sirenita1.png",
    "comics/sirenita2.png",
    "comics/sirenita3.png",
    "comics/sirenita4.png",
    "comics/sirenita5.png",
    "comics/sirenita6.png",
    "comics/sirenita7.png",
    "comics/sirenita8.png",
    "comics/soldadito1.png",
    "comics/soldadito2.png",
    "comics/soldadito3.png",
    "comics/soldadito4.png",
    "comics/soldadito5.png",
    "comics/soldadito6.png",
    "comics/soldadito7.png",
    "comics/soldadito8.png",
    "comics/traje1.png",
    "comics/traje2.png",
    "comics/traje3.png",
    "comics/traje4.png",
    "comics/traje5.png",
    "comics/traje6.png",
    "comics/traje7.png",
    "comics/traje8.png",
    "comics/zapatos1.png",
    "comics/zapatos2.png",
    "comics/zapatos3.png",
    "comics/zapatos4.png",
    "comics/zapatos5.png",
    "comics/zapatos6.png",
    "comics/zapatos7.png",
    "comics/zapatos8.png",
    "contra/barba_azul_a_caballo.png",
    "contra/barba_azul_barba_rubia.png",
    "contra/barba_azul_baul_joyas.png",
    "contra/barba_azul_esposa_castillo.png",
    "contra/barba_azul_manojo_llaves.png",
    "contra/barba_azul_ninos_asustados.png",
    "contra/barba_azul_ramo_flores.png",
    "contra/barba_azul_retrato.png",
    "contra/bella_anciana_huso.png",
    "contra/bella_castillo_cubierto.png",
    "contra/bella_castillo_isla.png",
    "contra/bella_princesa_cactus.png",
    "contra/bella_princesa_dedo.png",
    "contra/bella_rosas_blancas.png",
    "contra/bella_seto_rosas.png",
    "contra/bella_torre_alta.png",
    "contra/blancanieves_anciana_banana.png",
    "contra/blancanieves_anciana_cesta.png",
    "contra/blancanieves_carretilla_gemas.png",
    "contra/blancanieves_enanitos_faroles.png",
    "contra/blancanieves_enanitos_futbol.png",
    "contra/blancanieves_enanitos_mina.png",
    "contra/blancanieves_manzana_roja.png",
    "contra/blancanieves_ventana_cabana.png",
    "contra/cenicienta_arbol_pajaro.png",
    "contra/cenicienta_arbol_volcan.png",
    "contra/cenicienta_baila_principe.png",
    "contra/cenicienta_baja_escalera.png",
    "contra/cenicienta_deseo_arbol.png",
    "contra/cenicienta_pirata.png",
    "contra/cenicienta_tumba_ramita.png",
    "contra/cenicienta_zapatilla_escalon.png",
    "contra/cisnes_amanecer.png",
    "contra/cisnes_bandada_dia.png",
    "contra/cisnes_camisa_verde.png",
    "contra/cisnes_cisnes_noche.png",
    "contra/cisnes_elisa_lana.png",
    "contra/cisnes_manos_rojas.png",
    "contra/cisnes_ortigas_cementerio.png",
    "contra/cisnes_principes_noche.png",
    "contra/gigante_bienvenida_globos.png",
    "contra/gigante_cartel_prohibido.png",
    "contra/gigante_duraznos_flor.png",
    "contra/gigante_jardin_nevado.png",
    "contra/gigante_mira_ventana.png",
    "contra/gigante_muro_alto.png",
    "contra/gigante_ninos_agujero.png",
    "contra/gigante_pajaros_rama.png",
    "contra/guisante_joven_mojada.png",
    "contra/guisante_joven_sombrilla.png",
    "contra/guisante_pila_alta.png",
    "contra/guisante_reina_colchones.png",
    "contra/guisante_reina_piedra.png",
    "contra/guisante_relampago_castillo.png",
    "contra/guisante_rey_farol.png",
    "contra/guisante_verde_cojin.png",
    "contra/mowgli_cueva_lobos.png",
    "contra/mowgli_gatito.png",
    "contra/mowgli_huellas_tigre.png",
    "contra/mowgli_juega_lobeznos.png",
    "contra/mowgli_madre_loba_lame.png",
    "contra/mowgli_nido_aguilas.png",
    "contra/mowgli_ojos_tigre.png",
    "contra/mowgli_tigre_grande.png",
    "contra/nogalina_ardilla_roja.png",
    "contra/nogalina_ardilla_verde.png",
    "contra/nogalina_ardillas_balsa.png",
    "contra/nogalina_cola_esponjosa.png",
    "contra/perico_botones_dorados.png",
    "contra/perico_chaqueta_azul.png",
    "contra/perico_chaqueta_lunares.png",
    "contra/perico_espantapajaros.png",
    "contra/pulgarcito_bolsillos_piedras.png",
    "contra/pulgarcito_botas_magicas.png",
    "contra/pulgarcito_camino_blanco.png",
    "contra/pulgarcito_ogro_ballet.png",
    "contra/pulgarcito_ogro_dormido.png",
    "contra/pulgarcito_ogro_paso.png",
    "contra/pulgarcito_plumas.png",
    "contra/pulgarcito_regreso_casa.png",
    "contra/rapunzel_hiedra_torre.png",
    "contra/rapunzel_peinando.png",
    "contra/rapunzel_pelo_corto.png",
    "contra/rapunzel_torre_puerta_roja.png",
    "contra/rapunzel_torre_sin_puerta.png",
    "contra/rapunzel_trenza_gancho.png",
    "contra/rapunzel_trenza_ventana.png",
    "contra/rapunzel_ventana_alta.png",
    "contra/raton_perez_anciano_cabana.png",
    "contra/raton_perez_buby_palacio.png",
    "contra/raton_perez_buby_reina.png",
    "contra/raton_perez_cartera_roja.png",
    "contra/raton_perez_casco_bombero.png",
    "contra/raton_perez_lentes_oro.png",
    "contra/raton_perez_palacio_madrid.png",
    "contra/raton_perez_sombrero_paja.png",
    "contra/ricitos_dormida_pequena.png",
    "contra/ricitos_hamaca.png",
    "contra/ricitos_osos_miran.png",
    "contra/ricitos_pizza.png",
    "contra/ricitos_prueba_pequeno.png",
    "contra/ricitos_tres_camas.png",
    "contra/ricitos_tres_cucharas.png",
    "contra/ricitos_tres_tazones.png",
    "contra/ruisenor_ave_rosal.png",
    "contra/ruisenor_canta_luna.png",
    "contra/ruisenor_espina_luna.png",
    "contra/ruisenor_estudiante_rosa.png",
    "contra/ruisenor_joven_abraza_rosa.png",
    "contra/ruisenor_joven_joyas.png",
    "contra/ruisenor_nido_dormido.png",
    "contra/ruisenor_sobrino.png",
    "contra/rumpel_baila_fogata.png",
    "contra/rumpel_carretes_oro.png",
    "contra/rumpel_hombrecillo_hila.png",
    "contra/rumpel_mensajero_arbol.png",
    "contra/rumpel_paja_nieve.png",
    "contra/rumpel_paja_y_oro.png",
    "contra/rumpel_reina_entrega_bebe.png",
    "contra/rumpel_reina_hombrecillo.png",
    "contra/sirenita_caldero.png",
    "contra/sirenita_camino_algas.png",
    "contra/sirenita_casa_flores.png",
    "contra/sirenita_nadando_principe.png",
    "contra/sirenita_principe_arbol.png",
    "contra/sirenita_principe_arena.png",
    "contra/sirenita_pulpos.png",
    "contra/sirenita_templo_orilla.png",
    "contra/soldadito_bailarina_pierna.png",
    "contra/soldadito_bailarina_roja.png",
    "contra/soldadito_barco_pirata.png",
    "contra/soldadito_barquito_flota.png",
    "contra/soldadito_cinta_azul.png",
    "contra/soldadito_gesto_firme.png",
    "contra/soldadito_lentejuela.png",
    "contra/soldadito_ninos_barquito.png",
    "contra/traje_ayudantes.png",
    "contra/traje_carrete_oro.png",
    "contra/traje_emperador_monopatin.png",
    "contra/traje_estafadores_bolsa.png",
    "contra/traje_estafadores_pintura.png",
    "contra/traje_multitud.png",
    "contra/traje_palio.png",
    "contra/traje_rollos_seda.png",
    "contra/zapatos_angel_alas.png",
    "contra/zapatos_angel_espada.png",
    "contra/zapatos_baila_bosque.png",
    "contra/zapatos_baila_campo.png",
    "contra/zapatos_karen_asustada.png",
    "contra/zapatos_karen_lee.png",
    "contra/zapatos_payaso.png",
    "contra/zapatos_saltan_pasto.png",
    "emoticono/barba_azul_esposa_curiosa.png",
    "emoticono/barba_azul_furioso.png",
    "emoticono/bella_hada_enojada.png",
    "emoticono/bella_princesa_huso.png",
    "emoticono/blancanieves_enanitos.png",
    "emoticono/blancanieves_reina_espejo.png",
    "emoticono/bruja_del_mar.png",
    "emoticono/cenicienta_fogon.png",
    "emoticono/cenicienta_principe_zapatilla.png",
    "emoticono/cisnes_elisa_reconoce.png",
    "emoticono/cisnes_reina_malvada.png",
    "emoticono/gigante_conmovido.png",
    "emoticono/gigante_enojado.png",
    "emoticono/guisante_princesa_cama.png",
    "emoticono/guisante_princesa_empapada.png",
    "emoticono/mowgli_madre_loba.png",
    "emoticono/mowgli_shere_khan.png",
    "emoticono/nogalina_viejo_brown_enojado.png",
    "emoticono/perico_asustado.png",
    "emoticono/pulgarcito_ogro.png",
    "emoticono/pulgarcito_planea.png",
    "emoticono/rapunzel_bruja_llama.png",
    "emoticono/rapunzel_canta.png",
    "emoticono/raton_perez_buby_asustado.png",
    "emoticono/raton_perez_reverencia.png",
    "emoticono/ricitos_oso_enojado.png",
    "emoticono/ricitos_prueba_avena.png",
    "emoticono/ruisenor_canta_espina.png",
    "emoticono/ruisenor_estudiante_llora.png",
    "emoticono/rumpel_hombrecillo_baila.png",
    "emoticono/rumpel_molinera_llora.png",
    "emoticono/sirenita_asombrada.png",
    "emoticono/soldadito_bailarina.png",
    "emoticono/soldadito_duende.png",
    "emoticono/traje_emperador_telares.png",
    "emoticono/traje_nino_grita.png",
    "emoticono/zapatos_angel.png",
    "emoticono/zapatos_karen_baila.png",
    "pixelado/barba_azul_llave.png",
    "pixelado/barba_azul_personaje.png",
    "pixelado/bella_castillo_espinas.png",
    "pixelado/bella_huso.png",
    "pixelado/blancanieves_espejo.png",
    "pixelado/blancanieves_siete_enanitos.png",
    "pixelado/cenicienta_personaje.png",
    "pixelado/cenicienta_zapatilla.png",
    "pixelado/cisnes_elisa.png",
    "pixelado/cisnes_once_cisnes.png",
    "pixelado/gigante_durazno_flor.png",
    "pixelado/gigante_personaje.png",
    "pixelado/guisante_colchones.png",
    "pixelado/guisante_pequeno.png",
    "pixelado/mowgli_bagheera.png",
    "pixelado/mowgli_baloo.png",
    "pixelado/nogalina_viejo_brown.png",
    "pixelado/perico_conejo.png",
    "pixelado/pulgarcito_botas.png",
    "pixelado/pulgarcito_personaje.png",
    "pixelado/rapunzel_personaje.png",
    "pixelado/rapunzel_torre.png",
    "pixelado/raton_perez_caja_galletas.png",
    "pixelado/raton_perez_personaje.png",
    "pixelado/ricitos_osito.png",
    "pixelado/ricitos_personaje.png",
    "pixelado/ruisenor_ave.png",
    "pixelado/ruisenor_rosa_roja.png",
    "pixelado/rumpel_personaje.png",
    "pixelado/rumpel_rueca_oro.png",
    "pixelado/sirenita_palacio_coral.png",
    "pixelado/sirenita_principe_cubierta.png",
    "pixelado/soldadito_bailarina_papel.png",
    "pixelado/soldadito_personaje.png",
    "pixelado/traje_emperador.png",
    "pixelado/traje_telar_vacio.png",
    "pixelado/zapatos_par_rojo.png",
    "pixelado/zapatos_soldado.png",
    "testigo/barba_azul_salon.png",
    "testigo/barba_azul_torre_ana.png",
    "testigo/bella_cuarto_torre.png",
    "testigo/bella_salon_dormido.png",
    "testigo/blancanieves_anciana_ventana.png",
    "testigo/blancanieves_casita_interior.png",
    "testigo/cenicienta_cocina_fogon.png",
    "testigo/cenicienta_escalera_noche.png",
    "testigo/cisnes_cementerio_noche.png",
    "testigo/cisnes_red_cisnes.png",
    "testigo/gigante_jardin_primavera.png",
    "testigo/gigante_muro_nieve.png",
    "testigo/guisante_dormitorio_alto.png",
    "testigo/guisante_puerta_tormenta.png",
    "testigo/mowgli_aldea.png",
    "testigo/mowgli_consejo.png",
    "testigo/nogalina_isla.png",
    "testigo/perico_huerto.png",
    "testigo/pulgarcito_cocina_ogro.png",
    "testigo/pulgarcito_sendero_luna.png",
    "testigo/rapunzel_jardin_bruja.png",
    "testigo/rapunzel_torre_bosque.png",
    "testigo/raton_perez_casa_interior.png",
    "testigo/raton_perez_dormitorio.png",
    "testigo/ricitos_dormitorio_osos.png",
    "testigo/ricitos_mesa_osos.png",
    "testigo/ruisenor_escritorio.png",
    "testigo/ruisenor_jardin_noche.png",
    "testigo/rumpel_bosque_fogata.png",
    "testigo/rumpel_cuarto_paja.png",
    "testigo/sirenita_barco_noche.png",
    "testigo/sirenita_jardin_estatua.png",
    "testigo/soldadito_canal_lluvia.png",
    "testigo/soldadito_mesa_juguetes.png",
    "testigo/traje_calle_desfile.png",
    "testigo/traje_taller_interior.png",
    "testigo/zapatos_bosque_otono.png",
    "testigo/zapatos_iglesia_interior.png",
]


def norm(stem):
    s = stem.lower().strip()
    s = re.sub(r"^\s*\d+\s*[\.\-_)]\s*", "", s)   # "12. nombre" -> "nombre"
    s = re.sub(r"\s*\(\d+\)$", "", s)             # "nombre (1)" -> "nombre"
    return re.sub(r"[\s\-]+", "_", s)              # espacios y guiones -> "_"


def same_ext(a, b):
    f = lambda e: ".jpg" if e.lower() == ".jpeg" else e.lower()
    return f(a) == f(b)


def convert(src, dst):
    from PIL import Image  # puede lanzar ImportError
    img = Image.open(src)
    if dst.suffix.lower() in (".jpg", ".jpeg"):
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            rgba = img.convert("RGBA")
            bg.paste(rgba, mask=rgba.split()[-1])
            img = bg
        else:
            img = img.convert("RGB")
        img.save(dst, quality=95)
    else:
        img.save(dst)


def main():
    ap = argparse.ArgumentParser(description="Ordena las imágenes en assets/images/<carpeta>/")
    ap.add_argument("origen", help="carpeta donde están las imágenes generadas")
    ap.add_argument("--dest", default="assets/images", help="carpeta base de destino")
    ap.add_argument("--move", action="store_true", help="mover en vez de copiar")
    ap.add_argument("--dry-run", action="store_true", help="no modifica nada, solo informa")
    ap.add_argument("--overwrite", action="store_true", help="reemplazar archivos existentes")
    ap.add_argument("--no-recursive", action="store_true", help="no buscar en subcarpetas")
    a = ap.parse_args()

    origen, dest = Path(a.origen), Path(a.dest)
    if not origen.is_dir():
        sys.exit(f"[ERROR] No existe la carpeta de origen: {origen}")

    index = {}
    for rel in EXPECTED:
        folder, fname = rel.split("/", 1)
        k = norm(Path(fname).stem)
        if k in index:
            sys.exit(f"[ERROR] Dos imágenes esperadas se llaman igual: {index[k][0]}/{index[k][1]} y {rel}")
        index[k] = (folder, fname)

    files = origen.rglob("*") if not a.no_recursive else origen.glob("*")
    found, dup = {}, 0
    dest_abs = dest.resolve()
    for f in files:
        if not f.is_file() or f.suffix.lower() not in EXTS:
            continue
        if dest_abs in f.resolve().parents:          # ignora lo que ya está en el destino
            continue
        key = norm(f.stem)
        if key in index:
            if key in found:                          # duplicado: gana el más reciente
                dup += 1
                if f.stat().st_mtime <= found[key].stat().st_mtime:
                    continue
            found[key] = f

    placed = skipped = converted = 0
    warnings = []
    for key, src in sorted(found.items()):
        folder, fname = index[key]
        dst = dest / folder / fname
        if dst.exists() and not a.overwrite:
            skipped += 1
            continue
        accion = "mover" if a.move else "copiar"
        if a.dry_run:
            print(f"[dry-run] {accion}: {src} -> {dst}")
            placed += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if same_ext(src.suffix, dst.suffix):
            (shutil.move if a.move else shutil.copy2)(str(src), str(dst))
        else:
            try:
                convert(src, dst)
                converted += 1
                if a.move:
                    src.unlink()
                if folder == "cazador-intrusos" and dst.suffix.lower() == ".png":
                    warnings.append(f"{fname}: llegó como {src.suffix}; los objetos de cazador-intrusos "
                                    f"necesitan fondo transparente (revísalo).")
            except ImportError:
                alt = dst.with_suffix(src.suffix.lower())
                (shutil.move if a.move else shutil.copy2)(str(src), str(alt))
                warnings.append(f"{fname}: llegó como {src.suffix} y no se pudo convertir (falta Pillow); "
                                f"se guardó como {alt.name}. Instala Pillow o conviértelo a mano.")
        placed += 1

    esperados = len(EXPECTED)
    faltan = [rel for rel in EXPECTED if norm(Path(rel).stem) not in found]
    print("\n=== RESUMEN ===")
    print(f"Esperadas: {esperados} | Encontradas: {len(found)} | "
          f"{'Se colocarían' if a.dry_run else 'Colocadas'}: {placed} | "
          f"Ya existían (omitidas): {skipped} | Convertidas de formato: {converted}")
    if dup:
        print(f"Archivos duplicados ignorados (se usó el más reciente): {dup}")
    for w in warnings:
        print(f"[AVISO] {w}")
    if faltan:
        print(f"\nFaltan {len(faltan)} imágenes (lista completa en imagenes_faltantes.txt):")
        for rel in faltan[:15]:
            print(f"  - {rel}")
        if len(faltan) > 15:
            print(f"  ... y {len(faltan) - 15} más")
        if not a.dry_run:
            Path("imagenes_faltantes.txt").write_text("\n".join(faltan), encoding="utf-8")
    else:
        print("\n✓ Están todas las imágenes.")


if __name__ == "__main__":
    main()
