import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ActuacionMunicipalForm, GestionDenunciaForm, NuevaDenunciaForm
from .models import ActuacionMunicipal, Categoria, Denuncia, Evidencia, HistorialEstado, Ubicacion


def _denuncias_filtradas(request):
    """Aplica idénticos filtros y permisos al listado y a la exportación."""
    usuario = request.user
    if usuario.es_funcionario or usuario.es_administrador:
        qs = Denuncia.objects.all()
    else:
        qs = Denuncia.objects.filter(ciudadano=usuario)
    qs = qs.select_related('ciudadano', 'categoria', 'asignado_a', 'ubicacion', 'evidencia')

    estado = request.GET.get('estado', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    busqueda = request.GET.get('q', '').strip()[:100]
    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()
    solo_mias = request.GET.get('mias') == '1' and usuario.es_funcionario

    if estado in Denuncia.Estado.values:
        qs = qs.filter(estado=estado)
    if categoria.isdigit():
        qs = qs.filter(categoria_id=int(categoria))
    if busqueda:
        qs = qs.filter(
            Q(titulo__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(ubicacion__direccion__icontains=busqueda)
        )
    for texto, operacion in [(desde, 'gte'), (hasta, 'lte')]:
        try:
            fecha = date.fromisoformat(texto)
        except ValueError:
            continue
        qs = qs.filter(**{f'creado__date__{operacion}': fecha})
    if solo_mias:
        qs = qs.filter(asignado_a=usuario)
    return qs.order_by('-creado', '-pk'), {
        'estado_actual': estado, 'categoria_actual': categoria,
        'q_actual': busqueda, 'desde_actual': desde, 'hasta_actual': hasta,
        'mias_actual': solo_mias,
    }


@login_required
def listado(request):
    denuncias, filtros = _denuncias_filtradas(request)
    paginador = Paginator(denuncias, 10)
    pagina = paginador.get_page(request.GET.get('pagina'))
    return render(request, 'denuncias/listado.html', {
        'denuncias': pagina,
        'pagina': pagina,
        'total_filtrado': paginador.count,
        'estados': Denuncia.Estado.choices,
        'categorias': Categoria.objects.filter(activa=True),
        'querystring': request.GET.copy(),
        **filtros,
    })


def _csv_seguro(valor):
    """Evita interpretar datos de ciudadanos como fórmulas de Excel."""
    texto = str(valor or '')
    if texto.lstrip().startswith(('=', '+', '-', '@')) or texto.startswith(('\t', '\r', '\n')):
        return "'" + texto
    return texto


@login_required
def exportar_csv(request):
    if not (request.user.es_funcionario or request.user.es_administrador):
        return HttpResponseForbidden('Solo el personal municipal puede exportar reportes.')
    denuncias, _ = _denuncias_filtradas(request)
    respuesta = HttpResponse(content_type='text/csv; charset=utf-8')
    respuesta['Content-Disposition'] = 'attachment; filename="denuncias_pirapo.csv"'
    respuesta.write('\ufeff')
    escritor = csv.writer(respuesta)
    escritor.writerow(['ID', 'Fecha', 'Título', 'Categoría', 'Descripción',
                       'Ubicación', 'Estado', 'Ciudadano', 'Funcionario responsable'])
    for d in denuncias.iterator():
        escritor.writerow([
            d.pk, d.creado.strftime('%d/%m/%Y %H:%M'), _csv_seguro(d.nombre_corto),
            _csv_seguro(d.categoria.nombre), _csv_seguro(d.descripcion),
            _csv_seguro(d.direccion or f'{d.latitud}, {d.longitud}'),
            d.get_estado_display(), _csv_seguro(d.ciudadano.username),
            _csv_seguro(str(d.asignado_a)) if d.asignado_a else 'Sin asignar',
        ])
    return respuesta


@login_required
def nueva(request):
    if request.user.rol != 'CIUDADANO' or request.user.is_superuser:
        return HttpResponseForbidden('Solo los ciudadanos pueden registrar denuncias.')
    form = NuevaDenunciaForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            denuncia = form.save(commit=False)
            denuncia.ciudadano = request.user
            denuncia.estado = Denuncia.Estado.PENDIENTE
            denuncia.save()
            ubicacion = Ubicacion(
                denuncia=denuncia,
                direccion=form.cleaned_data.get('direccion', '').strip(),
                latitud=form.cleaned_data.get('latitud'),
                longitud=form.cleaned_data.get('longitud'),
            )
            ubicacion.full_clean()
            ubicacion.save()
            foto = form.cleaned_data.get('foto')
            if foto:
                Evidencia.objects.create(denuncia=denuncia, archivo=foto)
            HistorialEstado.objects.create(
                denuncia=denuncia, usuario=request.user, accion='CREACION',
                estado_nuevo=Denuncia.Estado.PENDIENTE,
                observacion='Denuncia registrada con estado Pendiente.',
            )
        messages.success(request, f'Denuncia #{denuncia.pk} registrada correctamente.')
        return redirect('denuncias:detalle', pk=denuncia.pk)
    return render(request, 'denuncias/nueva.html', {'form': form})


@login_required
def detalle(request, pk):
    usuario = request.user
    qs = Denuncia.objects.select_related('categoria', 'ciudadano', 'asignado_a', 'ubicacion', 'evidencia')
    if not (usuario.es_funcionario or usuario.es_administrador):
        qs = qs.filter(ciudadano=usuario)
    denuncia = get_object_or_404(qs, pk=pk)
    return render(request, 'denuncias/detalle.html', {
        'denuncia': denuncia,
        'actuaciones': denuncia.actuaciones.select_related('funcionario').all()
        if (usuario.es_funcionario or usuario.es_administrador) else None,
    })


@login_required
def gestionar(request, pk):
    if not request.user.es_funcionario:
        return HttpResponseForbidden('Solo los funcionarios municipales pueden gestionar denuncias.')
    denuncia = get_object_or_404(Denuncia, pk=pk)
    form = GestionDenunciaForm(request.POST or None, instance=denuncia)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            # Bloqueo para evitar historiales incorrectos ante dos ediciones simultáneas.
            actual = Denuncia.objects.select_for_update().get(pk=pk)
            estado_anterior = actual.estado
            asignado_anterior = actual.asignado_a_id
            actual.estado = form.cleaned_data['estado']
            actual.asignado_a = form.cleaned_data['asignado_a']
            actual.full_clean()
            actual.save()
            if estado_anterior != actual.estado:
                HistorialEstado.objects.create(
                    denuncia=actual, usuario=request.user, funcionario=request.user,
                    accion='CAMBIO_ESTADO', estado_anterior=estado_anterior,
                    estado_nuevo=actual.estado,
                    observacion=f'{dict(Denuncia.Estado.choices)[estado_anterior]} → {actual.get_estado_display()}.',
                )
            if asignado_anterior != actual.asignado_a_id:
                HistorialEstado.objects.create(
                    denuncia=actual, usuario=request.user, funcionario=request.user,
                    accion='ASIGNACION', observacion=f"Responsable: {actual.asignado_a or 'Sin asignar'}.",
                )
        messages.success(request, 'Denuncia actualizada correctamente.')
        return redirect('denuncias:detalle', pk=pk)
    return render(request, 'denuncias/gestionar.html', {'form': form, 'denuncia': denuncia})


@login_required
def registrar_actuacion(request, pk):
    """Registra una verificación municipal y opcionalmente actualiza el estado.

    No permite al ciudadano ni al administrador crear actuaciones.
    Cada registro es histórico; no modifica ni elimina visitas previas.
    """
    if not request.user.es_funcionario:
        return HttpResponseForbidden('Solo funcionarios municipales autorizados pueden verificar denuncias.')

    denuncia = get_object_or_404(
        Denuncia.objects.select_related('categoria', 'ubicacion', 'asignado_a'), pk=pk,
    )
    inicial = {
        'fecha_verificacion': timezone.localdate(),
        'lugar_verificado': denuncia.direccion or (
            f'{denuncia.latitud}, {denuncia.longitud}'
            if denuncia.latitud is not None and denuncia.longitud is not None else ''
        ),
    }
    form = ActuacionMunicipalForm(request.POST or None, initial=inicial)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            # Serializamos el cambio sobre esta denuncia para evitar estados cruzados.
            actual = Denuncia.objects.select_for_update().get(pk=pk)
            actuacion = form.save(commit=False)
            actuacion.denuncia = actual
            actuacion.funcionario = request.user
            actuacion.full_clean()
            actuacion.save()

            HistorialEstado.objects.create(
                denuncia=actual, usuario=request.user, funcionario=request.user,
                accion='VERIFICACION',
                observacion=f'Verificación municipal registrada el {actuacion.fecha_verificacion:%d/%m/%Y}.',
            )
            nuevo_estado = form.cleaned_data.get('nuevo_estado')
            if nuevo_estado and nuevo_estado != actual.estado:
                estado_anterior = actual.estado
                actual.estado = nuevo_estado
                actual.full_clean()
                actual.save(update_fields=['estado', 'actualizado'])
                HistorialEstado.objects.create(
                    denuncia=actual, usuario=request.user, funcionario=request.user,
                    accion='CAMBIO_ESTADO', estado_anterior=estado_anterior,
                    estado_nuevo=actual.estado,
                    observacion=(
                        f'Estado actualizado durante la verificación municipal: '
                        f'{dict(Denuncia.Estado.choices)[estado_anterior]} → {actual.get_estado_display()}.'
                    ),
                )
        messages.success(request, f'Verificación registrada en la denuncia #{pk}.')
        return redirect('denuncias:detalle', pk=pk)

    return render(request, 'denuncias/registrar_actuacion.html', {
        'denuncia': denuncia, 'form': form,
    })
