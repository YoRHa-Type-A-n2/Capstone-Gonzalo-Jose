from django.db import models
from core.models import TimeStampedModel
from catalog.models import Book, Chapter

class Minigame(TimeStampedModel):
    """
    Catálogo maestro de los minijuegos desarrollados en el frontend.
    Ejemplos de 'code': 'cazador_intrusos', 'ahorcado', 'pareo', 'trivia', etc.
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.name} ({self.code})"


class BookMinigame(TimeStampedModel):
    """
    Vincula un minijuego a un libro completo o a un capítulo específico.
    Usa config_data (JSON) para pasar la información que requiere el frontend.
    """
    minigame = models.ForeignKey(Minigame, on_delete=models.CASCADE, related_name='book_instances')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='minigames', null=True, blank=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='minigames', null=True, blank=True)
    
    title = models.CharField(max_length=255, help_text="Título visible del desafío")
    config_data = models.JSONField(
        default=dict, 
        help_text="Parámetros en JSON requeridos por el frontend para renderizar la mecánica."
    )

    def __str__(self):
        target = self.chapter or self.book
        return f"[{self.minigame.code}] {self.title} → {target}"