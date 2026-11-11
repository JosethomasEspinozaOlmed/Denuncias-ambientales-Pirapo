from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from usuarios.models import Usuario
from .models import Categoria, Denuncia


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
        fields = ("titulo", "categoria", "descripcion", "direccion", "latitud", "longitud", "foto")
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
