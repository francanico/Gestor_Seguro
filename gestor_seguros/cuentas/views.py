
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import RegistroUsuarioForm
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm 

def pagina_inicio(request):
    # Puedes pasar contexto adicional si es necesario
    # para mostrar información en la página de inicio
    context = {
        'titulo_pagina': 'Simplificamos la Gestión de tus Pólizas'
    }
    return render(request, 'pagina_inicio.html', context)




def registro_usuario(request):
    if request.user.is_authenticated:
        return redirect('dashboard') # O a la página de inicio pública

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Loguear al usuario automáticamente después del registro
            messages.success(request, '¡Registro exitoso! Ya puedes empezar a usar la plataforma.')
            return redirect('dashboard') # Redirigir al dashboard después del registro
        else:
            messages.error(request, 'Por favor corrige los errores abajo.')
    else:
        form = RegistroUsuarioForm()
    
    context = {
        'form': form,
        'titulo_pagina': 'Crear una Cuenta Nueva'
    }
    return render(request, 'cuentas/registro.html', context)


@login_required
def perfil_usuario(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, '¡Tu perfil ha sido actualizado exitosamente!')
            return redirect('cuentas:perfil_usuario') # Redirige a la misma página para ver los cambios
    else:
        u_form = UserUpdateForm(instance=request.user)

    context = {
        'u_form': u_form,
        'titulo_pagina': 'Mi Perfil'
    }
    return render(request, 'cuentas/perfil.html', context)