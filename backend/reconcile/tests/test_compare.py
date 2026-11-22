from datetime import date
from decimal import Decimal as D

from reconcile.compare import compare
from reconcile.importer import normalize_record_ref

DAY = date(2026, 3, 1)


def a(total="100.00", loc="L1", state="CONFIRMED"):
    return {"total": D(total), "location": loc, "date": DAY, "state": state}


def entry(eid, ref="REC-1", value="100.00", loc="L1", d=DAY):
    return {"entry_id": eid, "ref": ref, "value": D(value) if value is not None else None,
            "location": loc, "date": d}


def reasons(res):
    return [r["reason"] for r in res]


def test_clean_row_no_disagreement():
    assert compare({"REC-1": a()}, [entry("E1")]) == []

def test_missing_in_b():
    assert reasons(compare({"REC-1": a()}, [])) == ["MISSING_IN_B"]

def test_orphan_in_b():
    assert reasons(compare({"REC-1": a()}, [entry("E1"), entry("E2", ref="REC-999")])) == ["ORPHAN_IN_B"]

def test_duplicate_same_amount_flagged():
    res = compare({"REC-1": a()}, [entry("E1"), entry("E2")])
    assert reasons(res) == ["DUPLICATE_IN_B"]

def test_split_that_sums_is_not_an_error():
    assert compare({"REC-1": a()}, [entry("E1", value="40.00"), entry("E2", value="60.00")]) == []

def test_split_that_does_not_sum_is_flagged():
    assert reasons(compare({"REC-1": a()}, [entry("E1", value="40.00"), entry("E2", value="50.00")])) == ["DUPLICATE_IN_B"]

def test_value_mismatch():
    assert reasons(compare({"REC-1": a()}, [entry("E1", value="99.00")])) == ["VALUE_MISMATCH"]

def test_blank_value_flagged_and_not_zero():
    res = compare({"REC-1": a()}, [entry("E1", value=None)])
    assert reasons(res) == ["VALUE_MISMATCH"]
    assert res[0]["b_value"] is None          # empty, never 0

def test_blank_not_zero_even_when_a_total_is_zero():
    assert reasons(compare({"REC-1": a(total="0.00")}, [entry("E1", value=None)])) == ["VALUE_MISMATCH"]

def test_indian_commas_equal_after_cleaning():
    from reconcile.importer import parse_amount  # adjust name if yours differs
    assert parse_amount("1,25,400.00") == D("125400.00")

def test_location_mismatch():
    assert reasons(compare({"REC-1": a()}, [entry("E1", loc="L2")])) == ["LOCATION_MISMATCH"]

def test_date_mismatch():
    assert reasons(compare({"REC-1": a()}, [entry("E1", d=date(2026, 3, 2))])) == ["DATE_MISMATCH"]

def test_voided_without_b_is_not_missing():
    assert compare({"REC-1": a(state="VOIDED")}, []) == []

def test_voided_with_b_entry_flagged():
    assert reasons(compare({"REC-1": a(state="VOIDED")}, [entry("E1")])) == ["VOIDED_IN_B"]

def test_messy_references_match():
    for raw in ["rec1034", "REC - 1034", "1034", " REC-1034 "]:
        assert normalize_record_ref(raw) == "REC-1034"
    a_rows = {"REC-1034": a()}
    b = [entry("E1", ref=normalize_record_ref("rec1034"))]
    assert compare(a_rows, b) == []

def test_other_orgs_record_is_not_an_orphan():
    # ref exists in A (other org) but not in this org's rows
    assert compare({}, [entry("E1", ref="REC-5")], all_a_ids={"REC-5"}) == []