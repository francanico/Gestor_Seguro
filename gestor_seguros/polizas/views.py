# polizas/views.py
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Poliza, Aseguradora
from .forms import PolizaForm, AseguradoraForm
from clientes.models import Cliente # Para el selector de clientes
from django.db.models import F, ExpressionWrapper, DateField
from django.db.models.functions import ExtractMonth, ExtractDay

# Constantes para estados de póliza activos
ESTADOS_POLIZA_ACTIVOS = ['VIGENTE', 'PENDIENTE_PAGO']

# --- Vistas para Aseguradoras ---
class AseguradoraListView(LoginRequiredMixin, ListView):
    model = Aseguradora
    template_name = 'polizas/aseguradora_list.html'
    context_object_name = 'aseguradoras'
    paginate_by = 10

class AseguradoraCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Aseguradora
    form_class = AseguradoraForm
    template_name = 'polizas/aseguradora_form.html'
    success_url = reverse_lazy('polizas:lista_aseguradoras')
    success_message = "Aseguradora '%(nombre)s' creada exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Registrar Nueva Aseguradora"
        context['boton_submit'] = "Crear Aseguradora"
        return context
    
    def form_valid(self, form):
        form.instance.usuario = self.request.user # Asigna el usuario
        return super().form_valid(form)
    


class AseguradoraUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Aseguradora
    form_class = AseguradoraForm
    template_name = 'polizas/aseguradora_form.html'
    success_url = reverse_lazy('polizas:lista_aseguradoras')
    success_message = "Aseguradora '%(nombre)s' actualizada exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Aseguradora"
        context['boton_submit'] = "Actualizar Aseguradora"
        return context

class AseguradoraDeleteView(LoginRequiredMixin, DeleteView): # SuccessMessageMixin da problemas con %()s en DeleteView a veces
    model = Aseguradora
    template_name = 'polizas/aseguradora_confirm_delete.html'
    success_url = reverse_lazy('polizas:lista_aseguradoras')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Aseguradora '{obj.nombre}' eliminada exitosamente.")
        return super(AseguradoraDeleteView, self).delete(request, *args, **kwargs)


