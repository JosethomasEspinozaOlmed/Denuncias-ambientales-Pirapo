"""Formularios del panel municipal, separados del registro público."""
from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from .models import Usuario
from denuncias.models import Categoria


class _UsuarioFormMixin:
    def __init__(self, *args, allowed_roles=None, **kwargs):
        super().__init__(*args, **kwargs)
        roles = allowed_roles or (Usuario.Rol.CIUDADANO, Usuario.Rol.FUNCIONARIO)
        self.fields['rol'].choices = [
            (value, label) for value, label in Usuario.Rol.choices if value in roles
        ]
        for campo in ('first_name', 'last_name', 'email'):
            self.fields[campo].required = True
        for campo, field in self.fields.items():
            field.widget.attrs['class'] = (
                'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            )
            if campo == 'email':
                field.widget.attrs['autocomplete'] = 'email'

    def clean_email(self):
        correo = self.cleaned_data['email'].strip().lower()
        usuarios = Usuario.objects.filter(email__iexact=correo)
        if self.instance.pk:
            usuarios = usuarios.exclude(pk=self.instance.pk)
        if usuarios.exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo electrónico.')
        return correo


class UsuarioAltaForm(_UsuarioFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'rol')
        labels = {
            'username': 'Nombre de usuario', 'first_name': 'Nombre',
            'last_name': 'Apellido', 'email': 'Correo electrónico', 'rol': 'Rol',
        }


class UsuarioEdicionForm(_UsuarioFormMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'rol')
        labels = {
            'username': 'Nombre de usuario', 'first_name': 'Nombre',
            'last_name': 'Apellido', 'email': 'Correo electrónico', 'rol': 'Rol',
        }


class CategoriaMunicipalForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ('nombre', 'descripcion')
        labels = {'nombre': 'Nombre de la categoría', 'descripcion': 'Descripción (opcional)'}
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': 255}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        existentes = Categoria.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise forms.ValidationError('Ya existe una categoría con ese nombre.')
        return nombre


class CambiarClaveForm(SetPasswordForm):
    """Se usa SetPasswordForm para aplicar los validadores de contraseñas de Django."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ('new_password1', 'new_password2'):
            self.fields[campo].widget.attrs['class'] = 'form-control'
