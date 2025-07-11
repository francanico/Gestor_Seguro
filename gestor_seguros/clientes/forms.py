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
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notas_adicionales': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            # Añadir 'class': 'form-control' a otros campos si usas Bootstrap
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