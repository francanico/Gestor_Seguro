# polizas/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Poliza, Aseguradora, Cliente,PagoCuota,Siniestro,Asegurado
from django.core.exceptions import ValidationError 
from clientes.models import Cliente


class AseguradoraForm(forms.ModelForm):
    class Meta:
        model = Aseguradora
        fields = ['nombre', 'rif', 'contacto_nombre', 'contacto_email', 'contacto_telefono']
        widgets = {
            # Puedes añadir widgets específicos si es necesario
            # 'contacto_nombre': forms.TextInput(attrs={'placeholder': 'Ej: Juan Pérez'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

class AseguradoForm(forms.ModelForm):
    class Meta:
        model = Asegurado
        fields = ['nombre_completo', 'cedula', 'fecha_nacimiento', 'parentesco', 'sexo', 'email', 'telefono', 'notas']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'notas': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        # Este __init__ es simple, no maneja 'user', solo pone los campos como no requeridos.
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

# --- Formset Factory (Configuración para Lógica de Servidor) ---
AseguradoFormSet = inlineformset_factory(
    Poliza,
    Asegurado,
    form=AseguradoForm,
    extra=0,            # No mostrar formularios vacíos por defecto.
    min_num=0,          # No requerir un mínimo.
    validate_min=False,   # No validar el número mínimo.
    can_delete=True,
    fk_name='poliza'
)

class PolizaForm(forms.ModelForm):
    class Meta:
        model = Poliza
        # Usamos 'exclude' para asegurarnos de que todos los demás campos se incluyan.
        # 'usuario' y 'renovacion_de' se manejan en la vista.
        exclude = ('usuario', 'renovacion_de')

    def __init__(self, *args, **kwargs):
        # Extraemos 'user' para filtrar los desplegables.
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Asignamos clases CSS para el estilo.
        for field_name, field in self.fields.items():
            css_class = 'form-control'
            if isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            elif isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            
            field.widget.attrs.update({'class': css_class})

        if user:
            # Filtramos los desplegables para mostrar solo los datos del usuario.
            self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user)
            self.fields['aseguradora'].queryset = Aseguradora.objects.filter(usuario=user)

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio_vigencia")
        fecha_fin = cleaned_data.get("fecha_fin_vigencia")
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise ValidationError("La fecha de fin de vigencia no puede ser anterior a la fecha de inicio.")
        return cleaned_data
#---(PAGO CUOTA FORM)---

# --- FORMULARIO PARA EDITAR UNA CUOTA (DENTRO DE UN FORMSET) ---
    class Meta:
        model = PagoCuota
        fields = ['fecha_vencimiento_cuota', 'monto_cuota', 'estado', 'fecha_de_pago_realizado', 'notas_pago']
        widgets = {
            'fecha_vencimiento_cuota': forms.DateInput(attrs={'type': 'date'}),
            'fecha_de_pago_realizado': forms.DateInput(attrs={'type': 'date'}),
            'notas_pago': forms.Textarea(attrs={'rows': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control form-control-sm'
            field.widget.attrs.update({'class': css_class})

# --- FORMULARIO PARA MARCAR UNA CUOTA COMO PAGADA (ACCIÓN RÁPIDA) ---
class RegistrarPagoForm(forms.ModelForm):
    class Meta:
        model = PagoCuota
        # Solo los campos que el usuario llena al pagar
        fields = ['fecha_de_pago_realizado', 'notas_pago']
        widgets = {
            'fecha_de_pago_realizado': forms.DateInput(attrs={'type': 'date'}),
            'notas_pago': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacemos la fecha de pago obligatoria
        self.fields['fecha_de_pago_realizado'].required = True

#---(END PAGO CUOTA FORM)---

class SiniestroForm(forms.ModelForm):
    class Meta:
        model = Siniestro
        fields = ['fecha_ocurrencia', 'fecha_reporte', 'estado_siniestro', 'descripcion', 'monto_reclamado', 'monto_indemnizado']
        widgets = {
            'fecha_ocurrencia': forms.DateInput(attrs={'type': 'date'}),
            'fecha_reporte': forms.DateInput(attrs={'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
#---(END SINIESTRO FORM)---

class CuotaForm(forms.ModelForm):
    class Meta:
        model = PagoCuota
        fields = ['fecha_vencimiento_cuota', 'monto_cuota', 'estado', 'fecha_de_pago_realizado', 'notas_pago']
        widgets = {
            'fecha_vencimiento_cuota': forms.DateInput(attrs={'type': 'date'}),
            'fecha_de_pago_realizado': forms.DateInput(attrs={'type': 'date'}),
            'notas_pago': forms.Textarea(attrs={'rows': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control form-control-sm'
            field.widget.attrs.update({'class': css_class})