"""Vistas para la API de mochila, puntos, minijuegos y finales alternativos."""

from collections import OrderedDict

from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

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
from .serializers import (
    AlternateEndingContentSerializer,
    BackpackItemSerializer,
    BackpackSummarySerializer,
    BookContextSerializer,
    BookEventQuerySerializer,
    BookEventResponseSerializer,
    ItemSerializer,
    MinigameAttemptSerializer,
    MinigameHistoryFilterSerializer,
    PointTransactionSerializer,
    RecordMinigameAttemptSerializer,
)


class MinigameHistoryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BaseBackpackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_backpack(self, user):
        """Crea la mochila si todavía no existe."""
        backpack, _ = Backpack.objects.get_or_create(user=user)
        return backpack

    def get_locked_backpack(self, user):
        """Debe invocarse dentro de transaction.atomic()."""
        backpack, _ = Backpack.objects.get_or_create(user=user)
        return Backpack.objects.select_for_update().get(pk=backpack.pk)


# -----------------------------------------------------------------------------
# Mochila y estadísticas
# -----------------------------------------------------------------------------

class BackpackDetailView(BaseBackpackView):
    """GET /api/mochila/ — saldo, puntos acumulados, objetos y estadísticas."""

    def get(self, request):
        backpack = self.get_backpack(request.user)

        user_items = (
            BackpackItem.objects.filter(backpack=backpack)
            .select_related('item', 'item__book', 'item__alternate_story')
            .order_by('-created_at')
        )
        items_data = BackpackItemSerializer(
            user_items, many=True, context={'request': request}
        ).data

        attempts = MinigameAttempt.objects.filter(backpack=backpack)
        stats = attempts.aggregate(
            total_played=Count('id'),
            won_count=Count('id', filter=Q(result=MinigameAttempt.ResultChoices.WON)),
            lost_count=Count('id', filter=Q(result=MinigameAttempt.ResultChoices.LOST)),
            points_earned_in_games=Coalesce(Sum('points_earned'), 0),
        )

        by_minigame = (
            attempts.values('minigame_id', 'minigame__code', 'minigame__name')
            .annotate(
                played=Count('id'),
                won=Count('id', filter=Q(result=MinigameAttempt.ResultChoices.WON)),
                lost=Count('id', filter=Q(result=MinigameAttempt.ResultChoices.LOST)),
                total_points=Coalesce(Sum('points_earned'), 0),
            )
            .order_by('minigame__name')
        )

        # 🌟 NUEVO: Obtener el catálogo global de todos los objetos activos del sistema
        all_catalog_items = Item.objects.filter(is_active=True).select_related('book', 'alternate_story')
        all_items_data = ItemSerializer(
            all_catalog_items, many=True, context={'request': request}
        ).data

        return Response({
            'backpack': BackpackSummarySerializer(backpack).data,
            'points_balance': backpack.points_balance,
            'total_points_earned': backpack.total_points_earned,
            'items': items_data,
            'all_items': all_items_data,  # 👈 Se incluye esta clave para Angular
            'stats': stats,
            'history_by_minigame': list(by_minigame),
        })


class MinigameHistoryListView(BaseBackpackView):
    """
    GET /api/mochila/history/
    Filtros opcionales: result=won|lost, minigame=<UUID>, book=<UUID>.
    Paginación: page y page_size (20 por página, máximo 100).
    """

    pagination_class = MinigameHistoryPagination

    def get(self, request):
        filter_serializer = MinigameHistoryFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        filters = filter_serializer.validated_data

        backpack = self.get_backpack(request.user)
        queryset = MinigameAttempt.objects.filter(backpack=backpack).select_related(
            'minigame', 'book'
        )

        if filters.get('result'):
            queryset = queryset.filter(result=filters['result'])
        if filters.get('minigame'):
            queryset = queryset.filter(minigame_id=filters['minigame'])
        if filters.get('book'):
            queryset = queryset.filter(book_id=filters['book'])

        queryset = queryset.order_by('-created_at', '-id')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = MinigameAttemptSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PointTransactionHistoryView(BaseBackpackView):
    """GET /api/mochila/transactions/ — movimientos de puntos auditables."""

    pagination_class = MinigameHistoryPagination

    def get(self, request):
        backpack = self.get_backpack(request.user)
        queryset = PointTransaction.objects.filter(backpack=backpack).select_related(
            'item', 'attempt__minigame'
        ).order_by('-created_at', '-id')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PointTransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# -----------------------------------------------------------------------------
