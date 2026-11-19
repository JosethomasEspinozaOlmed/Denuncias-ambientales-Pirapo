"""CRUD municipal; Django Admin queda disponible solo para uso técnico."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from denuncias.models import Categoria, Denuncia
from .admin_forms import (
    CambiarClaveForm, CategoriaMunicipalForm, UsuarioAltaForm, UsuarioEdicionForm,
)
from .models import Usuario


def solo_administrador(vista):
    @login_required
    @wraps(vista)
    def interna(request, *args, **kwargs):
        if not request.user.es_administrador:
            return HttpResponseForbidden('Esta sección está reservada a la administración municipal.')
        return vista(request, *args, **kwargs)
    return interna


def _roles_permitidos(request):
    roles = [Usuario.Rol.CIUDADANO, Usuario.Rol.FUNCIONARIO]
    # Solo el superusuario técnico puede conceder permisos administrativos.
    if request.user.is_superuser:
        roles.append(Usuario.Rol.ADMINISTRADOR)
    return roles


def _puede_modificar_actor(request, objetivo):
    if objetivo.pk == request.user.pk:
        return False  # Evitar quedarse sin acceso por error.
    if objetivo.is_superuser:
        return False  # Los superusuarios se gestionan solo desde Django Admin.
    if objetivo.rol == Usuario.Rol.ADMINISTRADOR and not request.user.is_superuser:
        return False
    return True


@solo_administrador
def panel(request):
    datos = {
        'total_usuarios': Usuario.objects.count(),
        'ciudadanos': Usuario.objects.filter(rol=Usuario.Rol.CIUDADANO, is_active=True).count(),
        'funcionarios': Usuario.objects.filter(rol=Usuario.Rol.FUNCIONARIO, is_active=True).count(),
        'categorias': Categoria.objects.filter(activa=True).count(),
        'denuncias': Denuncia.objects.count(),
        'pendientes': Denuncia.objects.filter(estado=Denuncia.Estado.PENDIENTE).count(),
    }
    return render(request, 'gestion/panel.html', {'resumen': datos})


@solo_administrador
def usuarios_listado(request):
    qs = Usuario.objects.all().order_by('username')
    q = request.GET.get('q', '').strip()[:100]
    rol = request.GET.get('rol', '').strip()
    estado = request.GET.get('estado', '').strip()
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) |
                       Q(first_name__icontains=q) | Q(last_name__icontains=q))
    if rol in Usuario.Rol.values:
        qs = qs.filter(rol=rol)
    if estado in ('activo', 'inactivo'):
        qs = qs.filter(is_active=(estado == 'activo'))
    pagina = Paginator(qs, 15).get_page(request.GET.get('pagina'))
    return render(request, 'gestion/usuarios.html', {
        'pagina': pagina, 'q': q, 'rol': rol, 'estado': estado,
        'roles': Usuario.Rol.choices,
    })


@solo_administrador
def usuario_nuevo(request):
    form = UsuarioAltaForm(request.POST or None, allowed_roles=_roles_permitidos(request))
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            usuario = form.save(commit=False)
            usuario.is_staff = False
            usuario.is_superuser = False
            usuario.is_active = True
            usuario.save()
        messages.success(request, f'Cuenta de {usuario.username} creada correctamente.')
        return redirect('administracion:usuarios')
    return render(request, 'gestion/usuario_form.html', {
        'form': form, 'titulo': 'Nuevo usuario', 'creando': True,
    })


@solo_administrador
def usuario_editar(request, pk):
    objetivo = get_object_or_404(Usuario, pk=pk)
    if not _puede_modificar_actor(request, objetivo):
        return HttpResponseForbidden('No se permite modificar esta cuenta desde el panel municipal.')
    form = UsuarioEdicionForm(
        request.POST or None, instance=objetivo, allowed_roles=_roles_permitidos(request),
    )
    if request.method == 'POST' and form.is_valid():
        # El formulario no expone is_staff, is_superuser ni is_active.
        form.save()
        messages.success(request, 'Datos del usuario actualizados.')
        return redirect('administracion:usuarios')
    return render(request, 'gestion/usuario_form.html', {
        'form': form, 'titulo': 'Editar usuario', 'creando': False, 'objetivo': objetivo,
    })


@solo_administrador
@require_POST
def usuario_estado(request, pk):
    objetivo = get_object_or_404(Usuario, pk=pk)
    if not _puede_modificar_actor(request, objetivo):
        return HttpResponseForbidden('No se permite cambiar el estado de esta cuenta.')
    if objetivo.is_active and objetivo.rol == Usuario.Rol.FUNCIONARIO:
        if Denuncia.objects.filter(asignado_a=objetivo).exclude(estado=Denuncia.Estado.RESUELTO).exists():
            messages.error(request, 'Antes de desactivar este funcionario, reasigná sus denuncias pendientes o en proceso.')
            return redirect('administracion:usuarios')
    objetivo.is_active = not objetivo.is_active
    objetivo.save(update_fields=['is_active'])
    messages.success(request, 'Cuenta activada.' if objetivo.is_active else 'Cuenta desactivada.')
    return redirect('administracion:usuarios')


@solo_administrador
def usuario_clave(request, pk):
    objetivo = get_object_or_404(Usuario, pk=pk)
    if not _puede_modificar_actor(request, objetivo):
        return HttpResponseForbidden('No se permite cambiar la clave de esta cuenta.')
    form = CambiarClaveForm(objetivo, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Contraseña actualizada. El usuario deberá utilizar la nueva clave.')
        return redirect('administracion:usuarios')
    return render(request, 'gestion/usuario_clave.html', {'form': form, 'objetivo': objetivo})


@solo_administrador
def categorias_listado(request):
    q = request.GET.get('q', '').strip()[:100]
    qs = Categoria.objects.all().order_by('nombre')
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    pagina = Paginator(qs, 15).get_page(request.GET.get('pagina'))
    return render(request, 'gestion/categorias.html', {'pagina': pagina, 'q': q})


@solo_administrador
def categoria_nueva(request):
    form = CategoriaMunicipalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Categoría agregada correctamente.')
        return redirect('administracion:categorias')
    return render(request, 'gestion/categoria_form.html', {
        'form': form, 'titulo': 'Nueva categoría',
    })


@solo_administrador
def categoria_editar(request, pk):
    objetivo = get_object_or_404(Categoria, pk=pk)
    form = CategoriaMunicipalForm(request.POST or None, instance=objetivo)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Categoría actualizada correctamente.')
        return redirect('administracion:categorias')
    return render(request, 'gestion/categoria_form.html', {
        'form': form, 'titulo': 'Editar categoría', 'objetivo': objetivo,
    })


@solo_administrador
@require_POST
def categoria_estado(request, pk):
    objetivo = get_object_or_404(Categoria, pk=pk)
    objetivo.activa = not objetivo.activa
    objetivo.save(update_fields=['activa'])
    messages.success(request, 'Categoría habilitada.' if objetivo.activa else 'Categoría desactivada.')
    return redirect('administracion:categorias')
