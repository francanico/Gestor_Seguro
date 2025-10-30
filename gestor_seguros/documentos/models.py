from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

def user_directory_path(instance, filename):
    # El archivo se subirá a MEDIA_ROOT/documentos/<user_id>/<filename>
    return f'documentos/{instance.usuario.id}/{filename}'

class Documento(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documentos')
    titulo = models.CharField(max_length=200, verbose_name="Título o Descripción")
    archivo = models.FileField(upload_to=user_directory_path, verbose_name="Archivo")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    # Campos para la relación genérica
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-fecha_subida']
