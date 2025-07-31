from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save

class Usuario(AbstractUser):
    ROLES = (
        ('ADMIN', 'Administrador'),
        ('TECNICO', 'Técnico'),
        ('VISITANTE', 'Visitante'),
    )
    
    rol = models.CharField(max_length=10, choices=ROLES, default='VISITANTE')
    telefono = models.CharField(max_length=20, blank=True)
    
    # Solución para conflictos de related_name
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name="usuarios_usuario_set",
        related_query_name="usuario",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name="usuarios_usuario_set",
        related_query_name="usuario",
    )

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_role_display(self):
        return dict(self.ROLES).get(self.rol, self.rol)

class Perfil(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)