# --- Vistas para Pólizas ---
class PolizaListView(LoginRequiredMixin, ListView):
    model = Poliza
    template_name = 'polizas/poliza_list.html'
    context_object_name = 'polizas'
    paginate_by = 10

    def get_queryset(self):
        queryset = Poliza.objects.select_related('cliente', 'aseguradora')
        filtro = self.request.GET.get('filtro_dashboard')
        hoy = timezone.now().date()
        ESTADOS_RELEVANTES = ['VIGENTE', 'PENDIENTE_PAGO']

        if filtro == 'vencidas':
            queryset = queryset.filter(fecha_fin_vigencia__lt=hoy, estado_poliza__in=ESTADOS_RELEVANTES)
            self.request.session['titulo_lista_polizas'] = "Pólizas Vencidas" # Opcional para el título
        elif filtro == 'vencer30':
            proximos_30_dias = hoy + timedelta(days=30)
            queryset = queryset.filter(fecha_fin_vigencia__gte=hoy, fecha_fin_vigencia__lte=proximos_30_dias, estado_poliza__in=ESTADOS_RELEVANTES)
            self.request.session['titulo_lista_polizas'] = "Pólizas Venciendo en Menos de 30 Días"
        elif filtro == 'vencer60':
            proximos_30_dias = hoy + timedelta(days=30)
            proximos_60_dias = hoy + timedelta(days=60)
            queryset = queryset.filter(fecha_fin_vigencia__gt=proximos_30_dias, fecha_fin_vigencia__lte=proximos_60_dias, estado_poliza__in=ESTADOS_RELEVANTES)
            self.request.session['titulo_lista_polizas'] = "Pólizas Venciendo en 31-60 Días"
        else:
            # Podrías limpiar el título si no hay filtro o es otro tipo de filtro
            if 'titulo_lista_polizas' in self.request.session:
                del self.request.session['titulo_lista_polizas']


        # También podrías añadir otros filtros aquí, por ejemplo, búsqueda por texto
        # query_busqueda = self.request.GET.get('q')
        # if query_busqueda:
        #     queryset = queryset.filter(numero_poliza__icontains=query_busqueda) # O buscar en más campos

        return queryset.order_by('-fecha_fin_vigencia')


    def get_queryset(self):
        # Filtra el queryset para mostrar solo los clientes del usuario actual
        queryset = super().get_queryset().filter(usuario=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar el título dinámico a la plantilla si se estableció
        context['titulo_dinamico_lista'] = self.request.session.get('titulo_lista_polizas', "Lista de Pólizas")
        # Limpiar el título de la sesión después de usarlo para que no persista
        # if 'titulo_lista_polizas' in self.request.session:
        #     del self.request.session['titulo_lista_polizas']
        return context

class PolizaDetailView(LoginRequiredMixin, DetailView):
    model = Poliza
    template_name = 'polizas/poliza_detail.html'
    context_object_name = 'poliza'

    def get_queryset(self):
        return super().get_queryset().select_related('cliente', 'aseguradora')

class PolizaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Poliza
    form_class = PolizaForm
    template_name = 'polizas/poliza_form.html'
    # success_url = reverse_lazy('polizas:lista_polizas') # O redirigir al detalle
    success_message = "Póliza No. '%(numero_poliza)s' creada exitosamente."

    def get_success_url(self):
        return reverse_lazy('polizas:detalle_poliza', kwargs={'pk': self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        cliente_id = self.request.GET.get('cliente_id')
        if cliente_id:
            try:
                initial['cliente'] = Cliente.objects.get(pk=cliente_id)
            except Cliente.DoesNotExist:
                pass
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Registrar Nueva Póliza"
        context['boton_submit'] = "Crear Póliza"
        return context

    def get_form_kwargs(self):
        # Pasa el usuario al __init__ del formulario
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)

class PolizaUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Poliza
    form_class = PolizaForm
    template_name = 'polizas/poliza_form.html'
    # success_url = reverse_lazy('polizas:lista_polizas')
    success_message = "Póliza No. '%(numero_poliza)s' actualizada exitosamente."

    def get_success_url(self):
        return reverse_lazy('polizas:detalle_poliza', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Póliza"
        context['boton_submit'] = "Actualizar Póliza"
        return context

class PolizaDeleteView(LoginRequiredMixin, DeleteView):
    model = Poliza
    template_name = 'polizas/poliza_confirm_delete.html'
    success_url = reverse_lazy('polizas:lista_polizas')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Póliza No. '{obj.numero_poliza}' eliminada exitosamente.")
        return super(PolizaDeleteView, self).delete(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        return self.model.objects.filter(usuario=self.request.user)

# --- Dashboard y Recordatorios ---
@login_required
def dashboard_view(request):

    hoy = timezone.now().date()
    proximos_30_dias = hoy + timedelta(days=30)
    proximos_60_dias = hoy + timedelta(days=60)
    proximos_90_dias = hoy + timedelta(days=90)
    mes_actual = hoy.month
    dia_actual = hoy.day

    # Clientes cuyo cumpleaños es en el mes actual
    cumpleaneros_mes = Cliente.objects.filter(
        usuario=request.user,
        fecha_nacimiento__month=mes_actual
    ).order_by('fecha_nacimiento__day', 'fecha_nacimiento__month')

    ESTADOS_POLIZA_ACTIVOS= ['VIGENTE', 'PENDIENTE_PAGO']

    polizas_vencidas = Poliza.objects.filter(
        usuario=request.user,
        fecha_fin_vigencia__lt=hoy,
        estado_poliza__in=ESTADOS_POLIZA_ACTIVOS # Solo mostrar las que estaban activas
    ).select_related('cliente', 'aseguradora').order_by('fecha_fin_vigencia')

    polizas_a_vencer_30 = Poliza.objects.filter(
        usuario=request.user,
        fecha_fin_vigencia__gte=hoy,
        fecha_fin_vigencia__lte=proximos_30_dias,
        estado_poliza__in=ESTADOS_POLIZA_ACTIVOS
    ).select_related('cliente', 'aseguradora').order_by('fecha_fin_vigencia')
    
    polizas_a_vencer_60 = Poliza.objects.filter(
        usuario=request.user,
        fecha_fin_vigencia__gt=proximos_30_dias,
        fecha_fin_vigencia__lte=proximos_60_dias,
        estado_poliza__in=ESTADOS_POLIZA_ACTIVOS
    ).select_related('cliente', 'aseguradora').order_by('fecha_fin_vigencia')

    # Puedes añadir más rangos si es necesario

   # Pólizas pendientes de cobro de comisión
    comisiones_pendientes = Poliza.objects.filter(
        usuario=request.user,
        comision_cobrada=False,
        comision_monto__gt=0  # <-- CAMBIO CLAVE: Busca donde el monto sea mayor a 0
    ).select_related('cliente', 'aseguradora').order_by('fecha_fin_vigencia')

    total_clientes = Cliente.objects.filter(usuario=request.user).count()
    total_polizas_vigentes = Poliza.objects.filter(usuario=request.user, estado_poliza='VIGENTE').count()
    
    context = {
        'polizas_vencidas': polizas_vencidas,
        'polizas_a_vencer_30': polizas_a_vencer_30,
        'polizas_a_vencer_60': polizas_a_vencer_60,
        'comisiones_pendientes': comisiones_pendientes,
        'cumpleaneros_mes': cumpleaneros_mes,
        'total_clientes': total_clientes,
        'total_polizas_vigentes': total_polizas_vigentes,
        'titulo_pagina': "Dashboard de Pólizas",
    }

    return render(request, 'polizas/dashboard.html', context)


