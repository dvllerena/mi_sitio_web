from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group

@receiver(post_migrate)
def crear_grupos_iniciales(sender, **kwargs):
    Group.objects.get_or_create(name='Admin')
    Group.objects.get_or_create(name='Tecnico')
    Group.objects.get_or_create(name='Visitante')