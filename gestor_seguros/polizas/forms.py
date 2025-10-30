# polizas/forms.py
from django import forms
from .models import Poliza, Aseguradora, Cliente,PagoCuota,Siniestro 
from django.core.exceptions import ValidationError # <-- IMPORTAR



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


class PolizaForm(forms.ModelForm):
    class Meta:
        model = Poliza
        fields = [
            'cliente', 'aseguradora', 'numero_poliza', 'ramo_tipo_seguro',
            'descripcion_bien_asegurado', 'fecha_emision', 'fecha_inicio_vigencia',
            'fecha_fin_vigencia', 'prima_total_anual', 'frecuencia_pago',
            'valor_cuota', 'comision_monto', 'comision_cobrada',
            'fecha_cobro_comision', 'estado_poliza', 'notas_poliza',
            'archivo_poliza',
        ]
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date'}),
            'fecha_inicio_vigencia': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin_vigencia': forms.DateInput(attrs={'type': 'date'}),
            'fecha_cobro_comision': forms.DateInput(attrs={'type': 'date'}),
            'notas_poliza': forms.Textarea(attrs={'rows': 3}),
            'descripcion_bien_asegurado': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        # 1. "Capturamos" el argumento 'user' y lo eliminamos de kwargs
        user = kwargs.pop('user', None)
        
        # 2. Ahora llamamos al __init__ del padre con los kwargs ya "limpios"
        super().__init__(*args, **kwargs)

        # 3. Si el usuario fue pasado, filtramos los querysets
        if user:
            self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user).order_by('nombre_completo')
            self.fields['aseguradora'].queryset = Aseguradora.objects.filter(usuario=user).order_by('nombre')
        
        # 4. (Opcional) Aplicamos las clases CSS a los campos
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio_vigencia")
        fecha_fin = cleaned_data.get("fecha_fin_vigencia")

        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise ValidationError(
                    "La fecha de fin de vigencia no puede ser anterior a la fecha de inicio."
                )
        return cleaned_data

#---(PAGO CUOTA FORM)---

class PagoCuotaForm(forms.ModelForm):
    class Meta:
        model = PagoCuota
        fields = ['fecha_pago', 'monto_pagado', 'fecha_cuota_correspondiente', 'notas']
        widgets = {
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
            'fecha_cuota_correspondiente': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

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

