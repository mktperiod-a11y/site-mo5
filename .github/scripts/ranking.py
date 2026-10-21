"""Weekly ranking shared by render_ranking.py (what the page shows) and collect.py (what it showed last week)."""
import random


def apply_max_rank(data, ranked):
    """maxRank {id: lowest allowed rank}: an entry ranked below it is moved up to that rank."""
    for sid, worst in sorted(data.get("maxRank", {}).items(), key=lambda kv: kv[1]):
        pos = next((i for i, s in enumerate(ranked) if s["id"] == sid), None)
        if pos is not None and pos >= worst:
            ranked.insert(worst - 1, ranked.pop(pos))
    return ranked


def weekly(data, start):
    """Ready entries for the week starting on `start`, with that week's adjustment, best first.

    Each week a few entries get an adjustment of up to ±max points. The draw is seeded by
    the week's Monday, so every build in the same week shows the same ranking.
    """
    cfg = data["weeklyAdjust"]
    ready = [dict(s) for s in data["webhards"] if s["status"] == "ready" and "index" in s]
    rng = random.Random(start.isoformat())
    for s in rng.sample(ready, min(cfg["items"], len(ready))):
        new = round(min(100, max(0, s["index"] + rng.uniform(-cfg["max"], cfg["max"]))), 1)
        if s.get("parts") and s["index"]:
            # spread the adjustment over the parts so the chart's per-part scores still add up to the index
            s["parts"] = {k: round(v * new / s["index"], 1) for k, v in s["parts"].items()}
        s["index"] = new
    for s in ready:
        s["score"] = f"{s['index'] / 20:.1f}"
    return apply_max_rank(data, sorted(ready, key=lambda s: -s["index"]))
