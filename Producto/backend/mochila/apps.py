from django.apps import AppConfig


class MochilaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mochila'

    def ready(self):
        import mochila.signals  # Importa las señales para que se registren al iniciar Django