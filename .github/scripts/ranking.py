"""Weekly ranking shared by render_ranking.py (what the page shows) and collect.py (what it showed last week)."""
import random
import sys

# services the owner decided never to list (2026-10); ask the owner before touching this
BLOCKED = {"미투디스크": "me2disk", "파일캐스트": "filecast", "파일이즈": "fileis", "애플파일": "applefile",
           "스마트파일": "smartfile", "피디팝": "pdpop"}


def check_blocked(data):
    """Stop when a blocked service is in the data, whatever its status."""
    found = [
        s.get("name") or s.get("id")
        for s in data["webhards"]
        for name, key in BLOCKED.items()
        if name in s.get("name", "").replace(" ", "")
        or key in " ".join(str(s.get(k, "")) for k in ("id", "url", "logo")).lower()
    ]
    if found:
        sys.exit(f"::error::다루지 않기로 한 웹하드가 데이터에 있습니다: {', '.join(found)}. 소유자에게 먼저 확인하세요.")


def full_shares(data):
    """Each part's largest possible value: its weight's share of 100."""
    weights = data.get("weights", {})
    total = sum(weights.values()) or 1
    return {k: 100 * w / total for k, w in weights.items()}


def shift_parts(parts, delta, full, order=None):
    """Move the parts by `delta` points in total, never past 0 or a part's full share.
    Points go in `order` when given, otherwise spread by each part's room (up) or size (down)."""
    parts = dict(parts)
    for _ in range(4):  # a part that hits its limit hands the rest to the others
        if abs(delta) < 0.05:
            break
        keys = [k for k in (order or parts) if k in parts]
        room = {k: (full.get(k, 100) - parts[k]) if delta > 0 else parts[k] for k in keys}
        room = {k: r for k, r in room.items() if r > 0}
        if not room:
            break
        if order:
            k = next(iter(room))
            step = min(abs(delta), room[k])
            parts[k] += step if delta > 0 else -step
            delta -= step if delta > 0 else -step
            continue
        total = sum(room.values())
        moved = 0
        for k, r in room.items():
            step = min(r, abs(delta) * r / total)
            parts[k] += step if delta > 0 else -step
            moved += step
        delta -= moved if delta > 0 else -moved
    return {k: round(v, 1) for k, v in parts.items()}


def apply_max_rank(data, ranked):
    """maxRank {id: lowest allowed rank}: an entry ranked below it is moved up to that rank, and it gets
    the smallest number of points that puts its index just above the entry under it, so the shown
    order still reads as index order. The points go to 애정 first, then 사용성, then 인기, each up to
    that part's full share."""
    for sid, worst in sorted(data.get("maxRank", {}).items(), key=lambda kv: kv[1]):
        pos = next((i for i, s in enumerate(ranked) if s["id"] == sid), None)
        if pos is None or pos < worst - 1:
            continue
        s = ranked.pop(pos)
        ranked.insert(worst - 1, s)
        below = ranked[worst]["index"] if worst < len(ranked) else None
        if below is None or s["index"] > below:
            continue
        need = round(below - s["index"] + 0.1, 1)
        if s.get("parts"):
            s["parts"] = shift_parts(s["parts"], need, full_shares(data), ("affection", "usability", "popularity"))
        s["index"] = round(sum(s["parts"].values()), 1) if s.get("parts") else round(below + 0.1, 1)
        s["score"] = f"{max(data.get('minScore', 0), s['index'] / 20):.1f}"
    return ranked


def weekly(data, start):
    """Ready entries for the week starting on `start`, with that week's adjustment, best first.

    Each week a few entries get an adjustment of up to ±max points. The draw is seeded by
    the week's Monday, so every build in the same week shows the same ranking.
    """
    cfg = data["weeklyAdjust"]
    ready = [dict(s) for s in data["webhards"] if s["status"] == "ready" and "index" in s]
    for s in ready:
        if s.get("parts"):
            s["index"] = round(sum(s["parts"].values()), 1)  # the shown parts always add up to the shown index
    rng = random.Random(start.isoformat())
    for s in rng.sample(ready, min(cfg["items"], len(ready))):
        new = round(min(100, max(0, s["index"] + rng.uniform(-cfg["max"], cfg["max"]))), 1)
        if s.get("parts") and s["index"]:
            # spread the adjustment over the parts so the chart's per-part scores still add up to the index
            s["parts"] = shift_parts(s["parts"], new - s["index"], full_shares(data))
            new = round(sum(s["parts"].values()), 1)  # rounded parts decide the index, so they always add up
        s["index"] = new
    for s in ready:
        s["score"] = f"{max(data.get('minScore', 0), s['index'] / 20):.1f}"
    return apply_max_rank(data, sorted(ready, key=lambda s: -s["index"]))
