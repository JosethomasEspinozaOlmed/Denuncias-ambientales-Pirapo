from django.core.management.base import BaseCommand
from denuncias.models import Categoria

CATEGORIAS = [
    "Residuos y basurales",
    "Quema de basura",
    "Contaminación del agua",
    "Contaminación del aire",
    "Árboles y áreas verdes",
    "Desagües y aguas residuales",
    "Otros problemas ambientales",
]

class Command(BaseCommand):
    help = "Carga categorías ambientales básicas (sin duplicarlas)."

    def handle(self, *args, **options):
        for nombre in CATEGORIAS:
            Categoria.objects.get_or_create(nombre=nombre)
        self.stdout.write(self.style.SUCCESS("Categorías ambientales preparadas."))
