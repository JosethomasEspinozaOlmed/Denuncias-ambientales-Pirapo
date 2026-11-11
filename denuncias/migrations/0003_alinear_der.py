"""Alinea el esquema al DER de seis entidades sin descartar denuncias históricas.

IMPORTANTE: esta migración sigue a 0002_initial, que ya está aplicada
en el proyecto local. NO modificar 0001_initial ni 0002_initial. Realizar pg_dump antes de ejecutar.
"""
from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


def migrar_ubicaciones_evidencias_y_historial(apps, schema_editor):
    Denuncia = apps.get_model("denuncias", "Denuncia")
    Ubicacion = apps.get_model("denuncias", "Ubicacion")
    Evidencia = apps.get_model("denuncias", "Evidencia")
    HistorialEstado = apps.get_model("denuncias", "HistorialEstado")
    db = schema_editor.connection.alias

    ubicaciones, evidencias = [], []
    for denuncia in Denuncia.objects.using(db).all().iterator(chunk_size=500):
        direccion = (denuncia.direccion or "").strip()
        tiene_lat = denuncia.latitud is not None
        tiene_lon = denuncia.longitud is not None
        if tiene_lat != tiene_lon or not (direccion or (tiene_lat and tiene_lon)):
            raise RuntimeError(
                f"La denuncia #{denuncia.pk} tiene una ubicación inválida. "
                "Corrige ese registro en la versión anterior antes de migrar."
            )
        ubicaciones.append(Ubicacion(
            denuncia_id=denuncia.pk, direccion=direccion,
            latitud=denuncia.latitud, longitud=denuncia.longitud,
        ))
        if denuncia.foto:
            evidencias.append(Evidencia(
                denuncia_id=denuncia.pk, archivo=str(denuncia.foto),
            ))
        if len(ubicaciones) >= 500:
            Ubicacion.objects.using(db).bulk_create(ubicaciones, batch_size=500)
            ubicaciones = []
        if len(evidencias) >= 500:
            Evidencia.objects.using(db).bulk_create(evidencias, batch_size=500)
            evidencias = []
    if ubicaciones:
        Ubicacion.objects.using(db).bulk_create(ubicaciones, batch_size=500)
    if evidencias:
        Evidencia.objects.using(db).bulk_create(evidencias, batch_size=500)

    etiquetas = {
        "pendiente": "PENDIENTE", "en proceso": "EN_PROCESO", "resuelto": "RESUELTO"
    }
    for evento in HistorialEstado.objects.using(db).select_related("usuario").iterator(chunk_size=500):
        campos = []
        if evento.accion in ("CAMBIO_ESTADO", "ASIGNACION") and evento.usuario.rol == "FUNCIONARIO":
            evento.funcionario_id = evento.usuario_id
            campos.append("funcionario")
        if evento.accion == "CREACION":
            evento.estado_nuevo = "PENDIENTE"
            campos.append("estado_nuevo")
        elif evento.accion == "CAMBIO_ESTADO":
            detalle = (evento.observacion or "").strip().rstrip(".")
            partes = detalle.split("→")
            if len(partes) == 2:
                anterior = etiquetas.get(partes[0].strip().lower(), "")
                nuevo = etiquetas.get(partes[1].strip().lower(), "")
                if anterior and nuevo:
                    evento.estado_anterior = anterior
                    evento.estado_nuevo = nuevo
                    campos += ["estado_anterior", "estado_nuevo"]
        if campos:
            evento.save(using=db, update_fields=campos)


