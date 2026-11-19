"""Pruebas adicionales para el formulario ciudadano sin título breve."""
from django.test import TestCase
from django.urls import reverse
from usuarios.models import Usuario
from .models import Categoria, Denuncia, Evidencia, Ubicacion


class FormularioSimplificadoTest(TestCase):
    def setUp(self):
        self.ciudadano = Usuario.objects.create_user(
            username="ciudadano_simplificado", email="ciudadano.simplificado@example.com",
            password="ClavePruebaSeguro123!",
        )
        self.categoria = Categoria.objects.create(nombre="Residuos de prueba")
        self.client.force_login(self.ciudadano)

    def test_formulario_no_muestra_ni_exige_titulo(self):
        respuesta = self.client.get(reverse("denuncias:nueva"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn("titulo", respuesta.context["form"].fields)
        self.assertNotContains(respuesta, 'name="titulo"')
        self.assertContains(respuesta, 'name="categoria"')
        self.assertContains(respuesta, 'name="descripcion"')

    def test_registra_sin_titulo_ni_foto_con_ubicacion(self):
        respuesta = self.client.post(reverse("denuncias:nueva"), {
            "categoria": self.categoria.pk,
            "descripcion": "Se observan residuos acumulados cerca del camino.",
            "direccion": "Zona urbana de Pirapó",
            # Aunque un cliente envíe un título, el formulario no debe guardarlo.
            "titulo": "Este dato no debe guardarse",
        })
        self.assertEqual(respuesta.status_code, 302)
        denuncia = Denuncia.objects.get()
        self.assertEqual(denuncia.titulo, "")
        self.assertEqual(denuncia.estado, Denuncia.Estado.PENDIENTE)
        self.assertEqual(denuncia.categoria, self.categoria)
        self.assertEqual(denuncia.ubicacion.direccion, "Zona urbana de Pirapó")
        self.assertFalse(Evidencia.objects.filter(denuncia=denuncia).exists())

    def test_sin_ubicacion_no_registra_denuncia(self):
        respuesta = self.client.post(reverse("denuncias:nueva"), {
            "categoria": self.categoria.pk,
            "descripcion": "Quema de residuos en terreno baldío",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Denuncia.objects.count(), 0)
        self.assertEqual(Ubicacion.objects.count(), 0)
