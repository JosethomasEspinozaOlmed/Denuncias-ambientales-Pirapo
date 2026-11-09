from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import RegistroCiudadanoForm
from .models import Usuario


def inicio(request):
    return render(request, "inicio.html")


def registro(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistroCiudadanoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, "Cuenta creada correctamente.")
        return redirect("dashboard")
    return render(request, "usuarios/registro.html", {"form": form})


@login_required
def dashboard(request):
    from denuncias.models import Denuncia
    usuario = request.user
    if usuario.es_administrador:
        resumen = {"total": Denuncia.objects.count(), "ciudadanos": Usuario.objects.filter(rol=Usuario.Rol.CIUDADANO).count()}
    elif usuario.es_funcionario:
        resumen = {"total": Denuncia.objects.count(), "pendientes": Denuncia.objects.filter(estado=Denuncia.Estado.PENDIENTE).count()}
    else:
        propias = Denuncia.objects.filter(ciudadano=usuario)
        resumen = {"total": propias.count(), "pendientes": propias.filter(estado=Denuncia.Estado.PENDIENTE).count()}
    return render(request, "usuarios/dashboard.html", {"resumen": resumen})
