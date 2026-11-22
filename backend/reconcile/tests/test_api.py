import json
from datetime import date
from decimal import Decimal as D

import pytest
from rest_framework.test import APIClient

from reconcile.models import Location, SystemARecord, SystemBEntry

DAY = date(2026, 3, 1)


@pytest.fixture
def data(db):
    Location.objects.create(loc_id="LOC-101", org_id="ORG-A")
    Location.objects.create(loc_id="LOC-201", org_id="ORG-B")
    # normal ORG-A mismatch
    SystemARecord.objects.create(record_id="REC-1", loc_id="LOC-101", event_date=DAY, total_value=D("100"), state="CONFIRMED")
    SystemBEntry.objects.create(entry_id="E1", record_ref="REC-1", loc_id="LOC-101", recorded_on=DAY, value=D("90"))
    # normal ORG-B mismatch
    SystemARecord.objects.create(record_id="REC-2", loc_id="LOC-201", event_date=DAY, total_value=D("50"), state="CONFIRMED")
    SystemBEntry.objects.create(entry_id="E2", record_ref="REC-2", loc_id="LOC-201", recorded_on=DAY, value=D("40"))
    # trap row: A at ORG-A location, B at ORG-B location
    SystemARecord.objects.create(record_id="REC-3", loc_id="LOC-101", event_date=DAY, total_value=D("10"), state="CONFIRMED")
    SystemBEntry.objects.create(entry_id="E3", record_ref="REC-3", loc_id="LOC-201", recorded_on=DAY, value=D("10"))


def get(org):
    return APIClient().get("/api/disagreements/", {"org": org} if org else {})


def test_org_is_required(data):
    assert get(None).status_code == 400


def test_org_a_sees_no_org_b_data(data):
    body = json.dumps(get("ORG-A").json())
    assert "LOC-201" not in body and "REC-2" not in body and "E2" not in body


def test_org_b_sees_no_org_a_data(data):
    body = json.dumps(get("ORG-B").json())
    assert "LOC-101" not in body and "REC-1" not in body and "REC-3" not in body


def test_cross_org_row_hides_other_orgs_location(data):
    rows = get("ORG-A").json()["results"]
    trap = [r for r in rows if r["record_id"] == "REC-3"][0]
    assert trap["reason"] == "LOCATION_MISMATCH"
    assert trap["a_location"] == "LOC-101" and trap["b_location"] is None