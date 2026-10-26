import os
import sys
from pathlib import Path
import django
import zipfile
import re
import shutil
from decimal import Decimal
from bs4 import BeautifulSoup
from django.core.files import File

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

def clean_content(html_soup, book_slug):
    for img in html_soup.find_all('img'):
        src = img.get('src', '')
        if 'elejandria' in src.lower() or 'logo' in src.lower():
            img.decompose()
            continue
        filename = os.path.basename(src)
        img['src'] = f"/media/books/{book_slug}/images/{filename}"
        img['style'] = "max-width: 100%; height: auto; display: block; margin: 1em auto; border-radius: 8px;"
    return str(html_soup)

def extract_images(epub_path, dest_folder):
    img_folder = Path(dest_folder) / "images"
    img_folder.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            for f in z.infolist():
                if f.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    dest = img_folder / os.path.basename(f.filename)
                    with z.open(f) as s, open(dest, "wb") as t:
                        shutil.copyfileobj(s, t)
    except Exception:
        pass

def manual_extract_chapters(epub_path, slug):
    chapters = []
    synopsis = ""
    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            container = z.read('META-INF/container.xml').decode('utf-8')
            opf_path = re.search(r'full-path="([^"]+)"', container).group(1)
            opf_content = z.read(opf_path).decode('utf-8', errors='ignore')
            base_dir = os.path.dirname(opf_path)
            manifest = {re.search(r'id="([^"]+)"', line).group(1): re.search(r'href="([^"]+)"', line).group(1) 
                        for line in opf_content.split('<item ') if 'id="' in line and 'href="' in line}
            spine_ids = [re.search(r'idref="([^"]+)"', line).group(1) 
                         for line in opf_content.split('<itemref ') if 'idref="' in line]
            order = 1
            for item_id in spine_ids:
                if item_id in manifest:
                    file_path = os.path.join(base_dir, manifest[item_id]).replace("\\", "/")
                    try:
                        raw_html = z.read(file_path).decode('utf-8', errors='ignore')
                        soup = BeautifulSoup(raw_html, 'html.parser')
                        text_content = soup.get_text().strip()
                        if len(text_content) > 50:
                            title_tag = soup.find(['h1', 'h2', 'h3'])
                            title = title_tag.text.strip()[:100] if title_tag else f"Capítulo {order}"
                            
                            # Capturar el primer texto denso como sinopsis provisional si está vacía
                            if not synopsis and len(text_content) > 200:
                                synopsis = text_content[:400] + "..."

                            chapters.append({
                                'title': title,
                                'content': clean_content(soup, slug),
                                'order': order
                            })
                            order += 1
                    except Exception:
                        continue
    except Exception as e:
        print(f"Error en extracción manual para {slug}: {e}")
    return chapters, synopsis

def get_metadata_from_opf(epub_path):
    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            container = z.read('META-INF/container.xml').decode('utf-8')
            opf_path = re.search(r'full-path="([^"]+)"', container).group(1)
            opf_content = z.read(opf_path).decode('utf-8', errors='ignore')
            
            title_match = re.search(r'<dc:title[^>]*>(.*?)</dc:title>', opf_content, re.DOTALL | re.IGNORECASE)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else None
            
            creator_match = re.search(r'<dc:creator[^>]*>(.*?)</dc:creator>', opf_content, re.DOTALL | re.IGNORECASE)
            creator = re.sub(r'<[^>]+>', '', creator_match.group(1)).strip() if creator_match else None
            
            return title, creator
    except Exception:
        return None, None

def main():
    root_dir = Path("media/books")
    if not root_dir.exists():
        print(f"La ruta {root_dir} no existe.")
        return

    print("--- 📚 INYECCIÓN COMPLETA (CON PORTADAS Y SINOPSIS) ---")
    subfolders = [f for f in root_dir.iterdir() if f.is_dir()]
    
    for folder in subfolders:
        slug = folder.name
        epub_files = list(folder.glob("*.epub"))
        if not epub_files:
            continue
        
        epub_path = epub_files[0]
        print(f"Procesando libro: {slug}")
        
        extract_images(epub_path, folder)
        book_title, author_name = get_metadata_from_opf(epub_path)
        chapters_data, extracted_synopsis = manual_extract_chapters(epub_path, slug)
        
        if not author_name:
            author_name = "Autor Desconocido"
        if not book_title:
            book_title = slug.replace("-", " ").title()
            
        if not chapters_data:
            print(f"  ⚠️ No se encontraron capítulos para {slug}")
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

        # Buscar y asignar el archivo cover.jpg si existe en la carpeta del libro
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
        
        book_obj.chapters.all().delete()
        for chap in chapters_data:
            Chapter.objects.create(
                book=book_obj, 
                title=chap['title'], 
                content_html=chap['content'], 
                order=chap['order']
            )
        print(f"  ✅ {book_title} importado con éxito ({len(chapters_data)} capítulos).")

    print("\n✅ Proceso de inyección de portadas y contenido finalizado.")

if __name__ == "__main__":
    main()