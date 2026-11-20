"""Serializadores de la API de mochila, puntos, minijuegos y finales alternativos."""

from rest_framework import serializers

from catalog.models import Book
from games.models import BookMinigame

from .models import (
    AlternateStory,
    Backpack,
    BackpackItem,
    Item,
    MinigameAttempt,
    PointTransaction,
)


class AlternateStorySummarySerializer(serializers.ModelSerializer):
    """Información del evento sin incluir el texto completo del final alternativo."""

    class Meta:
        model = AlternateStory
        fields = ['id', 'title', 'chapter_index', 'trigger_phrase']


class ItemSerializer(serializers.ModelSerializer):
    """Objeto del catálogo, con información de su libro y de su final alternativo."""

    book_title = serializers.CharField(source='book.title', read_only=True)
    alternate_story = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id',
            'book',
            'book_title',
            'name',
            'description',
            'icon',
            'unlock_method',
            'points_cost',
            'is_active',
            'alternate_story',
        ]

    def get_alternate_story(self, obj):
        try:
            story = obj.alternate_story
        except AlternateStory.DoesNotExist:
            return None
        if not story.is_active:
            return None
        return AlternateStorySummarySerializer(story, context=self.context).data


class BackpackItemSerializer(serializers.ModelSerializer):
    """Objeto que el usuario ya posee en su mochila."""

    item = ItemSerializer(read_only=True)

    class Meta:
        model = BackpackItem
        fields = [
            'id',
            'item',
            'acquisition_method',
            'times_used',
            'last_used_at',
            'created_at',
        ]


class BookEventEntrySerializer(serializers.Serializer):
    """Evento de lectura y los objetos que pueden activarlo."""

    chapter_index = serializers.IntegerField()
    trigger_phrase = serializers.CharField()
    usable_items = ItemSerializer(many=True)


class BookEventResponseSerializer(serializers.Serializer):
    """Eventos disponibles para el usuario en un libro."""

    has_event = serializers.BooleanField()
    events = BookEventEntrySerializer(many=True, required=False)
    # Campos de compatibilidad: describen el primer evento disponible.
    chapter_index = serializers.IntegerField(required=False)
    trigger_phrase = serializers.CharField(required=False)
    usable_items = ItemSerializer(many=True, required=False)


class AlternateEndingContentSerializer(serializers.Serializer):
    item_id = serializers.UUIDField()
    alternate_ending = serializers.CharField()
    title = serializers.CharField()
    chapter_index = serializers.IntegerField()


class BookEventQuerySerializer(serializers.Serializer):
    chapter_index = serializers.IntegerField(required=False, min_value=1)


class BookContextSerializer(serializers.Serializer):
    book_id = serializers.UUIDField()

    def validate_book_id(self, value):
        if not Book.objects.filter(pk=value).exists():
            raise serializers.ValidationError('El libro indicado no existe.')
        return value


class RecordMinigameAttemptSerializer(serializers.Serializer):
    """
    Datos del resultado que comunica el juego.

    La recompensa no se acepta desde el cliente: la determina la vista con la
    configuración y el código del minijuego.
    """

    book_minigame_id = serializers.UUIDField(required=False)
    book_id = serializers.UUIDField(required=False)
    minigame_id = serializers.UUIDField(required=False)
    result = serializers.ChoiceField(choices=MinigameAttempt.ResultChoices.choices)
    score = serializers.IntegerField(default=0, min_value=0)

    def validate(self, attrs):
        if 'points_earned' in self.initial_data:
            raise serializers.ValidationError({
                'points_earned': 'No envíes puntos desde el cliente; Django calcula la recompensa.'
            })

        has_instance = bool(attrs.get('book_minigame_id'))
        has_book_and_game = bool(attrs.get('book_id') and attrs.get('minigame_id'))

        if not has_instance and not has_book_and_game:
            raise serializers.ValidationError(
                'Envía book_minigame_id o, alternativamente, book_id y minigame_id.'
            )
        return attrs


class MinigameHistoryFilterSerializer(serializers.Serializer):
    result = serializers.ChoiceField(
        choices=MinigameAttempt.ResultChoices.choices,
        required=False,
    )
    minigame = serializers.UUIDField(required=False)
    book = serializers.UUIDField(required=False)


class MinigameAttemptSerializer(serializers.ModelSerializer):
    minigame_name = serializers.CharField(source='minigame.name', read_only=True)
    minigame_code = serializers.CharField(source='minigame.code', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)

    class Meta:
        model = MinigameAttempt
        fields = [
            'id',
            'book',
            'book_title',
            'minigame',
            'minigame_name',
            'minigame_code',
            'result',
            'score',
            'points_earned',
            'created_at',
        ]


class PointTransactionSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True, default=None)
    minigame_name = serializers.CharField(source='attempt.minigame.name', read_only=True, default=None)

    class Meta:
        model = PointTransaction
        fields = [
            'id',
            'amount',
            'reason',
            'item',
            'item_name',
            'attempt',
            'minigame_name',
            'balance_after',
            'created_at',
        ]
        read_only_fields = fields


class BackpackSummarySerializer(serializers.ModelSerializer):
    items_count = serializers.IntegerField(source='items.count', read_only=True)

    class Meta:
        model = Backpack
        fields = ['id', 'points_balance', 'total_points_earned', 'items_count']
