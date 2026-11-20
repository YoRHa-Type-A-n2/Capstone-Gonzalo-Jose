from django.urls import path
from .views import BookMinigameListView, BookMinigameByCodeView, AvailableBooksWithMinigamesView, BookMinigameDevBuscaImagenView

urlpatterns = [
    path('books/', AvailableBooksWithMinigamesView.as_view(), name='available-books-minigames'),
    path('books/<uuid:book_id>/minigames/', BookMinigameListView.as_view(), name='book-minigames-list'),
    path('books/<uuid:book_id>/minigames/<str:game_code>/', BookMinigameByCodeView.as_view(), name='book-minigames-by-code'),
    path('books/<uuid:book_id>/minigames/dev-busca-imagen/', BookMinigameDevBuscaImagenView.as_view(), name='dev-busca-imagen-list'),
]
