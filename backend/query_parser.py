"""
Deterministic query parsing for sender and temporal filters.
No LLM involved.
"""

import re
from datetime import datetime, timedelta

PARTICIPANTS = ["Priya", "Rohan", "Anjali", "Karan", "Meera", "Vikram", "Sneha", "Amit"]

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

# dataset reference point = end of the generated range (not "now")
REFERENCE_DATE = datetime(2024, 6, 30, 23, 59, 59)


def detect_sender(query: str) -> str | None:
    lowered = " " + query.lower() + " "
    for name in PARTICIPANTS:
        if f" {name.lower()} " in lowered or f"{name.lower()}'s" in lowered:
            return name
    return None


def month_range(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1)
    end = datetime(year + (month == 12), (month % 12) + 1, 1) - timedelta(seconds=1)
    return start, end


def parse_relative(expr: str, ref: datetime) -> tuple[datetime, datetime] | None:
    lowered = expr.lower()
    if "this month" in lowered:
        return month_range(ref.year, ref.month)
    if "last month" in lowered:
        m, y = ref.month - 1, ref.year
        if m == 0:
            m, y = 12, y - 1
        return month_range(y, m)
    if "this week" in lowered:
        start = ref - timedelta(days=ref.weekday())
        start = start.replace(hour=0, minute=0, second=0)
        return start, ref
    if "last week" in lowered:
        end = ref - timedelta(days=ref.weekday() + 1)
        end = end.replace(hour=23, minute=59, second=59)
        start = end - timedelta(days=6)
        start = start.replace(hour=0, minute=0, second=0)
        return start, end
    return None


def parse_date(text: str, default_year: int = 2024) -> datetime | None:
    text = text.strip().rstrip(".,?")
    # full date like "May 15 2024" / "15 May 2024" / "May 15, 2024"
    for pattern, fmt in [
        (r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", "%d %B %Y"),
        (r"([a-z]+)\s+(\d{1,2})\s*,?\s*(\d{4})", "%B %d %Y"),
    ]:
        m = re.fullmatch(pattern, text.lower())
        if m:
            try:
                return datetime.strptime(" ".join(m.groups()), fmt)
            except ValueError:
                pass
    # month + optional year, e.g. "May 2024" or "May"
    m = re.fullmatch(r"([a-z]+)(?:\s+(\d{4}))?", text.lower())
    if m and m.group(1) in MONTHS:
        month = MONTHS[m.group(1)]
        year = int(m.group(2)) if m.group(2) else default_year
        return datetime(year, month, 1)
    # numeric date
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None


def parse_temporal(query: str) -> tuple[datetime, datetime] | None:
    lowered = query.lower()

    # between <date> and <date>
    m = re.search(r"between\s+(.+?)\s+and\s+(.+?)(?:\s|$)", lowered)
    if m:
        d1, d2 = parse_date(m.group(1)), parse_date(m.group(2))
        if d1 and d2:
            return (min(d1, d2), max(d2, d1).replace(hour=23, minute=59, second=59))

    # before / after <date>
    m = re.search(r"before\s+(.+?)(?:\s|$)", lowered)
    if m:
        d = parse_date(m.group(1))
        if d:
            return datetime.min.replace(year=1), d - timedelta(seconds=1)
    m = re.search(r"after\s+(.+?)(?:\s|$)", lowered)
    if m:
        d = parse_date(m.group(1))
        if d:
            return d + timedelta(days=1), REFERENCE_DATE

    # relative expressions
    rel = parse_relative(lowered, REFERENCE_DATE)
    if rel:
        return rel

    # explicit month references like "May 2024" or "in March"
    m = re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b(?:\s+(\d{4}))?", lowered)
    if m:
        month = MONTHS[m.group(1)]
        year = int(m.group(2)) if m.group(2) else 2024
        return month_range(year, month)

    return None


def parse_query(query: str) -> dict:
    """Return {sender, date_range, clean_query} for a raw user query."""
    sender = detect_sender(query)
    date_range = parse_temporal(query)
    clean = query

    patterns = [
        r"\bthis month\b", r"\blast month\b", r"\bthis week\b", r"\blast week\b",
        r"\bbetween\s+.+?\s+and\s+.+?(?:\s|$)", r"\bbefore\s+.+?(?:\s|$)",
        r"\bafter\s+.+?(?:\s|$)",
        r"\b(?:in|during|of)\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b(?:\s+\d{4})?",
        r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b",
        r"\b(?:about|from|by|of)\s+(?:priya|rohan|anjali|karan|meera|vikram|sneha|amit)\b",
    ]
    for p in patterns:
        clean = re.sub(p, " ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+", " ", clean).strip(" ,?")

    return {"sender": sender, "date_range": date_range, "clean_query": clean}
