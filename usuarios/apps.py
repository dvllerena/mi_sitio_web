from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    
    def ready(self):
            # Importa las señales solo después de que las apps estén listas
            from . import signals