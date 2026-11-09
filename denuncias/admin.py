from django.contrib import admin
from .models import Categoria, Denuncia, HistorialDenuncia

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa")
    list_editable = ("activa",)
    search_fields = ("nombre",)

@admin.register(Denuncia)
class DenunciaAdmin(admin.ModelAdmin):
    list_display = ("id", "categoria", "ciudadano", "estado", "asignado_a", "creado")
    list_filter = ("estado", "categoria", "creado")
    search_fields = ("descripcion", "ciudadano__username")

    # En el prototipo se permite consulta administrativa, NO cambio de estado desde admin.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(HistorialDenuncia)
class HistorialAdmin(admin.ModelAdmin):
    list_display = ("denuncia", "usuario", "accion", "fecha")
    list_filter = ("accion", "fecha")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
