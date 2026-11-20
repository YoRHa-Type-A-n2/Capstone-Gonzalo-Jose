import os
import sys
from pathlib import Path
import django
import zipfile
import re
import shutil
from urllib.parse import unquote
from decimal import Decimal
from bs4 import BeautifulSoup
from django.core.files import File
from django.conf import settings

# Configurar entorno Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from catalog.models import Book, Author, BookAuthor, Edition, Genre, Chapter
from ebooklib import epub

def slugify_fallback(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '-', text) 
    return text.strip('-')[:100]

def clean_and_strip_images(html_soup):
    """
    Elimina todas las imágenes (etiquetas <img>) y elementos vacíos 
    para dejar exclusivamente el texto limpio y continuo del cuento.
    """
    for img in html_soup.find_all('img'):
        img.decompose()
        
    for svg in html_soup.find_all('svg'):
        svg.decompose()
        
    return str(html_soup)

def manual_extract_single_chapter(epub_path, slug):
    """
    Recorre el spine, descarta únicamente portadas y metadatos reales,
    elimina imágenes y concatena todo el relato en un único HTML continuo.
    """
    combined_soup_body = BeautifulSoup("", "html.parser")
    synopsis = ""
    extracted_title = None

    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            container = z.read('META-INF/container.xml').decode('utf-8')
            opf_path_match = re.search(r'full-path="([^"]+)"', container)
            if not opf_path_match:
                print(f"    ⚠️ No se encontró el archivo OPF en container.xml para {slug}")
                return None, synopsis, None
                
            opf_path = opf_path_match.group(1)
            opf_content = z.read(opf_path).decode('utf-8', errors='ignore')
            base_dir = os.path.dirname(opf_path)
            
            manifest = {}
            for item_match in re.finditer(r'<item\s+([^>]+)>', opf_content, re.IGNORECASE):
                attrs = item_match.group(1)
                id_match = re.search(r'id="([^"]+)"', attrs)
                href_match = re.search(r'href="([^"]+)"', attrs)
                if id_match and href_match:
                    manifest[id_match.group(1)] = unquote(href_match.group(1))

            spine_ids = [re.search(r'idref="([^"]+)"', line).group(1) 
                         for line in opf_content.split('<itemref ') if 'idref="' in line]
            
            print(f"    [Spine analizado: {len(spine_ids)} ítems]")
            
            for item_id in spine_ids:
                if item_id in manifest:
                    rel_path = manifest[item_id]
                    file_path = os.path.join(base_dir, rel_path).replace("\\", "/")
                    file_name_lower = file_path.lower()
                    
                    # 🚫 FILTRAR SOLO PORTADAS TÉCNICAS E ÍNDICES/HITOS EXPLÍCITOS
                    if any(x in file_name_lower for x in ['cover', 'titlepage', 'hitos', 'toc', 'nav', 'indice', 'portada']):
                        # Excepción: si el archivo de título contiene parte del cuento o intro larga, evaluarlo
                        if not any(story_w in file_name_lower for story_w in ['barba', 'caperucita', 'blancanieves', 'ardilla', 'perico', 'gigante', 'patito', 'ruisenor', 'soldadito', 'emperador', 'gato', 'hansel', 'durmiente', 'cenicienta', 'guisante', 'sirenita', 'cisnes', 'mowgli', 'cerditos', 'zapatos', 'pulgarcito', 'rapunzel', 'perez', 'ricitos', 'rumpelstiltskin']):
                            print(f"    - Omitido por sección no narrativa: {file_path}")
                            continue
                        
                    try:
                        raw_html = z.read(file_path).decode('utf-8', errors='ignore')
                        soup = BeautifulSoup(raw_html, 'html.parser')
                        text_content = soup.get_text().strip()
                        
                        # 🚫 Omitir avisos comerciales muy cortos o páginas de créditos aisladas (menos de 40 caracteres)
                        if len(text_content) < 40 and ('elejandria' in text_content.lower() or 'descarga' in text_content.lower()):
                            print(f"    - Omitido aviso comercial corto en: {file_path}")
                            continue
                            
                        # Omitir páginas vacías
                        if len(text_content) < 15:
                            print(f"    - Omitido por contenido vacío ({len(text_content)} chars): {file_path}")
                            continue

                        # Limpiar imágenes y estructurar contenido de texto puro
                        cleaned_html = clean_and_strip_images(soup)
                        body_content = BeautifulSoup(cleaned_html, 'html.parser')
                        
                        # Capturar título limpio si existe
                        if not extracted_title:
                            t_tag = body_content.find(['h1', 'h2', 'h3'])
                            if t_tag and t_tag.text.strip():
                                candidate_title = t_tag.text.strip()
                                if len(candidate_title) < 80 and not any(w in candidate_title.lower() for w in ['elejandria', 'capítulo', 'www']):
                                    extracted_title = candidate_title

                        # CONCATENAR TODO EN EL BLOQUE ÚNICO CONTINUO
                        for element in body_content.contents:
                            combined_soup_body.append(element)
                            
                        if not synopsis and len(text_content) > 200:
                            synopsis = text_content[:400] + "..."
                            
                        print(f"    + Texto útil incorporado: {file_path} ({len(text_content)} chars)")
                        
                    except Exception as ex:
                        print(f"    ⚠️ Error leyendo archivo interno {file_path}: {ex}")
                        continue
                        
    except Exception as e:
        print(f"Error en extracción manual para {slug}: {e}")
        
    return str(combined_soup_body), synopsis, extracted_title

