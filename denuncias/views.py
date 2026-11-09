from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from .forms import GestionDenunciaForm, NuevaDenunciaForm
from .models import Denuncia, HistorialDenuncia


@login_required
def listado(request):
    usuario = request.user
    if usuario.es_funcionario or usuario.es_administrador:
        qs = Denuncia.objects.select_related("ciudadano", "categoria", "asignado_a")
    else:
        qs = Denuncia.objects.filter(ciudadano=usuario).select_related("categoria")
    estado = request.GET.get("estado", "")
    if estado in Denuncia.Estado.values:
        qs = qs.filter(estado=estado)
    return render(request, "denuncias/listado.html", {
        "denuncias": qs[:100],
        "estados": Denuncia.Estado.choices,
        "estado_actual": estado,
    })


@login_required
def nueva(request):
    if request.user.rol != "CIUDADANO" or request.user.is_superuser:
        return HttpResponseForbidden("Solo los ciudadanos pueden registrar denuncias.")
    form = NuevaDenunciaForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            denuncia = form.save(commit=False)
            denuncia.ciudadano = request.user
            denuncia.estado = Denuncia.Estado.PENDIENTE
            denuncia.save()
            HistorialDenuncia.objects.create(
                denuncia=denuncia, usuario=request.user, accion="CREACION",
                detalle="Denuncia registrada con estado Pendiente.",
            )
        messages.success(request, f"Denuncia #{denuncia.pk} registrada correctamente.")
        return redirect("denuncias:detalle", pk=denuncia.pk)
    return render(request, "denuncias/nueva.html", {"form": form})


@login_required
def detalle(request, pk):
    usuario = request.user
    qs = Denuncia.objects.select_related("categoria", "ciudadano", "asignado_a")
    if not (usuario.es_funcionario or usuario.es_administrador):
        qs = qs.filter(ciudadano=usuario)
    denuncia = get_object_or_404(qs, pk=pk)
    return render(request, "denuncias/detalle.html", {"denuncia": denuncia})


@login_required
def gestionar(request, pk):
    if not request.user.es_funcionario:
        return HttpResponseForbidden("Solo los funcionarios municipales pueden gestionar denuncias.")
    denuncia = get_object_or_404(Denuncia, pk=pk)
    # Guardamos los valores originales ANTES de validar el ModelForm:
    # Django actualiza la instancia en memoria durante form.is_valid().
    estado_anterior = denuncia.estado
    asignado_anterior = denuncia.asignado_a_id
    form = GestionDenunciaForm(request.POST or None, instance=denuncia)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            denuncia = form.save()
            if estado_anterior != denuncia.estado:
                HistorialDenuncia.objects.create(
                    denuncia=denuncia, usuario=request.user, accion="CAMBIO_ESTADO",
                    detalle=f"{dict(Denuncia.Estado.choices)[estado_anterior]} → {denuncia.get_estado_display()}.",
                )
            if asignado_anterior != denuncia.asignado_a_id:
                HistorialDenuncia.objects.create(
                    denuncia=denuncia, usuario=request.user, accion="ASIGNACION",
                    detalle=f"Responsable: {denuncia.asignado_a or 'Sin asignar'}.",
                )
        messages.success(request, "Denuncia actualizada correctamente.")
        return redirect("denuncias:detalle", pk=denuncia.pk)
    return render(request, "denuncias/gestionar.html", {"form": form, "denuncia": denuncia})
