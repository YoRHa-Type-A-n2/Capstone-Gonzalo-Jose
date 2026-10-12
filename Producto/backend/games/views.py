import random
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import BookMinigame, Minigame
from .serializers import BookMinigameSerializer, MinigameSerializer

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