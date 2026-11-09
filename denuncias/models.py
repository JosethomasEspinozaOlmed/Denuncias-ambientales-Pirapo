from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class Denuncia(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        RESUELTO = "RESUELTO", "Resuelto"

    ciudadano = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="denuncias")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="denuncias")
    titulo = models.CharField(max_length=150, blank=True, verbose_name="Título breve (opcional)")
    descripcion = models.TextField(verbose_name="Descripción del problema")
    direccion = models.CharField(max_length=250, blank=True, verbose_name="Ubicación o dirección de referencia")
    latitud = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    foto = models.ImageField(
        upload_to="denuncias/%Y/%m/", blank=True, null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
        verbose_name="Fotografía (opcional)",
    )
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="denuncias_asignadas", limit_choices_to={"rol": "FUNCIONARIO"},
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "Denuncia"
        verbose_name_plural = "Denuncias"

    def clean(self):
        super().clean()
        tiene_lat = self.latitud is not None
        tiene_lon = self.longitud is not None
        if tiene_lat != tiene_lon:
            raise ValidationError("La latitud y la longitud deben indicarse juntas.")
        if not self.direccion.strip() and not (tiene_lat and tiene_lon):
            raise ValidationError("Indica una ubicación: dirección de referencia o punto en el mapa.")
        if self.asignado_a_id and self.asignado_a.rol != "FUNCIONARIO":
            raise ValidationError("Solo puede asignarse a funcionarios municipales.")

    @property
    def nombre_corto(self):
        return self.titulo or self.descripcion[:65]

    def __str__(self):
        return f"#{self.pk or 'nuevo'} - {self.nombre_corto}"


class HistorialDenuncia(models.Model):
    denuncia = models.ForeignKey(Denuncia, on_delete=models.CASCADE, related_name="historial")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    accion = models.CharField(max_length=30)
    detalle = models.CharField(max_length=400)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Movimiento de denuncia"
        verbose_name_plural = "Historial de denuncias"

    def __str__(self):
        return f"Denuncia #{self.denuncia_id}: {self.accion}"
