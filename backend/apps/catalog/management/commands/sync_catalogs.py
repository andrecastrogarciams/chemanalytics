import json

from django.core.management.base import BaseCommand, CommandError

from apps.catalog.oracle_adapter import OracleSyncError
from apps.catalog.services import sync_catalogs


class Command(BaseCommand):
    help = "Sincroniza catalogos auxiliares e imprime relatorio."

    def add_arguments(self, parser):
        parser.add_argument("--format", choices=["text", "json"], default="text")

    def handle(self, *args, **options):
        try:
            sync_run = sync_catalogs()
        except OracleSyncError as exc:
            raise CommandError(str(exc)) from exc

        payload = {
            "id": sync_run.id,
            "status": sync_run.status,
            "articles": sync_run.records_articles_upserted,
            "chemicals": sync_run.records_products_upserted,
        }
        if options["format"] == "json":
            self.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            for key, value in payload.items():
                self.stdout.write(f"{key}: {value}")
