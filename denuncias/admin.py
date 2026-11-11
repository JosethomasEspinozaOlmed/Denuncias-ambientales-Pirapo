from django.contrib import admin
from .models import Categoria, Denuncia, Evidencia, HistorialEstado, Ubicacion


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion", "activa")
    list_editable = ("activa",)
    search_fields = ("nombre",)


class UbicacionInline(admin.StackedInline):
    model = Ubicacion
    extra = 0
    can_delete = False
    readonly_fields = ("direccion", "latitud", "longitud")

    def has_add_permission(self, request, obj=None):
        return False


class EvidenciaInline(admin.StackedInline):
    model = Evidencia
    extra = 0
    can_delete = False
    readonly_fields = ("archivo", "fecha_carga")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Denuncia)
class DenunciaAdmin(admin.ModelAdmin):
    list_display = ("id", "categoria", "ciudadano", "estado", "asignado_a", "creado")
    list_filter = ("estado", "categoria", "creado")
    search_fields = ("descripcion", "ciudadano__username", "ubicacion__direccion")
    inlines = [UbicacionInline, EvidenciaInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HistorialEstado)
class HistorialAdmin(admin.ModelAdmin):
    list_display = ("denuncia", "usuario", "funcionario", "accion", "estado_anterior", "estado_nuevo", "fecha")
    list_filter = ("accion", "fecha")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
