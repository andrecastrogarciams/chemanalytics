import json

from django.core.management.base import BaseCommand

from apps.health.services import build_dependencies_payload, build_live_payload


class Command(BaseCommand):
    help = "Exibe status operacional minimo da aplicacao e dependencias."

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="Formato da saida",
        )

    def handle(self, *args, **options):
        payload = {
            "live": build_live_payload(),
            "dependencies": build_dependencies_payload(),
        }

        if options["format"] == "json":
            self.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False))
            return

        self.stdout.write("ChemAnalytics system status")
        self.stdout.write(f"live: {payload['live']['status']}")
        for name, info in payload["dependencies"]["dependencies"].items():
            self.stdout.write(f"{name}: {info['status']}")
