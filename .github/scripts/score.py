"""Compute the 모아온 지수 from collected metrics and reorder the ranking.

Usage:
  python3 .github/scripts/score.py            recompute index/score and reorder data/webhards.json
  python3 .github/scripts/score.py --baseline save the current data as data/baseline.json (the default)
  python3 .github/scripts/score.py --restore  put data/baseline.json back as data/webhards.json

지수(0-100) = 사용감 × w_usability + 애정 × w_affection (+ 인기 × w_popularity once search data exists)
- 사용감: 추정 다운로드(로그 척도, 60%) + 보정 평점(40%)
- 애정: 평가 수(로그 척도), 좋은 평가든 나쁜 평가든 관심의 크기로 본다
- 인기: 네이버 검색량(로그 척도), 데이터가 없으면 그 비중을 나머지에 나눠 준다
보정 평점은 평가 수가 적을수록 전체 평균 쪽으로 당긴 값이다(베이즈 평균, prior 300건).
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
    vals = [math.log10(s["metrics"][key]) for s in rows]
    lo, hi = min(vals), max(vals)
    return lambda v: (math.log10(v) - lo) / (hi - lo) if hi > lo else 1.0


downloads = lognorm("downloads")
ratings = lognorm("ratingCount")
has_search = all(s["metrics"].get("searches") for s in rows)
searches = lognorm("searches") if has_search else None
mean = sum(s["metrics"]["rating"] * s["metrics"]["ratingCount"] for s in rows) / sum(s["metrics"]["ratingCount"] for s in rows)

parts = {"usability": w["usability"], "affection": w["affection"], "popularity": w["popularity"] if has_search else 0}
total = sum(parts.values())
for s in rows:
    m = s["metrics"]
    rating = (m["ratingCount"] * m["rating"] + PRIOR * mean) / (m["ratingCount"] + PRIOR)
    usability = 0.6 * downloads(m["downloads"]) + 0.4 * (rating - 1) / 4
    affection = ratings(m["ratingCount"])
    popularity = searches(m["searches"]) if has_search else 0
    index = 100 * (parts["usability"] * usability + parts["affection"] * affection + parts["popularity"] * popularity) / total
    s["index"] = round(index, 1)
    s["score"] = f"{index / 20:.1f}"

# ready entries ranked by index; entries without metrics and pending ones keep their relative order after them
ranked = sorted(rows, key=lambda s: -s["index"])
rest = [s for s in data["webhards"] if not s.get("metrics")]
data["webhards"] = ranked + rest
DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for i, s in enumerate(ranked, 1):
    print(f"{i:2} {s['name']} {s['index']}")

if "--baseline" in sys.argv:
    shutil.copyfile(DATA, BASELINE)
    print("data/webhards.json → data/baseline.json")
