# helpers.py
from datetime import datetime, timedelta, UTC

def safe_float(v):
    try:
        return float(v)
    except:
        return None

def safe_list(items, key):
    out = []
    for it in items:
        try:
            out.append(float(it.get(key)))
        except:
            out.append(None)
    return out

def compute_week_boundaries(target_year=None, target_week=None):
    """
    Compute Monday 00:00–next Monday 00:00 for given ISO week.
    If target_year/week is None → take previous ISO week.
    """
    today = datetime.now(UTC)
    iso_year, iso_week, iso_day = today.isocalendar()

    if target_year is None:  target_year = iso_year
    if target_week is None:  target_week = iso_week - 1

    # Monday of that week
    week_start = datetime.fromisocalendar(target_year, target_week, 1).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=UTC
    )
    # Next Monday
    week_end = week_start + timedelta(days=7)

    return week_start, week_end, target_year, target_week