class Migration(migrations.Migration):
    dependencies = [
        ("denuncias", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="categoria", name="descripcion",
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name="categoria", name="id",
            field=models.BigAutoField(primary_key=True, serialize=False, db_column="id_categoria"),
        ),
        migrations.AlterField(
            model_name="categoria", name="activa",
            field=models.BooleanField(default=True, db_column="activo"),
        ),
        migrations.AlterField(
            model_name="denuncia", name="id",
            field=models.BigAutoField(primary_key=True, serialize=False, db_column="id_denuncia"),
        ),
        migrations.AlterField(
            model_name="denuncia", name="ciudadano",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT,
                related_name="denuncias", db_column="id_usuario",
            ),
        ),
        migrations.AlterField(
            model_name="denuncia", name="categoria",
            field=models.ForeignKey(
                to="denuncias.categoria", on_delete=django.db.models.deletion.PROTECT,
                related_name="denuncias", db_column="id_categoria",
            ),
        ),
        migrations.AlterField(
            model_name="denuncia", name="creado",
            field=models.DateTimeField(auto_now_add=True, db_column="fecha_registro"),
        ),
        migrations.AlterField(
            model_name="denuncia", name="actualizado",
            field=models.DateTimeField(auto_now=True, db_column="fecha_actualizacion"),
        ),
        migrations.RenameModel(old_name="HistorialDenuncia", new_name="HistorialEstado"),
        migrations.AlterModelTable(name="historialestado", table="denuncias_historial_estado"),
        migrations.AlterModelOptions(
            name="historialestado",
            options={"ordering": ["-fecha", "-pk"], "verbose_name": "Movimiento de denuncia",
                     "verbose_name_plural": "Historial de denuncias"},
        ),
        migrations.RenameField(model_name="historialestado", old_name="detalle", new_name="observacion"),
        migrations.AlterField(
            model_name="historialestado", name="id",
            field=models.BigAutoField(primary_key=True, serialize=False, db_column="id_historial"),
        ),
        migrations.AlterField(
            model_name="historialestado", name="denuncia",
            field=models.ForeignKey(
                to="denuncias.denuncia", on_delete=django.db.models.deletion.CASCADE,
                related_name="historial", db_column="id_denuncia",
            ),
        ),
        migrations.AlterField(
            model_name="historialestado", name="fecha",
            field=models.DateTimeField(auto_now_add=True, db_column="fecha_cambio"),
        ),
        migrations.AlterField(
            model_name="historialestado", name="usuario",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT,
                related_name="historial_como_actor",
            ),
        ),
        migrations.AlterField(
            model_name="historialestado", name="observacion",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="historialestado", name="estado_anterior",
            field=models.CharField(max_length=20, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="historialestado", name="estado_nuevo",
            field=models.CharField(max_length=20, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="historialestado", name="funcionario",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT,
                related_name="historial_como_funcionario", blank=True, null=True,
                db_column="id_funcionario",
            ),
        ),
        migrations.CreateModel(
            name="Ubicacion",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, db_column="id_ubicacion")),
                ("direccion", models.CharField(max_length=255, blank=True)),
                ("latitud", models.DecimalField(
                    max_digits=9, decimal_places=6, blank=True, null=True,
                    validators=[MinValueValidator(-90), MaxValueValidator(90)],
                )),
                ("longitud", models.DecimalField(
                    max_digits=9, decimal_places=6, blank=True, null=True,
                    validators=[MinValueValidator(-180), MaxValueValidator(180)],
                )),
                ("denuncia", models.OneToOneField(
                    to="denuncias.denuncia", on_delete=django.db.models.deletion.CASCADE,
                    related_name="ubicacion", db_column="id_denuncia",
                )),
            ],
            options={"verbose_name": "Ubicación", "verbose_name_plural": "Ubicaciones"},
        ),
        migrations.CreateModel(
            name="Evidencia",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, db_column="id_evidencia")),
                ("archivo", models.ImageField(
                    upload_to="denuncias/%Y/%m/",
                    validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
                )),
                ("fecha_carga", models.DateTimeField(auto_now_add=True)),
                ("denuncia", models.OneToOneField(
                    to="denuncias.denuncia", on_delete=django.db.models.deletion.CASCADE,
                    related_name="evidencia", db_column="id_denuncia",
                )),
            ],
            options={"verbose_name": "Evidencia", "verbose_name_plural": "Evidencias"},
        ),
        migrations.RunPython(migrar_ubicaciones_evidencias_y_historial),
        migrations.RemoveField(model_name="denuncia", name="direccion"),
        migrations.RemoveField(model_name="denuncia", name="latitud"),
        migrations.RemoveField(model_name="denuncia", name="longitud"),
        migrations.RemoveField(model_name="denuncia", name="foto"),
    ]
