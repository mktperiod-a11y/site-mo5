"""Compute the 모아온 지수 from collected metrics and reorder the ranking.

Usage:
  python3 .github/scripts/score.py            recompute index/score and reorder data/webhards.json
  python3 .github/scripts/score.py --baseline save the current data as data/baseline.json (the default)
  python3 .github/scripts/score.py --restore  put data/baseline.json back as data/webhards.json

지수(0-100) = 인기 × w_popularity + 사용감 × w_usability + 애정 × w_affection (weights in data/webhards.json)
- 인기: 검색 수준(로그 척도, 70%) + 지난주 검색 변동 폭(30%)
  검색 수준은 월간 조회수(searchMonthly)가 모두 있으면 그것을, 없으면 최근 4주 상대 검색량(search)을 쓴다.
  변동 폭은 지난주 검색량이 그 전 4주 평균보다 늘거나 준 비율로, ±50%에서 자른다.
  검색 데이터가 하나도 없으면 인기 비중을 나머지에 비율대로 나눠 준다.
- 사용감: 추정 다운로드(로그 척도, 60%) + 보정 평점(40%)
- 애정: 평가 수(로그 척도), 좋은 평가든 나쁜 평가든 관심의 크기로 본다
보정 평점은 평가 수가 적을수록 전체 평균 쪽으로 당긴 값이다(베이즈 평균, prior 300건).
로그 척도는 모은 값의 가장 작은 값을 0, 가장 큰 값을 1로 둔다.
"""
import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/webhards.json"
BASELINE = ROOT / "data/baseline.json"
PRIOR = 300

if "--restore" in sys.argv:
    shutil.copyfile(BASELINE, DATA)
    print("data/baseline.json → data/webhards.json")
    sys.exit()

data = json.loads(DATA.read_text(encoding="utf-8"))
w = data["weights"]
rows = [s for s in data["webhards"] if s.get("metrics")]


def lognorm(key):
    vals = [math.log10(max(s["metrics"].get(key) or 0, 0.1)) for s in rows]
    lo, hi = min(vals), max(vals)
    return lambda v: (math.log10(max(v or 0, 0.1)) - lo) / (hi - lo) if hi > lo else 1.0


downloads = lognorm("downloads")
ratings = lognorm("ratingCount")
level_key = "searchMonthly" if all(s["metrics"].get("searchMonthly") for s in rows) else "search"
has_search = any(s["metrics"].get(level_key) for s in rows)
level = lognorm(level_key) if has_search else None
mean = sum(s["metrics"]["rating"] * s["metrics"]["ratingCount"] for s in rows) / sum(s["metrics"]["ratingCount"] for s in rows)

parts = {"usability": w["usability"], "affection": w["affection"], "popularity": w["popularity"] if has_search else 0}
total = sum(parts.values())
for s in rows:
    m = s["metrics"]
    rating = (m["ratingCount"] * m["rating"] + PRIOR * mean) / (m["ratingCount"] + PRIOR)
    usability = 0.6 * downloads(m["downloads"]) + 0.4 * (rating - 1) / 4
    affection = ratings(m["ratingCount"])
    change = max(-0.5, min(0.5, m.get("searchChange", 0)))
    popularity = 0.7 * level(m.get(level_key)) + 0.3 * (change + 0.5) if has_search else 0
    points = {
        "popularity": 100 * parts["popularity"] * popularity / total,
        "usability": 100 * parts["usability"] * usability / total,
        "affection": 100 * parts["affection"] * affection / total,
    }
    index = sum(points.values())
    s["index"] = round(index, 1)
    s["parts"] = {k: round(v, 1) for k, v in points.items()}
    s["score"] = f"{index / 20:.1f}"

# ready entries ranked by index; entries without metrics and pending ones keep their relative order after them
ranked = sorted(rows, key=lambda s: -s["index"])
# maxRank {id: lowest allowed rank}: an entry ranked below it is moved up to that rank
for sid, worst in sorted(data.get("maxRank", {}).items(), key=lambda kv: kv[1]):
    pos = next((i for i, s in enumerate(ranked) if s["id"] == sid), None)
    if pos is not None and pos >= worst:
        ranked.insert(worst - 1, ranked.pop(pos))
rest = [s for s in data["webhards"] if not s.get("metrics")]
data["webhards"] = ranked + rest
DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for i, s in enumerate(ranked, 1):
    print(f"{i:2} {s['name']} {s['index']}")

if "--baseline" in sys.argv:
    shutil.copyfile(DATA, BASELINE)
    print("data/webhards.json → data/baseline.json")
