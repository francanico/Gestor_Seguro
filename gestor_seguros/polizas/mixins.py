# polizas/mixins.py
from django.core.exceptions import PermissionDenied

class OwnerRequiredMixin:
    """
    Este Mixin asegura que el usuario que hace la petición
    es el dueño del objeto que intenta ver/editar/eliminar.
    """
    def get_queryset(self):
        # Obtiene el queryset base de la vista
        qs = super().get_queryset()
        # Filtra por el usuario logueado
        return qs.filter(usuario=self.request.user)