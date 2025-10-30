# clientes/views.py
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin # Para proteger vistas
from .models import Cliente
from .forms import ClienteForm

# Para proteger todas las vistas de esta app, puedes usar @method_decorator(login_required)
# o heredar de LoginRequiredMixin para cada CBV.

class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'clientes/cliente_list.html' # clientes/lista_clientes.html
    context_object_name = 'clientes'
    paginate_by = 10 # Opcional: paginación

    def get_queryset(self):
        # Filtra el queryset para mostrar solo los clientes del usuario actual
        queryset = super().get_queryset().filter(usuario=self.request.user)
        return queryset

class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'clientes/cliente_detail.html'
    context_object_name = 'cliente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['polizas_cliente'] = obj.polizas.all().order_by('-fecha_fin_vigencia')
        context['content_type'] = ContentType.objects.get_for_model(obj) # <-- LÍNEA CLAVE
        return context
    
    def get_queryset(self):
        # Asegura que el usuario solo puede editar SUS PROPIOS clientes.
        # Si intenta acceder a un cliente de otro usuario, obtendrá un 404.
        return self.model.objects.filter(usuario=self.request.user)

class ClienteCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:lista_clientes') # Redirige a la lista después de crear
    success_message = "Cliente '%(nombre_completo)s' creado exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Registrar Nuevo Cliente"
        context['boton_submit'] = "Crear Cliente"
        return context

    def form_valid(self, form):
        form.instance.usuario = self.request.user # Asigna el usuario logueado
        return super().form_valid(form)

class ClienteUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:lista_clientes')
    success_message = "Cliente '%(nombre_completo)s' actualizado exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Cliente"
        context['boton_submit'] = "Actualizar Cliente"
        return context
    
    def get_queryset(self):
        # Asegura que el usuario solo puede editar SUS PROPIOS clientes.
        # Si intenta acceder a un cliente de otro usuario, obtendrá un 404.
        return self.model.objects.filter(usuario=self.request.user)

class ClienteDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Cliente
    template_name = 'clientes/cliente_confirm_delete.html'
    success_url = reverse_lazy('clientes:lista_clientes')
    success_message = "Cliente eliminado exitosamente." # No se puede usar %(nombre_completo)s aquí directamente
    # Para el mensaje con nombre, puedes sobreescribir delete()

    def delete(self, request, *args, **kwargs):
        # from django.contrib import messages # Importar si no está ya
        # obj = self.get_object()
        # messages.success(self.request, f"Cliente '{obj.nombre_completo}' eliminado exitosamente.")
        return super(ClienteDeleteView, self).delete(request, *args, **kwargs)
    
    def get_queryset(self):
        # Asegura que el usuario solo puede editar SUS PROPIOS clientes.
        # Si intenta acceder a un cliente de otro usuario, obtendrá un 404.
        return self.model.objects.filter(usuario=self.request.user)