# Eventos de libro y uso de objetos
# -----------------------------------------------------------------------------

class BookEventView(BaseBackpackView):
    """
    GET /api/mochila/books/{book_id}/event/?chapter_index=N

    Devuelve los eventos alternativos para los objetos que el usuario posee en
    ese libro. Los objetos se agrupan por capítulo y frase de activación.
    Si se indica chapter_index, limita los eventos a ese capítulo.
    """

    def get(self, request, book_id):
        get_object_or_404(Book, pk=book_id)
        query_serializer = BookEventQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        chapter_index = query_serializer.validated_data.get('chapter_index')

        backpack = self.get_backpack(request.user)
        stories = (
            AlternateStory.objects.filter(
                item__book_id=book_id,
                item__is_active=True,
                item__user_items__backpack=backpack,
                is_active=True,
            )
            .select_related('item')
            .distinct()
            .order_by('chapter_index', 'trigger_phrase', 'created_at', 'item_id')
        )
        if chapter_index is not None:
            stories = stories.filter(chapter_index=chapter_index)

        # Orden preservado: cada popup agrupa objetos con el mismo punto de activación.
        groups = OrderedDict()
        for story in stories:
            key = (story.chapter_index, story.trigger_phrase)
            groups.setdefault(key, []).append(story.item_id)

        if not groups:
            return Response({'has_event': False, 'events': []})

        event_data = []
        for (event_chapter, trigger_phrase), item_ids in groups.items():
            items = list(
                Item.objects.filter(
                    id__in=item_ids,
                    book_id=book_id,
                    is_active=True,
                    alternate_story__is_active=True,
                )
                .select_related('book', 'alternate_story')
                .order_by('name')
            )
            if not items:
                continue
            event_data.append({
                'chapter_index': event_chapter,
                'trigger_phrase': trigger_phrase,
                'usable_items': items,
            })

        if not event_data:
            return Response({'has_event': False, 'events': []})

        payload = {
            'has_event': True,
            'events': event_data,
            # Campos singulares para facilitar compatibilidad con clientes antiguos.
            'chapter_index': event_data[0]['chapter_index'],
            'trigger_phrase': event_data[0]['trigger_phrase'],
            'usable_items': event_data[0]['usable_items'],
        }
        data = BookEventResponseSerializer(
            payload, context={'request': request}
        ).data
        return Response(data)


