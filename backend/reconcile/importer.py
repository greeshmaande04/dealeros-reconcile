import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


def normalize_record_ref(raw):
    """'rec1034', ' REC - 1070 ', '1112' -> 'REC-1034' etc. None if no digits."""
    m = re.search(r"\d+", raw or "")
    return f"REC-{m.group()}" if m else None


def parse_amount(raw):
    """'1,25,400.00' -> Decimal('125400.00'). Blank or junk -> None, never 0."""
    s = (raw or "").strip().replace(",", "")
    if not s:
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d")


def parse_date(raw):
    """Try a few formats; unknown -> None (row is kept, original not lost for A/B amounts)."""
    s = (raw or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None