# clientes/models.py
from django.db import models
from django.urls import reverse
from django.conf import settings

class Cliente(models.Model):

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clientes')


    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('NIT', 'NIT'),
        ('PAS', 'Pasaporte'),
        ('OTRO', 'Otro'),
    ]

    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre Completo")
    tipo_documento = models.CharField(max_length=5, choices=TIPO_DOCUMENTO_CHOICES, default='CC', verbose_name="Tipo de Documento")
    numero_documento = models.CharField(max_length=50, unique=True, verbose_name="Número de Documento")
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de Nacimiento")
    email = models.EmailField(max_length=254, unique=True, null=True, blank=True, verbose_name="Correo Electrónico")
    telefono_principal = models.CharField(max_length=20, verbose_name="Teléfono Principal")
    telefono_secundario = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono Secundario")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")
    ciudad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ciudad")
    profesion_ocupacion = models.CharField(max_length=150, blank=True, null=True, verbose_name="Profesión/Ocupación")
    notas_adicionales = models.TextField(blank=True, null=True, verbose_name="Notas Adicionales")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre_completo} ({self.numero_documento})"

    def get_absolute_url(self):
        return reverse('clientes:detalle_cliente', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre_completo']
        unique_together = ('usuario', 'numero_documento')