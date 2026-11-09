from django.test import TestCase
from django.urls import reverse
from .models import Usuario

class RegistroTest(TestCase):
    def test_registro_siempre_crea_ciudadano(self):
        respuesta = self.client.post(reverse("registro"), {
            "username": "vecina", "first_name": "Ana", "last_name": "Benitez",
            "email": "ana@example.com", "password1": "UnaClaveSegura123$",
            "password2": "UnaClaveSegura123$", "rol": "ADMINISTRADOR",
        })
        self.assertRedirects(respuesta, reverse("dashboard"))
        self.assertEqual(Usuario.objects.get(username="vecina").rol, Usuario.Rol.CIUDADANO)

    def test_login_requerido_para_panel(self):
        respuesta = self.client.get(reverse("dashboard"))
        self.assertEqual(respuesta.status_code, 302)
