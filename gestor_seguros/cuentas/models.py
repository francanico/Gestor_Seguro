from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class PerfilUsuario(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    nombre_agencia = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nombre de la Agencia")
    rif = models.CharField(max_length=50, blank=True, null=True, verbose_name="RIF/Identificación Fiscal")
    telefono_profesional = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono Profesional")
    direccion_agencia = models.TextField(blank=True, null=True, verbose_name="Dirección de la Agencia")
    biografia = models.TextField(blank=True, null=True, verbose_name="Breve Biografía/Descripción")
    
    def __clstr__(self):
        return f"Perfil de {self.user.username}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if not hasattr(instance, 'perfil'):
        PerfilUsuario.objects.create(user=instance)
    instance.perfil.save()
