"""Pure comparison logic: no database, no web code. Easy to test.

a_rows: {record_id: {"total": Decimal|None, "location": str, "date": date|None, "state": str}}
b_rows: [{"entry_id", "ref" (already cleaned), "value": Decimal|None, "location", "date"}]
all_a_ids: every A record_id that exists (any org). Used only to tell a real
           orphan from an entry that belongs to another org's record.
"""

MISSING_IN_B = "MISSING_IN_B"
ORPHAN_IN_B = "ORPHAN_IN_B"
DUPLICATE_IN_B = "DUPLICATE_IN_B"
VALUE_MISMATCH = "VALUE_MISMATCH"
LOCATION_MISMATCH = "LOCATION_MISMATCH"  # extra
DATE_MISMATCH = "DATE_MISMATCH"          # extra
VOIDED_IN_B = "VOIDED_IN_B"              # extra


def _row(reason, record_id, a=None, b_value=None, b_location=None, entry_id=None):
    return {
        "reason": reason,
        "record_id": record_id,
        "entry_id": entry_id,
        "a_location": a["location"] if a else None,
        "b_location": b_location,
        "a_value": a["total"] if a else None,
        "b_value": b_value,
    }


def compare(a_rows, b_rows, all_a_ids=None):
    all_a_ids = set(all_a_ids) if all_a_ids is not None else set(a_rows)
    out, by_ref = [], {}
    for e in b_rows:
        by_ref.setdefault(e["ref"], []).append(e)

    # Entries pointing at a record that is not in A at all
    for ref, entries in by_ref.items():
        if ref in a_rows or ref in all_a_ids:
            continue  # known record (maybe another org's): not an orphan
        for e in entries:
            out.append(_row(ORPHAN_IN_B, ref, None, e["value"], e["location"], e["entry_id"]))

    for rid, a in a_rows.items():
        entries = by_ref.get(rid, [])
        known = [e["value"] for e in entries if e["value"] is not None]
        b_sum = sum(known) if known and len(known) == len(entries) else None

        if a.get("state") == "VOIDED":
            if entries:  # voided in A but B still has it
                out.append(_row(VOIDED_IN_B, rid, a, b_sum, entries[0]["location"]))
            continue  # a voided record is not expected in B

        if not entries:
            out.append(_row(MISSING_IN_B, rid, a))
            continue

        if any(e["value"] is None for e in entries):  # blank = unknown, never 0
            out.append(_row(VALUE_MISMATCH, rid, a, None, entries[0]["location"]))
            continue

        if len(entries) > 1:
            if sum(e["value"] for e in entries) != a["total"]:  # split that adds up is fine
                out.append(_row(DUPLICATE_IN_B, rid, a, b_sum, entries[0]["location"]))
            continue

        e = entries[0]
        if e["value"] != a["total"]:
            out.append(_row(VALUE_MISMATCH, rid, a, e["value"], e["location"], e["entry_id"]))
        if e["location"] != a["location"]:
            out.append(_row(LOCATION_MISMATCH, rid, a, e["value"], e["location"], e["entry_id"]))
        if e["date"] and a.get("date") and e["date"] != a["date"]:
            out.append(_row(DATE_MISMATCH, rid, a, e["value"], e["location"], e["entry_id"]))
    return out