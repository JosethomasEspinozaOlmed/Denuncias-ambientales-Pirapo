from django import forms
from usuarios.models import Usuario
from .models import Categoria, Denuncia


class NuevaDenunciaForm(forms.ModelForm):
    class Meta:
        model = Denuncia
        fields = ("titulo", "categoria", "descripcion", "direccion", "latitud", "longitud", "foto")
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe el problema ambiental"}),
            "latitud": forms.HiddenInput(attrs={"id": "id_latitud"}),
            "longitud": forms.HiddenInput(attrs={"id": "id_longitud"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = Categoria.objects.filter(activa=True)
        self.fields["categoria"].empty_label = "Selecciona una categoría"
        self.fields["direccion"].help_text = "Obligatoria si no marcas un punto en el mapa."
        self.fields["foto"].help_text = "Opcional: JPG, PNG o WebP (máximo 5 MB)."

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and foto.size > 5 * 1024 * 1024:
            raise forms.ValidationError("La fotografía no puede superar 5 MB.")
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
