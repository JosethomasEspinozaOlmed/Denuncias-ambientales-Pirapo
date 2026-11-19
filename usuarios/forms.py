"""Registro público por correo conservando el nombre de usuario interno de Django."""
from uuid import uuid4

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario


class RegistroCiudadanoForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        # username queda oculto: permite los registros anteriores, pero ya no se pide en pantalla.
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['username'].widget = forms.HiddenInput()
        self.fields['username'].help_text = ''
        for campo in ('first_name', 'last_name', 'email'):
            self.fields[campo].required = True
            self.fields[campo].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs.update({'autocomplete': 'email', 'placeholder': 'ejemplo@correo.com'})
        self.fields['first_name'].widget.attrs['autocomplete'] = 'given-name'
        self.fields['last_name'].widget.attrs['autocomplete'] = 'family-name'
        for campo in ('password1', 'password2'):
            self.fields[campo].widget.attrs.update({'class': 'form-control', 'autocomplete': 'new-password'})

    def clean_username(self):
        # Mantener compatibilidad con las pruebas/registros anteriores que envían username.
        usuario = (self.cleaned_data.get('username') or '').strip()
        if usuario:
            if Usuario.objects.filter(username__iexact=usuario).exists():
                raise forms.ValidationError('Ese identificador ya está en uso.')
            return usuario
        for _ in range(10):
            generado = 'ciud_' + uuid4().hex[:20]
            if not Usuario.objects.filter(username=generado).exists():
                return generado
        raise forms.ValidationError('No se pudo generar el identificador; intentá otra vez.')

    def clean_email(self):
        correo = self.cleaned_data['email'].strip().lower()
        if Usuario.objects.filter(email__iexact=correo).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo electrónico.')
        return correo

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.CIUDADANO
        usuario.is_staff = False
        usuario.is_superuser = False
        if commit:
            usuario.save()
        return usuario
