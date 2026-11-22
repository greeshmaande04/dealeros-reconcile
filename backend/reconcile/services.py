from django.db.models import Q

from .compare import compare
from .importer import normalize_record_ref
from .models import Location, SystemARecord, SystemBEntry


class UnknownOrg(Exception):
    pass


def get_disagreements(org, reason=None, sort=None):
    # 1. Which locations belong to this org? Only locations.csv says so.
    org_locs = set(Location.objects.filter(org_id=org).values_list("loc_id", flat=True))
    if not org_locs:
        raise UnknownOrg(org)

    # 2. Filter INSIDE the database: only this org's A records, and only B entries
    #    at this org's locations or pointing at this org's A records.
    a_qs = SystemARecord.objects.filter(loc_id__in=org_locs)
    a_rows = {}
    for r in a_qs:
        total = r.total_value
        if total is None and r.base_value is not None:
            total = r.base_value + (r.adjustment or 0)
        a_rows[normalize_record_ref(r.record_id)] = {
            "total": total, "location": r.loc_id,
            "date": r.event_date, "state": r.state,
        }
    b_qs = SystemBEntry.objects.filter(
        Q(loc_id__in=org_locs) | Q(record_ref__in=list(a_rows))
    )
    b_rows = [{
        "entry_id": e.entry_id, "ref": normalize_record_ref(e.record_ref),
        "value": e.value, "location": e.loc_id, "date": e.recorded_on,
    } for e in b_qs]

    # Only the ids (never shown) so a real orphan is told apart from another org's record
    all_a_ids = {normalize_record_ref(x) for x in
                 SystemARecord.objects.values_list("record_id", flat=True)}

    rows = compare(a_rows, b_rows, all_a_ids)

    # 3. Cross-org trap: never reveal a location that is not this org's.
    for r in rows:
        if r["a_location"] not in org_locs:
            r["a_location"] = None
        if r["b_location"] not in org_locs:
            r["b_location"] = None

    if reason:
        rows = [r for r in rows if r["reason"] == reason]

    def val(r):
        return r["a_value"] if r["a_value"] is not None else r["b_value"]
    if sort in ("value", "-value"):
        has = sorted((r for r in rows if val(r) is not None), key=val, reverse=sort == "-value")
        rows = has + [r for r in rows if val(r) is None]

    for r in rows:  # JSON-safe
        for k in ("a_value", "b_value"):
            r[k] = str(r[k]) if r[k] is not None else None
    return rows