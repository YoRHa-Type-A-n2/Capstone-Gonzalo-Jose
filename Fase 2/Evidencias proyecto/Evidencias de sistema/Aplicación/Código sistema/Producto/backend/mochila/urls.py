"""Rutas para la API de mochila."""

from django.urls import path

from .views import (
    BackpackDetailView,
    BookEventView,
    MinigameHistoryListView,
    PointTransactionHistoryView,
    PurchaseItemView,
    RecordMinigameResultView,
    ShopCatalogListView,
    UseItemView,
    CheckBookUnlockedItemView,
)

app_name = 'mochila'

urlpatterns = [
    # Mochila, estadísticas e historiales
    path('', BackpackDetailView.as_view(), name='backpack-detail'),
    path('history/', MinigameHistoryListView.as_view(), name='minigame-history'),
    path('transactions/', PointTransactionHistoryView.as_view(), name='point-transactions'),

    # Eventos y finales alternativos vinculados al libro
    path('books/<uuid:book_id>/event/', BookEventView.as_view(), name='book-event'),
    path(
        'books/<uuid:book_id>/unlocked-item/',
        CheckBookUnlockedItemView.as_view(),
        name='check-book-unlocked-item',
    ),
    path(
        'books/<uuid:book_id>/items/<uuid:item_id>/use/',
        UseItemView.as_view(),
        name='use-book-item',
    ),
    # Compatibilidad temporal: esta ruta antigua exige book_id en el body.
    path('items/<uuid:item_id>/use/', UseItemView.as_view(), name='use-item'),

    # Registro de partidas y recompensas calculadas por Django
    path('minigames/record/', RecordMinigameResultView.as_view(), name='record-minigame'),

    # Tienda
    path('shop/', ShopCatalogListView.as_view(), name='shop-catalog'),
    path('shop/<uuid:item_id>/purchase/', PurchaseItemView.as_view(), name='purchase-item'),
]
