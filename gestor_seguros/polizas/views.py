# polizas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Poliza, Aseguradora,PagoCuota,Siniestro 
from .forms import PolizaForm, AseguradoraForm,PagoCuotaForm,SiniestroForm
from clientes.models import Cliente # Para el selector de clientes
from django.db.models import F, ExpressionWrapper, DateField
from django.db.models.functions import ExtractMonth, ExtractDay
import copy
from .mixins import OwnerRequiredMixin

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

class PolizaDetailView(LoginRequiredMixin,OwnerRequiredMixin, DetailView):
    model = Poliza
    template_name = 'polizas/poliza_detail.html'
    context_object_name = 'poliza'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poliza = self.get_object()

        # Formulario para registrar un nuevo pago
        pago_form = PagoCuotaForm(initial={
            'monto_pagado': poliza.valor_cuota or poliza.prima_total_anual,
            'fecha_cuota_correspondiente': poliza.proxima_fecha_cobro
        })
        context['pago_form'] = pago_form
        
        # Lista de pagos existentes
        context['pagos_realizados'] = poliza.pagos_cuotas.all()

            # Lista de siniestros asociados
        context['siniestros_asociados'] = self.object.siniestros.all()

        
        # ContentType para uso en formularios genéricos
        obj = self.get_object()
        context['content_type'] = ContentType.objects.get_for_model(obj)
        
        return context

    def post(self, request, *args, **kwargs):
        poliza = self.get_object()
        form = PagoCuotaForm(request.POST)

        if form.is_valid():
            nuevo_pago = form.save(commit=False)
            nuevo_pago.poliza = poliza
            nuevo_pago.save()
            messages.success(request, '¡Pago de cuota registrado exitosamente!')
            return redirect(poliza.get_absolute_url())
        else:
            # Si el formulario no es válido, volvemos a renderizar la página con los errores
            context = self.get_context_data()
            context['pago_form'] = form # Pasamos el formulario con errores
            messages.error(request, 'Hubo un error al registrar el pago. Por favor, revisa los datos.')
            return self.render_to_response(context)

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

@login_required
def renovar_poliza(request, pk):
    # Obtenemos la póliza original, asegurándonos de que pertenece al usuario
    poliza_original = get_object_or_404(Poliza, pk=pk, usuario=request.user)

    # Creamos una copia de la póliza en memoria (aún no en la BD)
    poliza_nueva = copy.copy(poliza_original)
    poliza_nueva.pk = None  # Quitamos el ID para que se cree un nuevo registro
    poliza_nueva.id = None

    # --- Calculamos las nuevas fechas ---
    # La nueva póliza empieza el día después de que termina la original
    if poliza_original.fecha_fin_vigencia:
        nueva_fecha_inicio = poliza_original.fecha_fin_vigencia + timedelta(days=1)
        
        # Calculamos la duración de la póliza original
        duracion = poliza_original.fecha_fin_vigencia - poliza_original.fecha_inicio_vigencia
        
        # La nueva fecha de fin es la nueva de inicio más la duración
        nueva_fecha_fin = nueva_fecha_inicio + duracion
        
        poliza_nueva.fecha_inicio_vigencia = nueva_fecha_inicio
        poliza_nueva.fecha_fin_vigencia = nueva_fecha_fin
    
    # Reiniciamos estados y fechas de la nueva póliza
    poliza_nueva.estado_poliza = 'EN_TRAMITE'
    poliza_nueva.comision_cobrada = False
    poliza_nueva.fecha_cobro_comision = None
    poliza_nueva.ultimo_pago_cubierto_hasta = None
    poliza_nueva.fecha_emision = timezone.now().date()
    # Generamos un número de póliza sugerido para la renovación
    poliza_nueva.numero_poliza = f"{poliza_original.numero_poliza}-REN"

    # Guardamos la nueva póliza para poder editarla
    poliza_nueva.save()

    # Marcamos la póliza original como "RENOVADA"
    poliza_original.estado_poliza = 'RENOVADA'
    poliza_original.save()

    messages.info(request, f"Póliza {poliza_original.numero_poliza} marcada como renovada. "
                        f"Estás editando la nueva póliza de renovación.")
    
    # Redirigimos al formulario de EDICIÓN de la NUEVA póliza
    return redirect('polizas:editar_poliza', pk=poliza_nueva.pk)

