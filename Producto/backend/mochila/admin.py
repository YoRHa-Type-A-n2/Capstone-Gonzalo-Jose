"""Administración de la app mochila: aquí se carga todo el contenido (objetos y finales alternos)."""

from django import forms
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from .models import (
    AlternateStory,
    Backpack,
    BackpackItem,
    Item,
    MinigameAttempt,
    PointTransaction,
)


# -----------------------------------------------------------------------------
# Catálogo: objetos y su final alterno (se cargan juntos, en la misma pantalla)
# -----------------------------------------------------------------------------

class AlternateStoryInline(admin.StackedInline):
    """Final alterno del objeto. Un objeto activa un solo final (OneToOne)."""

    model = AlternateStory
    extra = 0
    max_num = 1
    fields = ('title', 'chapter_index', 'trigger_phrase', 'alternate_ending', 'is_active')
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 10, 'style': 'width: 95%;'})},
    }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'trigger_phrase':
            field.help_text = (
                'Copia el último párrafo del libro ANTES del cambio, tal como se lee. '
                'El evento se lanza cuando ese párrafo llega a la mitad de la pantalla.'
            )
        if db_field.name == 'alternate_ending':
            field.help_text = (
                'HTML que reemplaza todo el texto que sigue al punto de activación. '
                'Un párrafo por etiqueta <p>...</p>.'
            )
        return field


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'book', 'unlock_method', 'points_cost', 'has_alternate_story', 'is_active')
    list_filter = ('unlock_method', 'is_active', 'book')
    search_fields = ('name', 'book__title')
    list_select_related = ('book',)
    inlines = [AlternateStoryInline]

    @admin.display(boolean=True, description='Final alterno')
    def has_alternate_story(self, obj):
        try:
            return obj.alternate_story.is_active
        except ObjectDoesNotExist:
            return False


# -----------------------------------------------------------------------------
# Mochila de cada usuario (los puntos se tocan solo desde el juego, no desde aquí)
# -----------------------------------------------------------------------------

class BackpackItemInline(admin.TabularInline):
    """Sirve para regalar un objeto a un usuario (útil para probar un final alterno)."""

    model = BackpackItem
    extra = 0
    fields = ('item', 'acquisition_method', 'times_used', 'last_used_at')
    readonly_fields = ('times_used', 'last_used_at')


@admin.register(Backpack)
class BackpackAdmin(admin.ModelAdmin):
    list_display = ('user', 'points_balance', 'total_points_earned')
    search_fields = ('user__username', 'user__email')
    list_select_related = ('user',)
    # Si los puntos se editaran aquí, el saldo dejaría de coincidir con PointTransaction.
    readonly_fields = ('points_balance', 'total_points_earned')
    inlines = [BackpackItemInline]


# -----------------------------------------------------------------------------
# Historiales: solo lectura, para auditar
# -----------------------------------------------------------------------------

class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MinigameAttempt)
class MinigameAttemptAdmin(ReadOnlyAdmin):
    list_display = ('backpack', 'book', 'minigame', 'result', 'score', 'points_earned', 'created_at')
    list_filter = ('result', 'minigame', 'book')
    search_fields = ('backpack__user__username', 'book__title')
    list_select_related = ('backpack__user', 'book', 'minigame')
    date_hierarchy = 'created_at'


@admin.register(PointTransaction)
class PointTransactionAdmin(ReadOnlyAdmin):
    list_display = ('backpack', 'amount', 'reason', 'balance_after', 'created_at')
    list_filter = ('reason',)
    search_fields = ('backpack__user__username',)
    list_select_related = ('backpack__user',)
    date_hierarchy = 'created_at'