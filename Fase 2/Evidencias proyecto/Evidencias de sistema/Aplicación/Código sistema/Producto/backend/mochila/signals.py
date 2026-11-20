# mochila/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Backpack

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_backpack(sender, instance, created, **kwargs):
    """
    Crea automáticamente una mochila con 0 puntos cada vez que se registra un usuario nuevo.
    """
    if created:
        Backpack.objects.create(
            user=instance,
            points_balance=0,
            total_points_earned=0
        )