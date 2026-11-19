"""Modelos del DER académico de Pirapó: Usuario, Categoria, Denuncia,
Ubicacion, Evidencia e HistorialEstado.

La entidad Usuario se encuentra en la app `usuarios` y conserva el modelo
AbstractUser de Django para evitar romper la autenticación existente.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models


class Categoria(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="id_categoria")
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    activa = models.BooleanField(default=True, db_column="activo")

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

    id = models.BigAutoField(primary_key=True, db_column="id_denuncia")
    ciudadano = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="denuncias", db_column="id_usuario",
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT,
        related_name="denuncias", db_column="id_categoria",
    )
    # Título y responsable son extensiones funcionales del DER: RF de asignación.
    titulo = models.CharField(max_length=150, blank=True, verbose_name="Título breve (opcional)")
    descripcion = models.TextField(verbose_name="Descripción del problema")
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="denuncias_asignadas", limit_choices_to={"rol": "FUNCIONARIO"},
    )
    creado = models.DateTimeField(auto_now_add=True, db_column="fecha_registro")
    actualizado = models.DateTimeField(auto_now=True, db_column="fecha_actualizacion")

    class Meta:
        ordering = ["-creado"]
        verbose_name = "Denuncia"
        verbose_name_plural = "Denuncias"

    def clean(self):
        super().clean()
        if self.asignado_a_id and self.asignado_a.rol != "FUNCIONARIO":
            raise ValidationError("Solo puede asignarse a funcionarios municipales.")

    @property
    def direccion(self):
        ubicacion = getattr(self, "ubicacion", None)
        return ubicacion.direccion if ubicacion else ""

    @property
    def latitud(self):
        ubicacion = getattr(self, "ubicacion", None)
        return ubicacion.latitud if ubicacion else None

    @property
    def longitud(self):
        ubicacion = getattr(self, "ubicacion", None)
        return ubicacion.longitud if ubicacion else None

    @property
    def foto(self):
        evidencia = getattr(self, "evidencia", None)
        return evidencia.archivo if evidencia else None

    @property
    def nombre_corto(self):
        return self.titulo or self.descripcion[:65]

    def __str__(self):
        return f"#{self.pk or 'nuevo'} - {self.nombre_corto}"


class Ubicacion(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="id_ubicacion")
    denuncia = models.OneToOneField(
        Denuncia, on_delete=models.CASCADE,
        related_name="ubicacion", db_column="id_denuncia",
    )
    direccion = models.CharField(max_length=255, blank=True)
    latitud = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"

    def clean(self):
        super().clean()
        tiene_lat = self.latitud is not None
        tiene_lon = self.longitud is not None
        if tiene_lat != tiene_lon:
            raise ValidationError("La latitud y la longitud deben indicarse juntas.")
        if not (self.direccion or "").strip() and not (tiene_lat and tiene_lon):
            raise ValidationError("La ubicación es obligatoria: dirección o coordenadas.")

    def __str__(self):
        return self.direccion or f"{self.latitud}, {self.longitud}"


class Evidencia(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="id_evidencia")
    denuncia = models.OneToOneField(
        Denuncia, on_delete=models.CASCADE,
        related_name="evidencia", db_column="id_denuncia",
    )
    archivo = models.ImageField(
        upload_to="denuncias/%Y/%m/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    fecha_carga = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evidencia"
        verbose_name_plural = "Evidencias"

    def __str__(self):
        return f"Fotografía de la denuncia #{self.denuncia_id}"


class HistorialEstado(models.Model):
    """Estado y auditoría: también conserva los eventos previos de creación/asignación.

    `funcionario` se deja opcional para los eventos de creación ciudadana ya existentes;
    cada CAMBIO_ESTADO nuevo registra siempre al funcionario responsable.
    """
    id = models.BigAutoField(primary_key=True, db_column="id_historial")
    denuncia = models.ForeignKey(
        Denuncia, on_delete=models.CASCADE, related_name="historial", db_column="id_denuncia",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="historial_como_actor",
    )
    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        blank=True, null=True, related_name="historial_como_funcionario",
        db_column="id_funcionario",
    )
    accion = models.CharField(max_length=30)
    estado_anterior = models.CharField(max_length=20, blank=True, default="")
    estado_nuevo = models.CharField(max_length=20, blank=True, default="")
    observacion = models.TextField(blank=True, default="")
    fecha = models.DateTimeField(auto_now_add=True, db_column="fecha_cambio")

    class Meta:
        db_table = "denuncias_historial_estado"
        ordering = ["-fecha", "-pk"]
        verbose_name = "Movimiento de denuncia"
        verbose_name_plural = "Historial de denuncias"

    @property
    def detalle(self):
        """Compatibilidad con plantillas anteriores (incluida la Etapa 3)."""
        return self.observacion

    def __str__(self):
        return f"Denuncia #{self.denuncia_id}: {self.accion}"

class ActuacionMunicipal(models.Model):
    """Constancia interna de una visita/verificación de una denuncia ambiental.

    No es una denuncia judicial ni un acta con efecto legal automático.
    La actuación no sustituye el historial de cambios de estado.
    """

    class Resultado(models.TextChoices):
        CONFIRMADA = "CONFIRMADA", "Problemática confirmada"
        NO_CONSTATADA = "NO_CONSTATADA", "Problemática no constatada"
        SEGUIMIENTO = "REQUIERE_SEGUIMIENTO", "Requiere seguimiento"

    denuncia = models.ForeignKey(
        Denuncia, on_delete=models.CASCADE, related_name="actuaciones",
    )
    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="actuaciones_municipales",
        limit_choices_to={"rol": "FUNCIONARIO"},
    )
    fecha_verificacion = models.DateField()
    lugar_verificado = models.CharField(max_length=255)
    resultado = models.CharField(max_length=24, choices=Resultado.choices)
    hechos_constatados = models.TextField()
    medidas_adoptadas = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    proxima_verificacion = models.DateField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "denuncias_actuacion_municipal"
        ordering = ["-fecha_registro", "-pk"]
        verbose_name = "Actuación municipal"
        verbose_name_plural = "Actuaciones municipales"

    def __str__(self):
        return f"Actuación #{self.pk} — Denuncia #{self.denuncia_id}"
