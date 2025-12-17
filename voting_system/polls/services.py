# polls/services.py
from decimal import Decimal, ROUND_HALF_UP
from .mongo import get_votes_collection

def tally_poll(poll):
    col = get_votes_collection()
    pid = int(poll.pk)

    pipeline = [
        {"$match": {"poll_id": pid}},
        {"$group": {"_id": "$option_id", "count": {"$sum": 1}}},
    ]
    raw = list(col.aggregate(pipeline))
    counts = {int(doc["_id"]): int(doc["count"]) for doc in raw}
    total = sum(counts.values())

    rows = []
    for opt in poll.options.all().order_by("order", "id"):
        c = counts.get(int(opt.pk), 0)
        pct = Decimal("0.0")
        if total:
            pct = (Decimal(c) * 100 / Decimal(total)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        rows.append({"option": opt, "count": c, "percent": pct})

    return {"total": total, "by_option": rows}


def check_validity(poll, total_votes):
    expected = getattr(poll, "expected_turnout", None)
    if expected and expected > 0:
        reached_pct = (Decimal(total_votes) * 100 / Decimal(expected)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        return (reached_pct >= Decimal(poll.quorum)), f"Набрано {reached_pct}%, потрібно ≥ {poll.quorum}% від {expected}"
    return (False, "Кворум не перевіряється (expected_turnout не задано).")
