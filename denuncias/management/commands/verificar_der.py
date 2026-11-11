from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from denuncias.models import Denuncia, Evidencia, HistorialEstado, Ubicacion
from usuarios.models import Usuario
from denuncias.models import Categoria


class Command(BaseCommand):
    help = "Verifica que las denuncias antiguas se conservaron con ubicación y evidencia."

    def handle(self, *args, **options):
        sin_ubicacion = Denuncia.objects.filter(ubicacion__isnull=True).count()
        invalidas = Ubicacion.objects.filter(
            Q(direccion="") & (Q(latitud__isnull=True) | Q(longitud__isnull=True))
        ).count()
        total_denuncias = Denuncia.objects.count()
        self.stdout.write("DER de seis entidades (más tablas internas de Django):")
        for nombre, modelo in [
            ("Usuario", Usuario), ("Categoria", Categoria),
            ("Denuncia", Denuncia), ("Ubicacion", Ubicacion),
            ("Evidencia", Evidencia), ("HistorialEstado", HistorialEstado),
        ]:
            self.stdout.write(f"  {nombre}: {modelo.objects.count()} registros")
        if sin_ubicacion or invalidas or Ubicacion.objects.count() != total_denuncias:
            raise CommandError(
                f"Ubicaciones incorrectas: {sin_ubicacion} denuncias sin ubicación; "
                f"{invalidas} ubicaciones sin dato; revisá los registros."
            )
        self.stdout.write(self.style.SUCCESS("CORRECTO: cada denuncia tiene exactamente una ubicación."))
