# clientes/forms.py
from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre_completo', 'tipo_documento', 'numero_documento', 'fecha_nacimiento',
            'email', 'telefono_principal', 'telefono_secundario', 'direccion',
            'ciudad', 'profesion_ocupacion', 'notas_adicionales'
        ]
        widgets = {
            # Calendario para la fecha de nacimiento
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            
            # Placeholders para guiar al usuario
            'nombre_completo': forms.TextInput(attrs={'placeholder': 'Nombre y Apellido'}),
            'numero_documento': forms.TextInput(attrs={'placeholder': 'Ej: V-12345678 o J-123456789-0'}),
            'email': forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}),
            'telefono_principal': forms.TextInput(attrs={'placeholder': 'Ej: 0414-1234567'}),
            'telefono_secundario': forms.TextInput(attrs={'placeholder': 'Opcional'}),
            'ciudad': forms.TextInput(attrs={'placeholder': 'Ej: Caracas'}),
            'profesion_ocupacion': forms.TextInput(attrs={'placeholder': 'Ej: Ingeniero, Comerciante'}),
            
            # Áreas de texto con tamaño definido
            'direccion': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Dirección de domicilio u oficina'}),
            'notas_adicionales': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Cualquier información relevante sobre el cliente...'}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 3