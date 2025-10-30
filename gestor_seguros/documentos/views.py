from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Documento
from .forms import DocumentoForm

@login_required
def subir_documento(request, content_type_id, object_id):
    content_type = get_object_or_404(ContentType, pk=content_type_id)
    parent_object = get_object_or_404(content_type.model_class(), pk=object_id)

    # Verificación de propiedad
    if not hasattr(parent_object, 'usuario') or parent_object.usuario != request.user:
        messages.error(request, "No tienes permiso para añadir documentos a este objeto.")
        return redirect('dashboard') # O a donde prefieras

    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.usuario = request.user
            documento.content_object = parent_object
            documento.save()
            messages.success(request, "Documento subido exitosamente.")
            return redirect(parent_object.get_absolute_url())
    
    # Esta vista solo procesa POST, así que redirigimos si es GET
    return redirect(parent_object.get_absolute_url())

@login_required
def eliminar_documento(request, pk):
    documento = get_object_or_404(Documento, pk=pk, usuario=request.user)
    parent_object_url = documento.content_object.get_absolute_url()
    
    if request.method == 'POST':
        documento.archivo.delete() # Borrar el archivo físico
        documento.delete() # Borrar el registro de la BD
        messages.success(request, "Documento eliminado exitosamente.")
        return redirect(parent_object_url)
        
    # Para mostrar una confirmación (opcional, pero recomendado)
    return render(request, 'documentos/documento_confirm_delete.html', {'documento': documento})