def get_metadata_from_opf(epub_path):
    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            container = z.read('META-INF/container.xml').decode('utf-8')
            opf_path_match = re.search(r'full-path="([^"]+)"', container)
            if not opf_path_match:
                return None, None
            opf_path = opf_path_match.group(1)
            opf_content = z.read(opf_path).decode('utf-8', errors='ignore')
            
            title_match = re.search(r'<dc:title[^>]*>(.*?)</dc:title>', opf_content, re.DOTALL | re.IGNORECASE)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else None
            
            creator_match = re.search(r'<dc:creator[^>]*>(.*?)</dc:creator>', opf_content, re.DOTALL | re.IGNORECASE)
            creator = re.sub(r'<[^>]+>', '', creator_match.group(1)).strip() if creator_match else None
            
            return title, creator
    except Exception:
        return None, None

def main():
    root_dir = Path(settings.BASE_DIR) / "media" / "books" / "literatus-games"
    if not root_dir.exists():
        print(f"La ruta {root_dir} no existe.")
        return

    print("--- 📚 INYECCIÓN EN PÁGINA ÚNICA (TEXTO PURO SIN IMÁGENES NI BASURA) ---")
    subfolders = [f for f in root_dir.iterdir() if f.is_dir()]
    
    for folder in subfolders:
        slug = folder.name
        epub_files = list(folder.glob("*.epub"))
        if not epub_files:
            continue
        
        epub_path = epub_files[0]
        print(f"\nProcesando libro: {slug}")
        
        book_title, author_name = get_metadata_from_opf(epub_path)
        
        # Extraer TODO el libro consolidado en un solo HTML sin imágenes
        full_content_html, extracted_synopsis, extracted_title = manual_extract_single_chapter(epub_path, slug)
        
        if not author_name:
            author_name = "Autor Desconocido"
        if not book_title:
            book_title = slug.replace("-", " ").title()
            
        final_title = extracted_title if extracted_title else book_title
            
        if not full_content_html or len(full_content_html.strip()) < 50:
            print(f"  ⚠️ No se encontró contenido narrativo válido para {slug}")
            continue
            
        author_obj, _ = Author.objects.get_or_create(
            slug=slugify_fallback(author_name), 
            defaults={'full_name': author_name[:100]}
        )
        
        book_obj, _ = Book.objects.get_or_create(
            slug=slug[:100], 
            defaults={
                'title': book_title[:100], 
                'synopsis': extracted_synopsis,
                'status': 'published', 
                'is_published': True
            }
        )

        cover_path = folder / "cover.jpg"
        if cover_path.exists() and not book_obj.cover_image:
            with open(cover_path, 'rb') as cf:
                book_obj.cover_image.save(f"{slug}_cover.jpg", File(cf), save=True)
            print(f"  🖼️ Portada asignada para {book_title}")
        
        BookAuthor.objects.get_or_create(book=book_obj, author=author_obj)
        Edition.objects.get_or_create(
            book=book_obj, 
            format='epub', 
            defaults={'file': f"books/{slug}/{epub_path.name}", 'price': Decimal('0.00')}
        )
        
        # 🛠️ CREAR UN ÚNICO CAPÍTULO CONTINUO SIN IMÁGENES
        book_obj.chapters.all().delete()
        Chapter.objects.create(
            book=book_obj, 
            title=final_title[:200], 
            content_html=full_content_html, 
            order=1
        )
        print(f"  ✅ '{book_title}' importado con éxito: Todo el texto continuo en 1 solo capítulo.")

    print("\n✅ Proceso completado exitosamente.")

if __name__ == "__main__":
    main()