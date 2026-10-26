from django.urls import path
from .views import BookMinigameListView, BookMinigameByCodeView, AvailableBooksWithMinigamesView

urlpatterns = [
    path('books/', AvailableBooksWithMinigamesView.as_view(), name='available-books-minigames'),
    path('books/<uuid:book_id>/minigames/', BookMinigameListView.as_view(), name='book-minigames-list'),
    path('books/<uuid:book_id>/minigames/<str:game_code>/', BookMinigameByCodeView.as_view(), name='book-minigames-by-code'),
]