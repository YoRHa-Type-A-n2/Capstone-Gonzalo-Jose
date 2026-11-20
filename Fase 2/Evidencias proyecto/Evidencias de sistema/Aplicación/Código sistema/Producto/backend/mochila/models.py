"""
mochila/models.py — Modelos del sistema de mochila, minijuegos y finales alternos.
"""

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Item(TimeStampedModel):
    """
    Catálogo de objetos asociados a un cuento.
    - reading: se otorga al ganar un minijuego del libro por primera vez.
    - purchase: se compra con puntos.
    """
    class UnlockMethod(models.TextChoices):
        READING = 'reading', 'Lectura y minijuego'
        PURCHASE = 'purchase', 'Compra'

    book = models.ForeignKey('catalog.Book', on_delete=models.PROTECT, related_name='backpack_items')
    name = models.CharField(max_length=255)  # Nombre visible del objeto
    description = models.TextField(blank=True, default='')  # Pista o descripción sin spoilers
    icon = models.ImageField(upload_to='backpack/items/', null=True, blank=True)  # Imagen para la mochila y popup
    unlock_method = models.CharField(
        max_length=20,
        choices=UnlockMethod.choices,
        default=UnlockMethod.READING,
    )
    points_cost = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Precio en puntos. Solo aplica a objetos de compra.",
    )
    is_active = models.BooleanField(default=True)  # Ocultar objeto sin borrarlo

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'

    def __str__(self):
        return f"{self.name} ({self.book.title})"


class AlternateStory(TimeStampedModel):
    """
    Historia alterna que reemplaza el final del libro cuando se activa un objeto válido.
    """
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name='alternate_story')
    title = models.CharField(max_length=255)  # Nombre del final alterno
    chapter_index = models.PositiveSmallIntegerField(default=1)  # Capítulo donde ocurre el evento (desde 1)
    trigger_phrase = models.TextField()  # Frase exacta donde se dispara el evento
    alternate_ending = models.TextField()  # Texto HTML que reemplaza el contenido posterior
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Alternate Story'
        verbose_name_plural = 'Alternate Stories'

    def __str__(self):
        return f"Final alterno: {self.title} (Item: {self.item.name})"


class Backpack(TimeStampedModel):
    """
    Mochila del usuario. Almacena el saldo actual de puntos y el histórico ganado.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='backpack')
    points_balance = models.PositiveIntegerField(default=0)  # Puntos gastables actuales
    total_points_earned = models.PositiveIntegerField(default=0)  # Histórico acumulado (nunca baja)

    class Meta:
        verbose_name = 'Backpack'
        verbose_name_plural = 'Backpacks'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(points_balance__gte=0),
                name='points_balance_gte_0',
                violation_error_message="El saldo de puntos no puede ser negativo.",
            )
        ]

    def __str__(self):
        return f"Mochila de {self.user.username} (Puntos: {self.points_balance})"


class BackpackItem(TimeStampedModel):
    """
    Objetos que posee el usuario en su mochila (permanentes y reutilizables).
    La fecha de obtención es created_at.
    """
    class AcquisitionMethod(models.TextChoices):
        READING = 'reading', 'Lectura y minijuego'
        PURCHASE = 'purchase', 'Compra'
        ADMIN = 'admin', 'Administrador'

    backpack = models.ForeignKey(Backpack, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='user_items')
    acquisition_method = models.CharField(max_length=20, choices=AcquisitionMethod.choices)
    times_used = models.PositiveIntegerField(default=0)  # Veces que se usó el objeto
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Backpack Item'
        verbose_name_plural = 'Backpack Items'
        constraints = [
            models.UniqueConstraint(
                fields=['backpack', 'item'],
                name='unique_backpack_item',
                violation_error_message="El usuario ya posee este objeto en su mochila.",
            )
        ]

    def __str__(self):
        return f"{self.backpack.user.username} tiene {self.item.name}"


class MinigameAttempt(TimeStampedModel):
    """
    Historial de partidas jugadas de minijuegos por el usuario.
    El tipo de minijuego sale de la FK a games.Minigame.
    """
    class ResultChoices(models.TextChoices):
        WON = 'won', 'Ganado'
        LOST = 'lost', 'Perdido'

    backpack = models.ForeignKey(Backpack, on_delete=models.CASCADE, related_name='minigame_attempts')
    book = models.ForeignKey('catalog.Book', on_delete=models.PROTECT, related_name='minigame_attempts')
    minigame = models.ForeignKey('games.Minigame', on_delete=models.PROTECT, related_name='attempts')
    result = models.CharField(max_length=10, choices=ResultChoices.choices)
    score = models.IntegerField(default=0)
    points_earned = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Minigame Attempt'
        verbose_name_plural = 'Minigame Attempts'
        indexes = [
            models.Index(fields=['backpack', 'minigame']),
            models.Index(fields=['backpack', 'book', 'result']),
            models.Index(fields=['backpack', 'created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(result='won') | models.Q(points_earned=0),
                name='lost_attempt_earns_no_points',
                violation_error_message="Una partida perdida no puede otorgar puntos.",
            ),
        ]

    def __str__(self):
        return f"Intento {self.minigame} - {self.backpack.user.username} ({self.result})"


class PointTransaction(TimeStampedModel):
    """
    Libro de movimientos contables para auditar cada ganancia o gasto de puntos.
    """
    class ReasonChoices(models.TextChoices):
        MINIGAME = 'minigame', 'Minijuego'
        ITEM_PURCHASE = 'item_purchase', 'Compra de objeto'
        ADMIN_ADJUSTMENT = 'admin_adjustment', 'Ajuste de administrador'

    backpack = models.ForeignKey(Backpack, on_delete=models.CASCADE, related_name='point_transactions')
    amount = models.IntegerField()  # Positivo si gana, negativo si gasta
    reason = models.CharField(max_length=30, choices=ReasonChoices.choices)
    attempt = models.ForeignKey(
        MinigameAttempt, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='transactions',
    )
    item = models.ForeignKey(
        Item, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='transactions',
    )
    balance_after = models.PositiveIntegerField()  # Saldo resultante tras el movimiento

    class Meta:
        verbose_name = 'Point Transaction'
        verbose_name_plural = 'Point Transactions'
        indexes = [
            models.Index(fields=['backpack', 'created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(amount=0),
                name='point_transaction_amount_not_zero',
                violation_error_message="Un movimiento de puntos no puede ser 0.",
            ),
            # Una partida solo puede otorgar puntos una vez (los NULL no cuentan como duplicados).
            models.UniqueConstraint(
                fields=['attempt'],
                name='unique_transaction_per_attempt',
                violation_error_message="Esta partida ya otorgó sus puntos.",
            ),
        ]

    def __str__(self):
        return f"Movimiento {self.amount} para {self.backpack.user.username} ({self.reason})"