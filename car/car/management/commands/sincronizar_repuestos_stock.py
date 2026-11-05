from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Obsoleto: el inventario operativo vive en Repuesto"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "El inventario operativo ya vive directamente en Repuesto; no hay nada que sincronizar."
        ))
