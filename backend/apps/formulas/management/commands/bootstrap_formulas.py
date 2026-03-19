import json

from django.core.management.base import BaseCommand, CommandError

from apps.formulas.services import bootstrap_formulas_from_file


class Command(BaseCommand):
    help = "Importa formulas iniciais de CSV ou XLSX e gera relatorio."

    def add_arguments(self, parser):
        parser.add_argument("file_path", help="Caminho para o arquivo CSV/XLSX de bootstrap")
        parser.add_argument("--format", choices=["text", "json"], default="text")

    def handle(self, *args, **options):
        try:
            report = bootstrap_formulas_from_file(options["file_path"])
        except (FileNotFoundError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        if options["format"] == "json":
            self.stdout.write(json.dumps(report, indent=2, ensure_ascii=False))
            return

        self.stdout.write("Formula bootstrap report")
        self.stdout.write(f"source_file: {report['source_file']}")
        self.stdout.write(f"source_type: {report['source_type']}")
        self.stdout.write(f"formulas_created: {report['formulas_created']}")
        self.stdout.write(f"versions_created: {report['versions_created']}")
        self.stdout.write(f"items_created: {report['items_created']}")
        self.stdout.write(f"incomplete_items_created: {report['incomplete_items_created']}")
        self.stdout.write(f"rejected_rows: {len(report['rejected_rows'])}")