# --- Dashboard y Recordatorios ---
@login_required
def dashboard_view(request):
    hoy = timezone.now().date()
    
    # --- 1. DEFINICIÓN DE QUERIES BASE ---
    
    # Estados que consideramos "en juego" para el dashboard (excluimos las resueltas)
    estados_activos_dashboard = ['VIGENTE', 'PENDIENTE_PAGO', 'VENCIDA', 'EN_TRAMITE']

    # Queryset base para todas las pólizas del usuario que no están resueltas
    base_polizas_query = Poliza.objects.filter(
        usuario=request.user,
        estado_poliza__in=estados_activos_dashboard
    ).select_related('cliente', 'aseguradora')

    # Queryset específico para pólizas "activas" (no vencidas)
    polizas_activas = base_polizas_query.filter(fecha_fin_vigencia__gte=hoy)


    # --- 2. CÁLCULOS PARA LAS TARJETAS DEL DASHBOARD ---

    # Pólizas vencidas (las que su fin de vigencia ya pasó)
    polizas_vencidas = base_polizas_query.filter(fecha_fin_vigencia__lt=hoy).order_by('fecha_fin_vigencia')
    
    # Pólizas a vencer en los próximos 30 días
    proximos_30_dias = hoy + timedelta(days=30)
    polizas_a_vencer_30 = polizas_activas.filter(fecha_fin_vigencia__range=(hoy, proximos_30_dias)).order_by('fecha_fin_vigencia')

    # Pólizas a vencer entre 31 y 60 días
    proximos_60_dias = hoy + timedelta(days=60)
    polizas_a_vencer_60 = polizas_activas.filter(fecha_fin_vigencia__range=(proximos_30_dias + timedelta(days=1), proximos_60_dias)).order_by('fecha_fin_vigencia')


    # --- 3. LÓGICA PARA PRÓXIMOS COBROS ---
    # Usamos el queryset 'polizas_activas' que ya definimos arriba
    polizas_con_cobros_periodicos = polizas_activas.exclude(frecuencia_pago='UNICO')

    proximos_30_dias_cobro = hoy + timedelta(days=30)
    cobros_pendientes_30_dias = []
    for poliza in polizas_con_cobros_periodicos:
        dias = poliza.dias_para_proximo_cobro
        if dias is not None and 0 <= dias <= 30:
            cobros_pendientes_30_dias.append(poliza)
    
    cobros_pendientes_30_dias.sort(key=lambda p: p.proxima_fecha_cobro)


    # --- 4. OTRAS CONSULTAS DEL DASHBOARD ---

    # Pólizas pendientes de cobro de comisión
    comisiones_pendientes = base_polizas_query.filter(
        comision_cobrada=False,
        comision_monto__gt=0
    ).order_by('fecha_fin_vigencia')

    # Cumpleaños del mes
    mes_actual = hoy.month
    cumpleaneros_mes = Cliente.objects.filter(
        usuario=request.user,
        fecha_nacimiento__month=mes_actual
    ).order_by('fecha_nacimiento__day')

    # Indicadores totales
    total_clientes = Cliente.objects.filter(usuario=request.user).count()
    total_polizas_vigentes = polizas_activas.filter(estado_poliza='VIGENTE').count()


    # --- 5. CONTEXTO PARA LA PLANTILLA ---
    context = {
        'hoy': hoy,
        'polizas_vencidas': polizas_vencidas,
        'polizas_a_vencer_30': polizas_a_vencer_30,
        'polizas_a_vencer_60': polizas_a_vencer_60,
        'cobros_pendientes_30_dias': cobros_pendientes_30_dias,
        'comisiones_pendientes': comisiones_pendientes,
        'cumpleaneros_mes': cumpleaneros_mes,
        'total_clientes': total_clientes,
        'total_polizas_vigentes': total_polizas_vigentes,
        'titulo_pagina': "Dashboard de Pólizas",
    }
    
    return render(request, 'polizas/dashboard.html', context)


# ---  VISTA DE ACCIÓN RÁPIDA PARA REGISTRAR PAGO ---
@login_required
def registrar_pago_rapido(request, pk):
    # Solo permitimos peticiones POST para esta acción por seguridad
    if request.method == 'POST':
        poliza = get_object_or_404(Poliza, pk=pk, usuario=request.user)
        
        # Obtenemos la fecha de la cuota desde los datos del formulario que enviaremos
        fecha_cuota_str = request.POST.get('fecha_cuota')
        
        if fecha_cuota_str:
            fecha_cuota = parse_date(fecha_cuota_str)
            
            # Verificamos que no estemos registrando un pago duplicado para esa cuota
            if not PagoCuota.objects.filter(poliza=poliza, fecha_cuota_correspondiente=fecha_cuota).exists():
                PagoCuota.objects.create(
                    poliza=poliza,
                    fecha_pago=timezone.now().date(),
                    monto_pagado=poliza.valor_cuota or poliza.prima_total_anual,
                    fecha_cuota_correspondiente=fecha_cuota,
                    notas="Pago rápido registrado desde el dashboard."
                )
                messages.success(request, f"Pago para la póliza {poliza.numero_poliza} registrado exitosamente.")
            else:
                messages.warning(request, f"El pago para esa cuota de la póliza {poliza.numero_poliza} ya había sido registrado.")
        else:
            messages.error(request, "No se proporcionó la fecha de la cuota para registrar el pago.")
            
    # Redirigimos siempre al dashboard
    return redirect('dashboard')


#---(VISTAS SINIESTROS)---
class SiniestroCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Siniestro
    form_class = SiniestroForm
    template_name = 'polizas/siniestro_form.html'
    success_message = "Siniestro reportado exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['poliza'] = get_object_or_404(Poliza, pk=self.kwargs['poliza_pk'], usuario=self.request.user)
        context['titulo_pagina'] = "Reportar Nuevo Siniestro"
        return context

    def form_valid(self, form):
        poliza = get_object_or_404(Poliza, pk=self.kwargs['poliza_pk'], usuario=self.request.user)
        form.instance.poliza = poliza
        form.instance.usuario = self.request.user
        return super().form_valid(form)

class SiniestroDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Siniestro
    template_name = 'polizas/siniestro_detail.html'
    
    def get_queryset(self):
        return super().get_queryset().select_related('poliza', 'poliza__cliente')

class SiniestroUpdateView(LoginRequiredMixin, OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Siniestro
    form_class = SiniestroForm
    template_name = 'polizas/siniestro_form.html'
    success_message = "Siniestro actualizado exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Siniestro"
        return context

class SiniestroDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Siniestro
    template_name = 'polizas/siniestro_confirm_delete.html'
    
    def get_success_url(self):
        messages.success(self.request, "Siniestro eliminado exitosamente.")
        # Redirige al detalle de la póliza a la que pertenecía el siniestro
        return reverse_lazy('polizas:detalle_poliza', kwargs={'pk': self.object.poliza.pk})
#---(END VISTAS SINIESTROS)---