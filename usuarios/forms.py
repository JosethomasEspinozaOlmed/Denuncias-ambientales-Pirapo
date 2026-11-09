from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

class RegistroCiudadanoForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("first_name", "last_name", "email"):
            self.fields[field].required = True

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.CIUDADANO  # Nunca aceptar el rol desde un formulario público.
        if commit:
            usuario.save()
        return usuario
