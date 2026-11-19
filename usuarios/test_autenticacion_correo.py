"""Pruebas de compatibilidad de cuentas y autenticación por correo."""
from django.contrib.auth import authenticate
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import RegistroCiudadanoForm
from .models import Usuario

CLAVE = 'ClaveSegura2026!'


class AutenticacionCorreoTest(TestCase):
    def setUp(self):
        self.existente = Usuario.objects.create_user(
            username='ciudadano_antiguo', email='ciudadano@ejemplo.com',
            password=CLAVE, rol=Usuario.Rol.CIUDADANO,
        )

    def test_registro_no_exige_nombre_de_usuario(self):
        form = RegistroCiudadanoForm()
        self.assertTrue(form.fields['username'].widget.is_hidden)
        resp = self.client.post(reverse('registro'), {
            'first_name': 'Ana', 'last_name': 'Perez',
            'email': 'ana@ejemplo.com', 'password1': CLAVE, 'password2': CLAVE,
            'rol': 'ADMINISTRADOR',
        })
        self.assertRedirects(resp, reverse('dashboard'))
        usuario = Usuario.objects.get(email='ana@ejemplo.com')
        self.assertTrue(usuario.username.startswith('ciud_'))
        self.assertEqual(usuario.rol, Usuario.Rol.CIUDADANO)
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)

    def test_ingreso_por_correo_existente(self):
        resp = self.client.post(reverse('login'), {
            'username': 'ciudadano@ejemplo.com', 'password': CLAVE,
        })
        self.assertRedirects(resp, reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.existente.pk)

    def test_ingreso_por_correo_no_distingue_mayusculas(self):
        usuario = authenticate(username='CIUDADANO@EJEMPLO.COM', password=CLAVE)
        self.assertEqual(usuario, self.existente)

    def test_conserva_acceso_por_usuario_interno(self):
        # Login tradicional, necesario para Django Admin y cuentas previas.
        self.assertEqual(authenticate(username='ciudadano_antiguo', password=CLAVE), self.existente)

    def test_no_permite_repetir_email_cambiando_mayusculas(self):
        resp = self.client.post(reverse('registro'), {
            'first_name': 'Ana', 'last_name': 'Perez',
            'email': 'CIUDADANO@EJEMPLO.COM', 'password1': CLAVE, 'password2': CLAVE,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 1)
        self.assertContains(resp, 'Ya existe una cuenta')

    def test_cuenta_inactiva_no_ingresa(self):
        self.existente.is_active = False
        self.existente.save(update_fields=['is_active'])
        resp = self.client.post(reverse('login'), {
            'username': self.existente.email, 'password': CLAVE,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_recuperacion_envia_enlace_de_uso_unico(self):
        respuesta = self.client.post(reverse('password_reset'), {'email': self.existente.email})
        self.assertRedirects(respuesta, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('restablecer-clave/', mail.outbox[0].body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_recuperacion_no_revela_si_cuenta_existe(self):
        respuesta = self.client.post(reverse('password_reset'), {'email': 'nadie@ejemplo.com'})
        self.assertRedirects(respuesta, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_login_exhibe_correo_y_enlace_recuperacion(self):
        resp = self.client.get(reverse('login'))
        self.assertContains(resp, 'Correo electrónico')
        self.assertContains(resp, reverse('password_reset'))
