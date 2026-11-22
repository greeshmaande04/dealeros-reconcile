import csv
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.db import transaction

from .models import Location, SystemARecord, SystemBEntry


def normalize_record_ref(raw_ref: str | None) -> str:
    """Normalize messy record references like 'rec1034' or 'REC - 1070' -> 'REC-1070'."""
    if not raw_ref:
        return ""
    cleaned = raw_ref.strip().upper()
    match = re.match(r"^REC\s*[-_:\s]*(\d+)$", cleaned)
    if match:
        return f"REC-{match.group(1)}"
    return re.sub(r"\s+", "", cleaned)


def parse_decimal(raw_val: str | None) -> Decimal | None:
    """Parse comma-formatted or blank numeric strings into Decimal or None."""
    if raw_val is None:
        return None
    text = raw_val.strip().replace(",", "")
    if not text or text.lower() in {"na", "n/a", "null", "none", "-"}:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_date(raw_date: str | None) -> date | None:
    """Parse common date formats into a date object or None."""
    if not raw_date:
        return None
    text = raw_date.strip()
    if not text or text.lower() in {"na", "n/a", "null", "none"}:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def clean_optional_str(raw_val: str | None) -> str | None:
    if raw_val is None:
        return None
    text = raw_val.strip()
    return text if text else None


def get_data_dir() -> Path:
    return Path(settings.BASE_DIR) / "data"


@transaction.atomic
def import_all_csvs(data_dir: Path | None = None) -> dict[str, int]:
    """Import locations.csv, system_a.csv, and system_b.csv idempotently."""
    base = data_dir or get_data_dir()
    counts = {"locations": 0, "system_a": 0, "system_b": 0}

    loc_path = base / "locations.csv"
    if loc_path.exists():
        with loc_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                loc_id = (
                    row.get("Location_id")
                    or row.get("location_id")
                    or row.get("loc_id")
                    or ""
                ).strip()
                org_id = (row.get("org_id") or "").strip()
                if not loc_id:
                    continue
                Location.objects.update_or_create(
                    loc_id=loc_id,
                    defaults={"org_id": org_id},
                )
                counts["locations"] += 1

    sys_a_path = base / "system_a.csv"
    if sys_a_path.exists():
        with sys_a_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                raw_rec_id = (
                    row.get("Record_id") or row.get("record_id") or ""
                ).strip()
                if not raw_rec_id:
                    continue
                record_id = normalize_record_ref(raw_rec_id) or raw_rec_id
                loc_id = (
                    row.get("location_id")
                    or row.get("Location_id")
                    or row.get("loc_id")
                    or ""
                ).strip()
                SystemARecord.objects.update_or_create(
                    record_id=record_id,
                    defaults={
                        "loc_id": loc_id,
                        "event_date": parse_date(row.get("event_date")),
                        "category_code": (row.get("category_code") or "").strip(),
                        "actor_id": clean_optional_str(row.get("actor_id")),
                        "base_value": parse_decimal(row.get("base_value")),
                        "adjustment": parse_decimal(row.get("adjustment")),
                        "total_value": parse_decimal(row.get("total_value")),
                        "state": (row.get("state") or "").strip(),
                    },
                )
                counts["system_a"] += 1

    sys_b_path = base / "system_b.csv"
    if sys_b_path.exists():
        with sys_b_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                entry_id = (
                    row.get("entry_id") or row.get("Entry_id") or ""
                ).strip()
                if not entry_id:
                    continue
                raw_ref = (
                    row.get("record_ref") or row.get("Record_ref") or ""
                ).strip()
                record_ref = normalize_record_ref(raw_ref)
                loc_id = (
                    row.get("location_id")
                    or row.get("Location_id")
                    or row.get("loc_id")
                    or ""
                ).strip()
                SystemBEntry.objects.update_or_create(
                    entry_id=entry_id,
                    defaults={
                        "record_ref": record_ref,
                        "loc_id": loc_id,
                        "recorded_on": parse_date(row.get("recorded_on")),
                        "value": parse_decimal(row.get("value")),
                    },
                )
                counts["system_b"] += 1

    return counts