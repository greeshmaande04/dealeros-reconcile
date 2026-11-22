from django.core.management.base import BaseCommand

from reconcile.importer import import_all_csvs


class Command(BaseCommand):
    help = "Import locations.csv, system_a.csv, and system_b.csv into the database."

    def handle(self, *args, **options):
        counts = import_all_csvs()
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported -> locations: {counts['locations']}, "
                f"system_a: {counts['system_a']}, "
                f"system_b: {counts['system_b']}"
            )
        )