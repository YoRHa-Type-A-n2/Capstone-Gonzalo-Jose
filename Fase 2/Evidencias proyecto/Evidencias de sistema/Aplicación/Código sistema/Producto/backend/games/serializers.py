from rest_framework import serializers
from .models import Minigame, BookMinigame

class MinigameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Minigame
        fields = ['id', 'code', 'name', 'description']

class BookMinigameSerializer(serializers.ModelSerializer):
    minigame_code = serializers.CharField(source='minigame.code', read_only=True)
    minigame_name = serializers.CharField(source='minigame.name', read_only=True)

    class Meta:
        model = BookMinigame
        fields = [
            'id', 
            'book', 
            'minigame', 
            'minigame_code', 
            'minigame_name', 
            'title', 
            'config_data', 
            'created_at'
        ]