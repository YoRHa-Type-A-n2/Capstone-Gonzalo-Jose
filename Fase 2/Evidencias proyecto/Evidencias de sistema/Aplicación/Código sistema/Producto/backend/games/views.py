import random
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from catalog.models import Book
from .models import BookMinigame, Minigame
from .serializers import BookMinigameSerializer, MinigameSerializer

class AvailableBooksWithMinigamesView(APIView):
    """
    Devuelve la lista de libros que tienen minijuegos asociados en la base de datos.
    Estructura JSON por libro:
    - id
    - title
    - author_name
    - cover_image
    - synopsis
    """
    def get(self, request):
        # Filtrar exclusivamente los libros con minijuegos registrados en BookMinigame
        direct_book_ids = BookMinigame.objects.filter(book__isnull=False).values_list('book_id', flat=True)
        chapter_book_ids = BookMinigame.objects.filter(chapter__isnull=False).values_list('chapter__book_id', flat=True)
        valid_book_ids = set(direct_book_ids).union(set(chapter_book_ids))

        books = Book.objects.filter(
            id__in=valid_book_ids
        ).prefetch_related('book_authors__author').distinct().order_by('title')

        data = []
        for book in books:
            book_authors = list(book.book_authors.all())
            author_name = "Autor Desconocido"
            if book_authors:
                main_author = next((ba for ba in book_authors if ba.role in ['primary', 'author']), None) or book_authors[0]
                author_name = main_author.author.full_name

            cover_image_url = None
            if book.cover_image:
                try:
                    cover_image_url = request.build_absolute_uri(book.cover_image.url)
                except Exception as err:
                    print(f"Error building absolute URI for cover image: {err}")
                    cover_image_url = book.cover_image.url

            data.append({
                'id': str(book.id),
                'title': book.title,
                'author_name': author_name,
                'cover_image': cover_image_url,
                'synopsis': book.synopsis or ''
            })

        return Response(data, status=status.HTTP_200_OK)


class BookMinigameListView(generics.ListAPIView):
    serializer_class = BookMinigameSerializer

    def get_queryset(self):
        book_id = self.kwargs.get('book_id')
        return BookMinigame.objects.filter(book_id=book_id).select_related('minigame')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # 1. Agrupar los minijuegos por su código de categoría (ej. 'busca_imagen', 'rafaga_vf', etc.)
        games_by_code = {}
        for item in queryset:
            code = item.minigame.code
            if code not in games_by_code:
                games_by_code[code] = []
            games_by_code[code].append(item)
            
        # 2. De cada grupo, seleccionar aleatoriamente UN SOLO elemento
        unique_section_games = []
        for code, items in games_by_code.items():
            if items:
                unique_section_games.append(random.choice(items))
                
        # 3. Si el frontend solicita aleatoriedad y un límite (ej. ?random=true&limit=5)
        if self.request.query_params.get('random', 'false').lower() == 'true':
            limit = int(self.request.query_params.get('limit', 5))
            if len(unique_section_games) > limit:
                unique_section_games = random.sample(unique_section_games, limit)
            else:
                random.shuffle(unique_section_games)
                
        serializer = self.get_serializer(unique_section_games, many=True)
        return Response(serializer.data)


class BookMinigameByCodeView(APIView):
    def get(self, request, book_id, game_code):
        games = BookMinigame.objects.filter(book_id=book_id, minigame__code=game_code)
        serializer = BookMinigameSerializer(games, many=True)
        return Response(serializer.data)
    
    
class BookMinigameDevBuscaImagenView(APIView):
    """
    Endpoint exclusivo para desarrolladores que recupera TODOS los registros 
    de 'busca_imagen' de un libro sin selección aleatoria, permitiendo 
    recorrerlos 1 por 1 para configurar coordenadas.
    """
    def get(self, request, book_id):
        games = BookMinigame.objects.filter(
            book_id=book_id, 
            minigame__code='busca_imagen'
        ).select_related('minigame')
        
        serializer = BookMinigameSerializer(games, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)