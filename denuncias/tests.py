from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from usuarios.models import Usuario
from .models import Categoria, Denuncia, Evidencia, HistorialEstado, Ubicacion


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

    def crear_denuncia(self, ciudadano=None, descripcion="Basural", direccion="Pirapó", **kwargs):
        d = Denuncia.objects.create(
            ciudadano=ciudadano or self.ana,
            categoria=self.categoria, descripcion=descripcion, **kwargs,
        )
        Ubicacion.objects.create(denuncia=d, direccion=direccion)
        return d

    def test_ciudadano_crea_denuncia_sin_foto_con_ubicacion_manual(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(reverse("denuncias:nueva"), {
            "categoria": self.categoria.pk, "descripcion": "Basural en la vía pública",
            "direccion": "Barrio Centro, Pirapó",
        })
        denuncia = Denuncia.objects.get()
        self.assertRedirects(respuesta, reverse("denuncias:detalle", args=[denuncia.pk]))
        self.assertEqual(denuncia.estado, Denuncia.Estado.PENDIENTE)
        self.assertEqual(denuncia.ubicacion.direccion, "Barrio Centro, Pirapó")
        self.assertFalse(Evidencia.objects.filter(denuncia=denuncia).exists())
        self.assertEqual(denuncia.historial.count(), 1)
        self.assertEqual(denuncia.historial.first().estado_nuevo, Denuncia.Estado.PENDIENTE)

    def test_sin_ubicacion_no_se_guarda(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(reverse("denuncias:nueva"), {
            "categoria": self.categoria.pk, "descripcion": "Basura cerca del arroyo",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Denuncia.objects.count(), 0)
        self.assertEqual(Ubicacion.objects.count(), 0)

    def test_ubicacion_por_mapa_sin_direccion(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(reverse("denuncias:nueva"), {
            "categoria": self.categoria.pk, "descripcion": "Prueba con GPS",
            "latitud": "-26.850000", "longitud": "-55.530000",
        })
        self.assertEqual(respuesta.status_code, 302)
        ubicacion = Ubicacion.objects.get()
        self.assertEqual(str(ubicacion.latitud), '-26.850000')
        self.assertFalse(Evidencia.objects.exists())

    def test_una_sola_coordenada_rechazada(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(reverse("denuncias:nueva"), {
            "categoria": self.categoria.pk, "descripcion": "Prueba con GPS",
            "latitud": "-26.850000",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Denuncia.objects.count(), 0)

    def test_ciudadano_no_ve_denuncia_ajena(self):
        denuncia = self.crear_denuncia()
        self.client.force_login(self.otro)
        respuesta = self.client.get(reverse("denuncias:detalle", args=[denuncia.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_funcionario_puede_asignar_y_actualizar(self):
        denuncia = self.crear_denuncia()
        self.client.force_login(self.funcionario)
        respuesta = self.client.post(reverse("denuncias:gestionar", args=[denuncia.pk]), {
            "estado": Denuncia.Estado.EN_PROCESO, "asignado_a": self.funcionario.pk,
        })
        self.assertEqual(respuesta.status_code, 302)
        denuncia.refresh_from_db()
        self.assertEqual(denuncia.estado, Denuncia.Estado.EN_PROCESO)
        self.assertEqual(denuncia.asignado_a, self.funcionario)
        self.assertEqual(denuncia.historial.count(), 2)
        cambio = denuncia.historial.get(accion="CAMBIO_ESTADO")
        self.assertEqual(cambio.estado_anterior, Denuncia.Estado.PENDIENTE)
        self.assertEqual(cambio.estado_nuevo, Denuncia.Estado.EN_PROCESO)
        self.assertEqual(cambio.funcionario, self.funcionario)

    def test_administrador_no_asigna_ni_cambia_estados(self):
        denuncia = self.crear_denuncia()
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
            "categoria": self.categoria.pk, "descripcion": "Prueba", "direccion": "Pirapó",
        })
        self.assertEqual(respuesta.status_code, 403)

    def test_der_tiene_seis_entidades_principales(self):
        from usuarios.models import Usuario
        self.assertEqual(len([Usuario, Categoria, Denuncia, Ubicacion, Evidencia, HistorialEstado]), 6)
        self.assertEqual(Ubicacion._meta.get_field('denuncia').unique, True)
        self.assertEqual(Evidencia._meta.get_field('denuncia').unique, True)
        self.assertEqual(Denuncia._meta.get_field('creado').db_column, 'fecha_registro')


class FiltrosYReportesTest(TestCase):
    def setUp(self):
        self.ciudadano = Usuario.objects.create_user(
            username='ciudadana', password='Clave1234$', email='ciudadana@ejemplo.com',
        )
        self.funcionario = Usuario.objects.create_user(
            username='empleado', password='Clave1234$', email='empleado@ejemplo.com',
            rol=Usuario.Rol.FUNCIONARIO,
        )
        self.categoria = Categoria.objects.create(nombre='Quema de residuos')
        self.pendiente = self.crear_denuncia('Humo en el barrio', Denuncia.Estado.PENDIENTE)
        self.resuelta = self.crear_denuncia('Basural retirado', Denuncia.Estado.RESUELTO,
                                          asignado_a=self.funcionario)

    def crear_denuncia(self, descripcion, estado, **kwargs):
        denuncia = Denuncia.objects.create(
            ciudadano=self.ciudadano, categoria=self.categoria,
            descripcion=descripcion, estado=estado, **kwargs,
        )
        Ubicacion.objects.create(denuncia=denuncia, direccion='Pirapó')
        return denuncia

    def test_filtro_por_estado(self):
        self.client.force_login(self.funcionario)
        respuesta = self.client.get(reverse('denuncias:listado'), {'estado': 'RESUELTO'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['total_filtrado'], 1)
        self.assertContains(respuesta, 'Basural retirado')
        self.assertNotContains(respuesta, 'Humo en el barrio')

    def test_mis_asignaciones_solo_funcionario(self):
        self.client.force_login(self.funcionario)
        respuesta = self.client.get(reverse('denuncias:listado'), {'mias': '1'})
        self.assertEqual(respuesta.context['total_filtrado'], 1)
        self.assertContains(respuesta, 'Basural retirado')

    def test_filtro_por_direccion_separada(self):
        self.client.force_login(self.funcionario)
        respuesta = self.client.get(reverse('denuncias:listado'), {'q': 'Pirapó'})
        self.assertEqual(respuesta.context['total_filtrado'], 2)

    def test_csv_rechaza_ciudadano(self):
        self.client.force_login(self.ciudadano)
        respuesta = self.client.get(reverse('denuncias:exportar_csv'))
        self.assertEqual(respuesta.status_code, 403)

    def test_csv_exporta_solo_resultados_filtrados(self):
        self.client.force_login(self.funcionario)
        respuesta = self.client.get(reverse('denuncias:exportar_csv'), {'estado': 'RESUELTO'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('text/csv', respuesta['Content-Type'])
        contenido = respuesta.content.decode('utf-8-sig')
        self.assertIn('Basural retirado', contenido)
        self.assertNotIn('Humo en el barrio', contenido)

    def test_tablero_ciudadano_no_expone_otros_reportes(self):
        otro = Usuario.objects.create_user(
            username='vecino2', password='Clave1234$', email='vecino2@ejemplo.com'
        )
        denuncia = Denuncia.objects.create(
            ciudadano=otro, categoria=self.categoria,
            descripcion='Reporte de otro ciudadano',
        )
        Ubicacion.objects.create(denuncia=denuncia, direccion='Pirapó')
        self.client.force_login(self.ciudadano)
        respuesta = self.client.get(reverse('dashboard'))
        self.assertEqual(respuesta.context['resumen']['total'], 2)
        self.assertNotContains(respuesta, 'Reporte de otro ciudadano')
