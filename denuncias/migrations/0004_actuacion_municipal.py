# Ampliación aprobada del flujo de gestión municipal: historial de verificaciones.
# Depende de 0003_alinear_der. No modifica denuncias ni actuaciones anteriores.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("denuncias", "0003_alinear_der"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActuacionMunicipal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha_verificacion", models.DateField()),
                ("lugar_verificado", models.CharField(max_length=255)),
                ("resultado", models.CharField(
                    max_length=24,
                    choices=[
                        ("CONFIRMADA", "Problemática confirmada"),
                        ("NO_CONSTATADA", "Problemática no constatada"),
                        ("REQUIERE_SEGUIMIENTO", "Requiere seguimiento"),
                    ],
                )),
                ("hechos_constatados", models.TextField()),
                ("medidas_adoptadas", models.TextField(blank=True)),
                ("observaciones", models.TextField(blank=True)),
                ("proxima_verificacion", models.DateField(blank=True, null=True)),
                ("fecha_registro", models.DateTimeField(auto_now_add=True)),
                ("denuncia", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="actuaciones", to="denuncias.denuncia",
                )),
                ("funcionario", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="actuaciones_municipales",
                    limit_choices_to={"rol": "FUNCIONARIO"},
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "db_table": "denuncias_actuacion_municipal",
                "ordering": ["-fecha_registro", "-pk"],
                "verbose_name": "Actuación municipal",
                "verbose_name_plural": "Actuaciones municipales",
            },
        ),
    ]
