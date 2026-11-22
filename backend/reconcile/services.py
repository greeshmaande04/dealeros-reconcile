from collections import defaultdict
from decimal import Decimal

from .importer import normalize_record_ref
from .models import Location, SystemARecord, SystemBEntry


def reconcile_records(
    org_id: str | None = None,
    loc_id: str | None = None,
    status_filter: str | None = None,
) -> dict:
    """Reconcile SystemARecord entries against SystemBEntry entries."""
    loc_to_org = dict(Location.objects.values_list("loc_id", "org_id"))

    sys_a_qs = SystemARecord.objects.all()
    sys_b_qs = SystemBEntry.objects.all()

    if loc_id:
        sys_a_qs = sys_a_qs.filter(loc_id=loc_id)
        sys_b_qs = sys_b_qs.filter(loc_id=loc_id)

    if org_id:
        matching_locs = [lid for lid, oid in loc_to_org.items() if oid == org_id]
        sys_a_qs = sys_a_qs.filter(loc_id__in=matching_locs)
        sys_b_qs = sys_b_qs.filter(loc_id__in=matching_locs)

    # Group System B entries by normalized record_ref + loc_id
    b_by_key: dict[tuple[str, str], list[SystemBEntry]] = defaultdict(list)
    b_by_ref_only: dict[str, list[SystemBEntry]] = defaultdict(list)

    for entry in sys_b_qs:
        norm_ref = normalize_record_ref(entry.record_ref)
        b_by_key[(norm_ref, entry.loc_id)].append(entry)
        b_by_ref_only[norm_ref].append(entry)

    matched_b_ids: set[int] = set()
    items: list[dict] = []

    summary = {
        "total_a": 0,
        "total_b": sys_b_qs.count(),
        "matched": 0,
        "mismatch": 0,
        "missing_in_b": 0,
        "missing_in_a": 0,
    }

    for rec in sys_a_qs.order_by("record_id"):
        summary["total_a"] += 1
        norm_id = normalize_record_ref(rec.record_id)
        matched_entries = b_by_key.get((norm_id, rec.loc_id), [])

        # Fallback match on normalized ref if loc_id differs/blank
        loc_mismatch = False
        if not matched_entries and b_by_ref_only.get(norm_id):
            matched_entries = b_by_ref_only[norm_id]
            loc_mismatch = True

        for e in matched_entries:
            matched_b_ids.add(e.id)

        a_total = rec.total_value
        if a_total is None and rec.base_value is not None:
            a_total = rec.base_value + (rec.adjustment or Decimal("0.00"))

        b_total: Decimal | None = None
        if matched_entries:
            b_total = sum(
                (e.value for e in matched_entries if e.value is not None),
                Decimal("0.00"),
            )

        calc_mismatch = False
        if (
            rec.base_value is not None
            and rec.adjustment is not None
            and rec.total_value is not None
            and (rec.base_value + rec.adjustment) != rec.total_value
        ):
            calc_mismatch = True

        issues: list[str] = []
        if not matched_entries:
            status = "missing_in_b"
            summary["missing_in_b"] += 1
            issues.append("No matching entry in System B")
        else:
            if loc_mismatch:
                issues.append("Location ID differs between System A and System B")
            if calc_mismatch:
                issues.append("System A base_value + adjustment != total_value")
            if a_total is not None and b_total is not None and a_total != b_total:
                issues.append(f"Value mismatch (A: {a_total}, B: {b_total})")

            if issues:
                status = "mismatch"
                summary["mismatch"] += 1
            else:
                status = "matched"
                summary["matched"] += 1

        diff = (
            (a_total - b_total)
            if (a_total is not None and b_total is not None)
            else None
        )

        item = {
            "record_id": rec.record_id,
            "normalized_id": norm_id,
            "loc_id": rec.loc_id,
            "org_id": loc_to_org.get(rec.loc_id),
            "event_date": rec.event_date.isoformat() if rec.event_date else None,
            "category_code": rec.category_code,
            "actor_id": rec.actor_id,
            "state": rec.state,
            "base_value": str(rec.base_value) if rec.base_value is not None else None,
            "adjustment": str(rec.adjustment) if rec.adjustment is not None else None,
            "system_a_total": str(a_total) if a_total is not None else None,
            "system_b_total": str(b_total) if b_total is not None else None,
            "difference": str(diff) if diff is not None else None,
            "status": status,
            "issues": issues,
        }

        if not status_filter or status == status_filter:
            items.append(item)

    # Any System B entries not matched to a System A record
    for entry in sys_b_qs.order_by("entry_id"):
        if entry.id in matched_b_ids:
            continue
        summary["missing_in_a"] += 1
        status = "missing_in_a"
        item = {
            "record_id": None,
            "normalized_id": normalize_record_ref(entry.record_ref),
            "entry_id": entry.entry_id,
            "loc_id": entry.loc_id,
            "org_id": loc_to_org.get(entry.loc_id),
            "event_date": entry.recorded_on.isoformat() if entry.recorded_on else None,
            "category_code": "",
            "actor_id": None,
            "state": "",
            "base_value": None,
            "adjustment": None,
            "system_a_total": None,
            "system_b_total": str(entry.value) if entry.value is not None else None,
            "difference": None,
            "status": status,
            "issues": ["No matching record in System A"],
        }
        if not status_filter or status == status_filter:
            items.append(item)

    return {
        "summary": summary,
        "count": len(items),
        "results": items,
    }