class UseItemView(BaseBackpackView):
    """
    POST /api/mochila/books/{book_id}/items/{item_id}/use/

    Valida posesión y pertenencia al libro antes de devolver el final alternativo.
    Para la ruta antigua /items/{item_id}/use/, book_id debe venir en el body.
    """

    def post(self, request, item_id, book_id=None):
        if book_id is None:
            context_serializer = BookContextSerializer(data=request.data)
            context_serializer.is_valid(raise_exception=True)
            book_id = context_serializer.validated_data['book_id']
        else:
            # También valida que el UUID del libro exista.
            context_serializer = BookContextSerializer(data={'book_id': book_id})
            context_serializer.is_valid(raise_exception=True)

        backpack = self.get_backpack(request.user)

        try:
            with transaction.atomic():
                backpack_item = (
                    BackpackItem.objects.select_for_update()
                    .select_related('item', 'item__book')
                    .get(
                        backpack=backpack,
                        item_id=item_id,
                        item__is_active=True,
                    )
                )

                if str(backpack_item.item.book_id) != str(book_id):
                    return Response(
                        {'detail': 'El objeto no pertenece al libro indicado.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                alternate_story = AlternateStory.objects.filter(
                    item=backpack_item.item,
                    is_active=True,
                ).first()
                if alternate_story is None:
                    return Response(
                        {'detail': 'El objeto no tiene un final alternativo activo.'},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                now = timezone.now()
                BackpackItem.objects.filter(pk=backpack_item.pk).update(
                    times_used=F('times_used') + 1,
                    last_used_at=now,
                )
                backpack_item.refresh_from_db(fields=['times_used', 'last_used_at'])
        except BackpackItem.DoesNotExist:
            return Response(
                {'detail': 'No posees este objeto en tu mochila o no está activo.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        payload = {
            'item_id': backpack_item.item_id,
            'alternate_ending': alternate_story.alternate_ending,
            'title': alternate_story.title,
            'chapter_index': alternate_story.chapter_index,
        }
        return Response(AlternateEndingContentSerializer(payload).data)

class CheckBookUnlockedItemView(BaseBackpackView):
    """
    GET /api/mochila/books/{book_id}/unlocked-item/
    Verifica si el usuario posee al menos 1 victoria en minijuegos para este libro
    y retorna la información del ítem de tipo READING desbloqueado.
    """

    def get(self, request, book_id):
        get_object_or_404(Book, pk=book_id)
        backpack = self.get_backpack(request.user)

        has_won = MinigameAttempt.objects.filter(
            backpack=backpack,
            book_id=book_id,
            result=MinigameAttempt.ResultChoices.WON
        ).exists()

        if not has_won:
            return Response({
                'has_won': False,
                'unlocked': False,
                'item': None
            })

        # Buscar el ítem de categoría READING asociado al libro
        reading_item = Item.objects.filter(
            book_id=book_id,
            unlock_method=Item.UnlockMethod.READING,
            is_active=True
        ).select_related('book', 'alternate_story').first()

        if not reading_item:
            return Response({
                'has_won': True,
                'unlocked': False,
                'item': None
            })

        # Asegurar asignación en mochila si hubo victoria pero faltaba el registro
        bp_item, created = BackpackItem.objects.get_or_create(
            backpack=backpack,
            item=reading_item,
            defaults={'acquisition_method': BackpackItem.AcquisitionMethod.READING}
        )

        item_data = ItemSerializer(reading_item, context={'request': request}).data

        return Response({
            'has_won': True,
            'unlocked': True,
            'is_new': created,
            'item': item_data
        })


# -----------------------------------------------------------------------------
# Registro de partidas, recompensas y desbloqueo reading
# -----------------------------------------------------------------------------

class RecordMinigameResultView(BaseBackpackView):
    """
    POST /api/mochila/minigames/record/

    Acepta el resultado y score comunicados por el juego, pero NO acepta
    points_earned desde el cliente. La recompensa se calcula en el backend:
      - comics_desordenados: 10 puntos por victoria.
      - rafaga_vf: 5, 10 o 15 puntos según el score permitido.
      - otros: points_on_win/points_reward de config_data, o 10 por defecto.

    La asociación libro-minijuego se valida a través de BookMinigame. Para
    validar la mecánica completa de cada juego, en una fase posterior el cliente
    deberá enviar sus respuestas/acciones para contrastarlas con config_data.
    """

    allowed_rewards = (5, 10, 15)

    def _associated_book(self, book_minigame):
        chapter_book_id = book_minigame.chapter.book_id if book_minigame.chapter_id else None
        if book_minigame.book_id and chapter_book_id and book_minigame.book_id != chapter_book_id:
            raise ValidationError({
                'book_minigame_id':
                    'La configuración es inconsistente: el libro y el capítulo pertenecen a libros distintos.'
            })
        if chapter_book_id:
            return book_minigame.chapter.book
        if book_minigame.book_id:
            return book_minigame.book
        raise ValidationError({
            'book_minigame_id': 'La instancia del minijuego no tiene libro ni capítulo asociado.'
        })

    def _get_book_minigame(self, data):
        queryset = BookMinigame.objects.select_related(
            'minigame', 'book', 'chapter', 'chapter__book'
        )

        instance_id = data.get('book_minigame_id')
        if instance_id:
            try:
                instance = queryset.get(pk=instance_id)
            except BookMinigame.DoesNotExist:
                return None, Response(
                    {'detail': 'La instancia del minijuego no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            associated_book = self._associated_book(instance)
            if data.get('book_id') and str(data['book_id']) != str(associated_book.pk):
                raise ValidationError({'book_id': 'El libro no coincide con la instancia del minijuego.'})
            if data.get('minigame_id') and str(data['minigame_id']) != str(instance.minigame_id):
                raise ValidationError({'minigame_id': 'El minijuego no coincide con la instancia indicada.'})
            return (instance, associated_book), None

        book_id = data['book_id']
        minigame_id = data['minigame_id']
        candidates = queryset.filter(minigame_id=minigame_id).filter(
            Q(book_id=book_id) | Q(chapter__book_id=book_id)
        ).distinct()

        count = candidates.count()
        if count == 0:
            return None, Response(
                {'detail': 'El minijuego no está asociado al libro indicado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if count > 1:
            return None, Response(
                {
                    'detail': 'Hay varias instancias de este minijuego para el libro. Envía book_minigame_id.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance = candidates.get()
        associated_book = self._associated_book(instance)
        if str(associated_book.pk) != str(book_id):
            return None, Response(
                {'detail': 'El minijuego no está asociado al libro indicado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return (instance, associated_book), None

    def _calculate_reward(self, book_minigame, result, score):
        if result == MinigameAttempt.ResultChoices.LOST:
            return 0

        code = (book_minigame.minigame.code or '').strip().lower().replace('-', '_')
        config = book_minigame.config_data or {}
        if not isinstance(config, dict):
            config = {}

        if code == 'comics_desordenados':
            return 10

        if code == 'rafaga_vf':
            if score <= 0 or score % 5 != 0:
                raise ValidationError({
                    'score': 'Una victoria de rafaga_vf debe tener un score positivo en múltiplos de 5.'
                })
            # La recompensa nunca supera los 15 puntos, aunque la configuración
            # del juego contenga más de tres afirmaciones.
            return min(score, 15)

        configured_reward = config.get('points_on_win', config.get('points_reward'))
        if configured_reward is not None:
            original_reward = configured_reward
            try:
                configured_reward = int(original_reward)
                if isinstance(original_reward, float) and not original_reward.is_integer():
                    raise ValueError
            except (TypeError, ValueError):
                raise ValidationError({
                    'config_data': 'points_on_win/points_reward debe ser 5, 10 o 15.'
                })
            if configured_reward not in self.allowed_rewards:
                raise ValidationError({
                    'config_data': 'points_on_win/points_reward debe ser 5, 10 o 15.'
                })
            return configured_reward

        # Recompensa predeterminada para juegos que aún no tengan regla configurada.
        return 10

    def post(self, request):
        request_serializer = RecordMinigameAttemptSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        resolved, error_response = self._get_book_minigame(data)
        if error_response is not None:
            return error_response
        book_minigame, book = resolved
        result = data['result']
        score = data['score']
        points_earned = self._calculate_reward(book_minigame, result, score)

        item_unlocked = None
        with transaction.atomic():
            backpack = self.get_locked_backpack(request.user)

            attempt = MinigameAttempt.objects.create(
                backpack=backpack,
                book=book,
                minigame=book_minigame.minigame,
                result=result,
                score=score,
                points_earned=points_earned,
            )

            if points_earned > 0:
                Backpack.objects.filter(pk=backpack.pk).update(
                    points_balance=F('points_balance') + points_earned,
                    total_points_earned=F('total_points_earned') + points_earned,
                )
                backpack.refresh_from_db(fields=['points_balance', 'total_points_earned'])
                PointTransaction.objects.create(
                    backpack=backpack,
                    amount=points_earned,
                    reason=PointTransaction.ReasonChoices.MINIGAME,
                    attempt=attempt,
                    balance_after=backpack.points_balance,
                )

            # Se entrega el único objeto reading al existir al menos una victoria
            # histórica del usuario para este libro.
            has_won_for_book = MinigameAttempt.objects.filter(
                backpack=backpack,
                book=book,
                result=MinigameAttempt.ResultChoices.WON,
            ).exists()

            if has_won_for_book:
                reading_item = Item.objects.filter(
                    book=book,
                    unlock_method=Item.UnlockMethod.READING,
                    is_active=True,
                ).order_by('created_at', 'id').first()

                if reading_item:
                    _, created = BackpackItem.objects.get_or_create(
                        backpack=backpack,
                        item=reading_item,
                        defaults={
                            'acquisition_method': BackpackItem.AcquisitionMethod.READING,
                        },
                    )
                    if created:
                        reading_item = Item.objects.select_related(
                            'book', 'alternate_story'
                        ).get(pk=reading_item.pk)
                        item_unlocked = ItemSerializer(
                            reading_item, context={'request': request}
                        ).data

        return Response({
            'attempt_id': str(attempt.pk),
            'book_id': str(book.pk),
            'book_minigame_id': str(book_minigame.pk),
            'minigame_id': str(book_minigame.minigame_id),
            'minigame_code': book_minigame.minigame.code,
            'result': attempt.result,
            'score': attempt.score,
            'points_earned': attempt.points_earned,
            'new_balance': backpack.points_balance,
            'total_points_earned': backpack.total_points_earned,
            'item_unlocked': item_unlocked,
        }, status=status.HTTP_201_CREATED)


# -----------------------------------------------------------------------------
# Tienda
# -----------------------------------------------------------------------------

class ShopCatalogListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ItemSerializer

    def get_queryset(self):
        return (
            Item.objects.filter(
                unlock_method=Item.UnlockMethod.PURCHASE,
                is_active=True,
            )
            .select_related('book', 'alternate_story')
            .order_by('points_cost', 'name')
        )


class PurchaseItemView(BaseBackpackView):
    """Compra única de un objeto, con descuento y entrega en una transacción."""

    def post(self, request, item_id):
        with transaction.atomic():
            backpack = self.get_locked_backpack(request.user)

            try:
                item = Item.objects.select_for_update().get(
                    pk=item_id,
                    unlock_method=Item.UnlockMethod.PURCHASE,
                    is_active=True,
                )
            except Item.DoesNotExist:
                return Response(
                    {'detail': 'Objeto no disponible en la tienda.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # points_cost es nullable en el modelo; una compra necesita precio válido.
            if item.points_cost is None or item.points_cost <= 0:
                return Response(
                    {'detail': 'Este objeto de tienda no tiene un precio válido configurado.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if BackpackItem.objects.filter(backpack=backpack, item=item).exists():
                return Response(
                    {'detail': 'Ya posees este objeto en tu mochila.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if backpack.points_balance < item.points_cost:
                return Response(
                    {'detail': 'Puntos insuficientes.', 'points_balance': backpack.points_balance,
                     'points_cost': item.points_cost},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Backpack.objects.filter(pk=backpack.pk).update(
                points_balance=F('points_balance') - item.points_cost
            )
            backpack.refresh_from_db(fields=['points_balance', 'total_points_earned'])

            backpack_item = BackpackItem.objects.create(
                backpack=backpack,
                item=item,
                acquisition_method=BackpackItem.AcquisitionMethod.PURCHASE,
            )
            PointTransaction.objects.create(
                backpack=backpack,
                amount=-item.points_cost,
                reason=PointTransaction.ReasonChoices.ITEM_PURCHASE,
                item=item,
                balance_after=backpack.points_balance,
            )

        backpack_item = BackpackItem.objects.select_related(
            'item', 'item__book', 'item__alternate_story'
        ).get(pk=backpack_item.pk)
        return Response({
            'message': 'Objeto comprado exitosamente.',
            'new_balance': backpack.points_balance,
            'total_points_earned': backpack.total_points_earned,
            'item': BackpackItemSerializer(
                backpack_item, context={'request': request}
            ).data,
        }, status=status.HTTP_200_OK)
