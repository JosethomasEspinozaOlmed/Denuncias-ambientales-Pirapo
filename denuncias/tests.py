from django.test import TestCase
from django.urls import reverse
from usuarios.models import Usuario
from .models import Categoria, Denuncia

class DenunciasTest(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user(username="ana", password="Clave1234$", email="ana@test.com")
        self.otro = Usuario.objects.create_user(username="pedro", password="Clave1234$", email="pedro@test.com")
        self.funcionario = Usuario.objects.create_user(
            username="funcionario", password="Clave1234$", email="func@test.com", rol=Usuario.Rol.FUNCIONARIO,
        )
        self.admin = Usuario.objects.create_user(
            username="adminweb", password="Clave1234$", email="admin@test.com", rol=Usuario.Rol.ADMINISTRADOR,
        )
        self.categoria = Categoria.objects.create(nombre="Residuos y basurales")

    def test_ciudadano_crea_denuncia_sin_foto_con_ubicacion_manual(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(reverse("denuncias:nueva"), {
            "categoria": self.categoria.pk, "descripcion": "Basural en la vía pública",
            "direccion": "Barrio Centro, Pirapó",
        })
        denuncia = Denuncia.objects.get()
        self.assertRedirects(respuesta, reverse("denuncias:detalle", args=[denuncia.pk]))
        self.assertEqual(denuncia.estado, Denuncia.Estado.PENDIENTE)
        self.assertFalse(bool(denuncia.foto))

    def test_sin_ubicacion_no_se_guarda(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(reverse("denuncias:nueva"), {
            "categoria": self.categoria.pk, "descripcion": "Basura cerca del arroyo",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Denuncia.objects.count(), 0)

    def test_ciudadano_no_ve_denuncia_ajena(self):
        denuncia = Denuncia.objects.create(
            ciudadano=self.ana, categoria=self.categoria,
            descripcion="Basural", direccion="Pirapó",
        )
        self.client.force_login(self.otro)
        respuesta = self.client.get(reverse("denuncias:detalle", args=[denuncia.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_funcionario_puede_asignar_y_actualizar(self):
        denuncia = Denuncia.objects.create(
            ciudadano=self.ana, categoria=self.categoria,
            descripcion="Basural", direccion="Pirapó",
        )
        self.client.force_login(self.funcionario)
        respuesta = self.client.post(reverse("denuncias:gestionar", args=[denuncia.pk]), {
            "estado": Denuncia.Estado.EN_PROCESO, "asignado_a": self.funcionario.pk,
        })
        self.assertEqual(respuesta.status_code, 302)
        denuncia.refresh_from_db()
        self.assertEqual(denuncia.estado, Denuncia.Estado.EN_PROCESO)
        self.assertEqual(denuncia.asignado_a, self.funcionario)
        self.assertEqual(denuncia.historial.count(), 2)

    def test_administrador_no_asigna_ni_cambia_estados(self):
        denuncia = Denuncia.objects.create(
            ciudadano=self.ana, categoria=self.categoria,
            descripcion="Basural", direccion="Pirapó",
        )
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("denuncias:gestionar", args=[denuncia.pk]), {
            "estado": Denuncia.Estado.RESUELTO,
        })
        self.assertEqual(respuesta.status_code, 403)
        denuncia.refresh_from_db()
        self.assertEqual(denuncia.estado, Denuncia.Estado.PENDIENTE)

    def test_funcionario_no_puede_publicar_denuncias_como_ciudadano(self):
        self.client.force_login(self.funcionario)
        respuesta = self.client.post(reverse("denuncias:nueva"), {
            "categoria": self.categoria.pk, "descripcion": "Prueba",
            "direccion": "Pirapó",
        })
        self.assertEqual(respuesta.status_code, 403)
