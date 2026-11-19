from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from usuarios.models import Usuario
from .models import ActuacionMunicipal, Categoria, Denuncia


class NuevaDenunciaForm(forms.ModelForm):
    # Ubicación y foto pertenecen a sus propias tablas, no a Denuncia.
    direccion = forms.CharField(max_length=255, required=False, label="Ubicación o dirección de referencia")
    latitud = forms.DecimalField(
        max_digits=9, decimal_places=6, required=False,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        widget=forms.HiddenInput(attrs={"id": "id_latitud"}),
    )
    longitud = forms.DecimalField(
        max_digits=9, decimal_places=6, required=False,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        widget=forms.HiddenInput(attrs={"id": "id_longitud"}),
    )
    foto = forms.ImageField(
        required=False, label="Fotografía (opcional)",
        help_text="Opcional: JPG, PNG o WebP (máximo 5 MB).",
    )

    class Meta:
        model = Denuncia
        fields = ("categoria", "descripcion", "direccion", "latitud", "longitud", "foto")
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe el problema ambiental"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = Categoria.objects.filter(activa=True)
        self.fields["categoria"].empty_label = "Selecciona una categoría"
        self.fields["direccion"].help_text = "Obligatoria si no marcás un punto en el mapa."

    def clean(self):
        datos = super().clean()
        lat, lon = datos.get("latitud"), datos.get("longitud")
        if (lat is None) != (lon is None):
            raise forms.ValidationError("La latitud y la longitud deben indicarse juntas.")
        if not (datos.get("direccion") or "").strip() and not (lat is not None and lon is not None):
            raise forms.ValidationError("Indicá la ubicación por dirección o marcando un punto en el mapa.")
        return datos

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and foto.size > 5 * 1024 * 1024:
            raise forms.ValidationError("La fotografía no puede superar 5 MB.")
        if foto and foto.name.rsplit(".", 1)[-1].lower() not in ("jpg", "jpeg", "png", "webp"):
            raise forms.ValidationError("Solo se permiten imágenes JPG, PNG o WebP.")
        return foto


class GestionDenunciaForm(forms.ModelForm):
    class Meta:
        model = Denuncia
        fields = ("asignado_a", "estado")
        labels = {"asignado_a": "Funcionario responsable", "estado": "Estado"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asignado_a"].queryset = Usuario.objects.filter(
            rol=Usuario.Rol.FUNCIONARIO, is_active=True,
        ).order_by("first_name", "last_name", "username")
        self.fields["asignado_a"].required = False
        self.fields["asignado_a"].empty_label = "Sin asignar"

class ActuacionMunicipalForm(forms.ModelForm):
    """Formulario interno para constatar hechos y documentar medidas municipales."""

    # Campo auxiliar: cambia el estado actual, pero no pertenece a la tabla ActuacionMunicipal.
    nuevo_estado = forms.ChoiceField(
        label="Actualizar estado de la denuncia",
        choices=[("", "Conservar estado actual")] + list(Denuncia.Estado.choices),
        required=False,
    )

    class Meta:
        model = ActuacionMunicipal
        fields = (
            "fecha_verificacion", "lugar_verificado", "resultado",
            "hechos_constatados", "medidas_adoptadas",
            "observaciones", "proxima_verificacion",
        )
        labels = {
            "fecha_verificacion": "Fecha de verificación",
            "lugar_verificado": "Lugar verificado",
            "resultado": "Resultado de la verificación",
            "hechos_constatados": "Hechos constatados",
            "medidas_adoptadas": "Medidas adoptadas (si corresponde)",
            "observaciones": "Observaciones adicionales",
            "proxima_verificacion": "Próxima verificación (opcional)",
        }
        widgets = {
            "fecha_verificacion": forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
            "lugar_verificado": forms.TextInput(attrs={"class": "form-control", "placeholder": "Dirección o referencia del lugar visitado"}),
            "resultado": forms.Select(attrs={"class": "form-select"}),
            "hechos_constatados": forms.Textarea(attrs={"rows": 4, "class": "form-control", "placeholder": "Describí lo verificado en el lugar"}),
            "medidas_adoptadas": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "proxima_verificacion": forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nuevo_estado"].widget.attrs["class"] = "form-select"
        self.fields["lugar_verificado"].strip = True
        self.fields["hechos_constatados"].strip = True
        # Los campos DateField pueden recibir una cadena ISO al enviar el formulario.

    def clean(self):
        datos = super().clean()
        from django.utils import timezone
        fecha = datos.get("fecha_verificacion")
        proxima = datos.get("proxima_verificacion")
        if fecha and fecha > timezone.localdate():
            self.add_error("fecha_verificacion", "La verificación no puede tener fecha futura.")
        if fecha and proxima and proxima <= fecha:
            self.add_error("proxima_verificacion", "La próxima visita debe ser posterior a la verificación.")
        return datos
