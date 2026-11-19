"""Pruebas de permisos y CRUD de administración municipal."""
from django.test import TestCase
from django.urls import reverse

from denuncias.models import Categoria, Denuncia, Ubicacion
from .models import Usuario


CLAVE = 'ClaveDePrueba123!'


class PanelMunicipalTest(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='adminlocal', email='admin@prueba.com', password=CLAVE,
            rol=Usuario.Rol.ADMINISTRADOR,
        )
        self.ciudadano = Usuario.objects.create_user(
            username='vecino', email='vecino@prueba.com', password=CLAVE,
            rol=Usuario.Rol.CIUDADANO,
        )
        self.funcionario = Usuario.objects.create_user(
            username='funcionario', email='funcionario@prueba.com', password=CLAVE,
            rol=Usuario.Rol.FUNCIONARIO,
        )
        self.superusuario = Usuario.objects.create_superuser(
            username='superjefe', email='super@prueba.com', password=CLAVE,
        )
        self.categoria = Categoria.objects.create(nombre='Residuos')

    def test_solo_administrador_ve_panel(self):
        url = reverse('administracion:panel')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.ciudadano)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.funcionario)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_ciudadano_no_puede_crear_funcionario(self):
        self.client.force_login(self.ciudadano)
        resp = self.client.post(reverse('administracion:usuario_nuevo'), {
            'username': 'intruso', 'first_name': 'A', 'last_name': 'B',
            'email': 'intruso@prueba.com', 'rol': 'FUNCIONARIO',
            'password1': CLAVE, 'password2': CLAVE,
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Usuario.objects.filter(username='intruso').exists())

    def test_admin_crea_funcionario_sin_staff_ni_superuser(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('administracion:usuario_nuevo'), {
            'username': 'operario', 'first_name': 'Juan', 'last_name': 'Perez',
            'email': 'OPERARIO@prueba.com', 'rol': 'FUNCIONARIO',
            'password1': CLAVE, 'password2': CLAVE,
        })
        self.assertRedirects(resp, reverse('administracion:usuarios'))
        u = Usuario.objects.get(username='operario')
        self.assertEqual(u.rol, Usuario.Rol.FUNCIONARIO)
        self.assertEqual(u.email, 'operario@prueba.com')
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertTrue(u.check_password(CLAVE))

    def test_admin_no_puede_crear_administrador(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('administracion:usuario_nuevo'), {
            'username': 'nuevo_admin', 'first_name': 'A', 'last_name': 'B',
            'email': 'nuevo_admin@prueba.com', 'rol': 'ADMINISTRADOR',
            'password1': CLAVE, 'password2': CLAVE,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Usuario.objects.filter(username='nuevo_admin').exists())

    def test_admin_edita_usuario(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('administracion:usuario_editar', args=[self.ciudadano.pk]), {
            'username': 'vecino', 'first_name': 'Ana', 'last_name': 'Lopez',
            'email': 'vecino@prueba.com', 'rol': 'CIUDADANO',
            'is_superuser': 'on', 'is_staff': 'on',
        })
        self.assertRedirects(resp, reverse('administracion:usuarios'))
        self.ciudadano.refresh_from_db()
        self.assertEqual(self.ciudadano.first_name, 'Ana')
        self.assertFalse(self.ciudadano.is_superuser)
        self.assertFalse(self.ciudadano.is_staff)

    def test_admin_no_puede_editare_a_si_mismo(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('administracion:usuario_editar', args=[self.admin.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_admin_no_modifica_superusuario(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('administracion:usuario_estado', args=[self.superusuario.pk]))
        self.assertEqual(resp.status_code, 403)
        self.superusuario.refresh_from_db()
        self.assertTrue(self.superusuario.is_active)

    def test_desactivar_requiere_post(self):
        self.client.force_login(self.admin)
        url = reverse('administracion:usuario_estado', args=[self.ciudadano.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.ciudadano.refresh_from_db()
        self.assertFalse(self.ciudadano.is_active)

    def test_funcionario_con_casos_abiertos_no_puede_desactivarse(self):
        d = Denuncia.objects.create(ciudadano=self.ciudadano, categoria=self.categoria,
                                    descripcion='Basura sin recolectar', asignado_a=self.funcionario)
        Ubicacion.objects.create(denuncia=d, direccion='Pirapó')
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('administracion:usuario_estado', args=[self.funcionario.pk]))
        self.assertRedirects(resp, reverse('administracion:usuarios'))
        self.funcionario.refresh_from_db()
        self.assertTrue(self.funcionario.is_active)

    def test_admin_restaurar_contrasena_de_ciudadano(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('administracion:usuario_clave', args=[self.ciudadano.pk]), {
            'new_password1': 'NuevaClaveSegura123$', 'new_password2': 'NuevaClaveSegura123$',
        })
        self.assertRedirects(resp, reverse('administracion:usuarios'))
        self.ciudadano.refresh_from_db()
        self.assertTrue(self.ciudadano.check_password('NuevaClaveSegura123$'))

    def test_admin_crea_edita_y_desactiva_categoria(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('administracion:categoria_nueva'), {
            'nombre': 'Quema de basura', 'descripcion': 'Residuos en combustión',
        })
        self.assertRedirects(resp, reverse('administracion:categorias'))
        cat = Categoria.objects.get(nombre='Quema de basura')
        resp = self.client.post(reverse('administracion:categoria_editar', args=[cat.pk]), {
            'nombre': 'Quema de residuos', 'descripcion': 'Quema no controlada',
        })
        self.assertRedirects(resp, reverse('administracion:categorias'))
        resp = self.client.post(reverse('administracion:categoria_estado', args=[cat.pk]))
        self.assertRedirects(resp, reverse('administracion:categorias'))
        cat.refresh_from_db()
        self.assertFalse(cat.activa)
        self.assertEqual(cat.nombre, 'Quema de residuos')

    def test_categoria_inactiva_no_se_ofrece_en_denuncias(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('administracion:categoria_estado', args=[self.categoria.pk]))
        from denuncias.forms import NuevaDenunciaForm
        formulario = NuevaDenunciaForm()
        self.assertNotIn(self.categoria, list(formulario.fields['categoria'].queryset))

    def test_correo_duplicado_no_se_acepta(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('administracion:usuario_nuevo'), {
            'username': 'vecino2', 'first_name': 'V', 'last_name': 'D',
            'email': 'VECINO@PRUEBA.COM', 'rol': 'CIUDADANO',
            'password1': CLAVE, 'password2': CLAVE,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Usuario.objects.filter(username='vecino2').exists())
