import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from reconcile.importer import normalize_record_ref, parse_amount, parse_date
from reconcile.models import Location, SystemARecord, SystemBEntry


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            yield {(k or "").strip(): (v or "").strip() for k, v in row.items()}


class Command(BaseCommand):
    help = "Import locations.csv, system_a.csv, system_b.csv (safe to run twice)."

    def handle(self, *args, **opts):
        data = Path(settings.BASE_DIR) / "data"
        loc_n = a_read = a_saved = b_read = b_saved = blanks = cleaned = 0

        for r in read_csv(data / "locations.csv"):
            Location.objects.update_or_create(
                loc_id=r["location_id"],
                defaults={"org_id": r["org_id"], "name": r.get("name", "")},
            )
            loc_n += 1

        for r in read_csv(data / "system_a.csv"):
            a_read += 1
            SystemARecord.objects.update_or_create(
                record_id=r["record_id"],
                defaults={
                    "loc_id": r["location_id"],
                    "event_date": parse_date(r.get("event_date")),
                    "category_code": r.get("category_code", ""),
                    "actor_id": r.get("actor_id") or None,
                    "base_value": parse_amount(r.get("base_value")),
                    "adjustment": parse_amount(r.get("adjustment")),
                    "total_value": parse_amount(r.get("total_value")),
                    "state": r.get("state", ""),
                },
            )
            a_saved += 1

        for r in read_csv(data / "system_b.csv"):
            b_read += 1
            ref = normalize_record_ref(r["record_ref"])
            val = parse_amount(r.get("value"))
            blanks += val is None
            cleaned += ref != r["record_ref"]
            SystemBEntry.objects.update_or_create(
                entry_id=r["entry_id"],
                defaults={
                    "record_ref_raw": r["record_ref"],
                    "record_ref": ref,
                    "loc_id": r["location_id"],
                    "recorded_on": parse_date(r.get("recorded_on")),
                    "value_raw": r.get("value", ""),
                    "value": val,
                    "label": r.get("label", ""),
                },
            )
            b_saved += 1

        self.stdout.write(
            f"Locations: {loc_n}; A: {a_read} read, {a_saved} saved; "
            f"B: {b_read} read, {b_saved} saved; values left empty: {blanks}; refs cleaned: {cleaned}"
        )
        if (a_read, b_read) != (a_saved, b_saved):
            self.stderr.write("WARNING: rows read != rows saved")