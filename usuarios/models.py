from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        CIUDADANO = "CIUDADANO", "Ciudadano"
        FUNCIONARIO = "FUNCIONARIO", "Funcionario municipal"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    email = models.EmailField("correo electrónico", unique=True)
    rol = models.CharField(max_length=15, choices=Rol.choices, default=Rol.CIUDADANO)

    @property
    def es_funcionario(self):
        return self.is_authenticated and self.is_active and self.rol == self.Rol.FUNCIONARIO

    @property
    def es_administrador(self):
        return self.is_authenticated and self.is_active and (self.rol == self.Rol.ADMINISTRADOR or self.is_superuser)

    def __str__(self):
        return self.get_full_name() or self.username
