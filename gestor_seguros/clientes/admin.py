# clientes/admin.py
from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'numero_documento', 'email', 'telefono_principal', 'fecha_actualizacion')
    search_fields = ('nombre_completo', 'numero_documento', 'email')
    list_filter = ('tipo_documento', 'ciudad', 'fecha_creacion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        (None, {
            'fields': ('nombre_completo', ('tipo_documento', 'numero_documento'), 'fecha_nacimiento')
        }),
        ('Información de Contacto', {
            'fields': ('email', 'telefono_principal', 'telefono_secundario', 'direccion', 'ciudad')
        }),
        ('Información Adicional', {
            'fields': ('profesion_ocupacion', 'notas_adicionales')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',), # Ocultar por defecto
        }),
    )