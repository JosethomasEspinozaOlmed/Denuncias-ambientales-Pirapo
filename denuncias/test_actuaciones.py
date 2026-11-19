"""Pruebas de verificación municipal. Conservar tests.py existente."""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from usuarios.models import Usuario

from .models import ActuacionMunicipal, Categoria, Denuncia, HistorialEstado, Ubicacion


class ActuacionMunicipalTest(TestCase):
    def setUp(self):
        self.ciudadano = Usuario.objects.create_user(
            username="vecino_prueba", email="vecino-actuaciones@example.com", password="Prueba12345!",
        )
        self.funcionario = Usuario.objects.create_user(
            username="funcionario_prueba", email="funcionario-actuaciones@example.com",
            password="Prueba12345!", rol=Usuario.Rol.FUNCIONARIO,
        )
        self.admin = Usuario.objects.create_user(
            username="admin_prueba", email="admin-actuaciones@example.com",
            password="Prueba12345!", rol=Usuario.Rol.ADMINISTRADOR,
        )
        self.categoria = Categoria.objects.create(nombre="Residuos - prueba actuación")
        self.denuncia = Denuncia.objects.create(
            ciudadano=self.ciudadano, categoria=self.categoria,
            descripcion="Basural frente al camino vecinal",
        )
        Ubicacion.objects.create(denuncia=self.denuncia, direccion="Pirapó")
        self.url = reverse("denuncias:registrar_actuacion", args=[self.denuncia.pk])

    def datos(self, **ajustes):
        datos = {
            "fecha_verificacion": timezone.localdate().isoformat(),
            "lugar_verificado": "Camino vecinal - Pirapó",
            "resultado": ActuacionMunicipal.Resultado.CONFIRMADA,
            "hechos_constatados": "Se encontraron residuos acumulados.",
            "medidas_adoptadas": "Se informó al área de limpieza.",
            "observaciones": "No había personas en el sitio.",
            "nuevo_estado": Denuncia.Estado.EN_PROCESO,
        }
        datos.update(ajustes)
        return datos

    def test_funcionario_registra_actuacion_cambia_estado_y_conserva_historial(self):
        self.client.force_login(self.funcionario)
        respuesta = self.client.post(self.url, self.datos())
        self.assertRedirects(respuesta, reverse("denuncias:detalle", args=[self.denuncia.pk]))
        self.denuncia.refresh_from_db()
        self.assertEqual(self.denuncia.estado, Denuncia.Estado.EN_PROCESO)
        self.assertEqual(self.denuncia.actuaciones.count(), 1)
        actuacion = self.denuncia.actuaciones.get()
        self.assertEqual(actuacion.funcionario, self.funcionario)
        self.assertEqual(actuacion.lugar_verificado, "Camino vecinal - Pirapó")
        self.assertTrue(HistorialEstado.objects.filter(denuncia=self.denuncia, accion="VERIFICACION").exists())
        self.assertTrue(HistorialEstado.objects.filter(denuncia=self.denuncia, accion="CAMBIO_ESTADO").exists())

    def test_se_pueden_registrar_varias_visitas_sin_perder_las_anteriores(self):
        self.client.force_login(self.funcionario)
        self.client.post(self.url, self.datos(nuevo_estado=""))
        self.client.post(self.url, self.datos(
            hechos_constatados="Se retiraron los residuos.",
            resultado=ActuacionMunicipal.Resultado.NO_CONSTATADA,
            nuevo_estado="",
        ))
        self.assertEqual(self.denuncia.actuaciones.count(), 2)
        self.denuncia.refresh_from_db()
        self.assertEqual(self.denuncia.estado, Denuncia.Estado.PENDIENTE)

    def test_ciudadano_no_registra_verificacion(self):
        self.client.force_login(self.ciudadano)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, self.datos()).status_code, 403)
        self.assertFalse(ActuacionMunicipal.objects.exists())

    def test_administrador_no_registra_verificacion(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(self.url, self.datos()).status_code, 403)
        self.assertFalse(ActuacionMunicipal.objects.exists())

    def test_no_se_guarda_sin_lugar_o_hechos(self):
        self.client.force_login(self.funcionario)
        respuesta = self.client.post(self.url, self.datos(lugar_verificado="", hechos_constatados=""))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(ActuacionMunicipal.objects.exists())
        self.denuncia.refresh_from_db()
        self.assertEqual(self.denuncia.estado, Denuncia.Estado.PENDIENTE)

    def test_no_admite_fecha_de_verificacion_futura(self):
        self.client.force_login(self.funcionario)
        futuro = (timezone.localdate() + timedelta(days=2)).isoformat()
        respuesta = self.client.post(self.url, self.datos(fecha_verificacion=futuro))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(ActuacionMunicipal.objects.exists())

    def test_ciudadano_no_ve_observaciones_internas(self):
        self.client.force_login(self.funcionario)
        self.client.post(self.url, self.datos(observaciones="Detalle interno de prueba ABC-321"))
        self.client.force_login(self.ciudadano)
        respuesta = self.client.get(reverse("denuncias:detalle", args=[self.denuncia.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, "Detalle interno de prueba ABC-321")
