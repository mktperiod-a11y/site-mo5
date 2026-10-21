"""Render the ranking from data/webhards.json into static HTML at deploy time.

Search engines and AI answer engines often read pages without running JavaScript,
so the cards, the side ranking, the chart, the summary sentence and the structured
data are written into the files here instead of being built in the browser.

Usage: python3 render_ranking.py <site_dir>
Fills {{...}} tokens and <!-- ranking:... --> markers in index.html, llms.txt and
sitemap.xml, and exits non-zero if any are left over.
"""
import html
import json
import random
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

site = Path(sys.argv[1])
data = json.loads((site / "data/webhards.json").read_text(encoding="utf-8"))
e = html.escape
today = datetime.now(timezone(timedelta(hours=9))).date()
week_start = today - timedelta(days=today.weekday())


def weekly(start):
    """Ready entries for the week starting on `start`, with that week's adjustment, best first.

    Each week a few entries get an adjustment of up to ±max points. The draw is seeded by
    the week's Monday, so every build in the same week shows the same ranking, and last
    week's ranking can be rebuilt to show the rank changes.
    """
    cfg = data["weeklyAdjust"]
    ready = [dict(s) for s in data["webhards"] if s["status"] == "ready" and "index" in s]
    rng = random.Random(start.isoformat())
    for s in rng.sample(ready, min(cfg["items"], len(ready))):
        new = round(min(100, max(0, s["index"] + rng.uniform(-cfg["max"], cfg["max"]))), 1)
        if s.get("parts") and s["index"]:
            # spread the adjustment over the parts so the chart segments still add up to the index
            s["parts"] = {k: round(v * new / s["index"], 1) for k, v in s["parts"].items()}
        s["index"] = new
    for s in ready:
        s["score"] = f"{s['index'] / 20:.1f}"
    return apply_max_rank(sorted(ready, key=lambda s: -s["index"]))


def apply_max_rank(ranked):
    """maxRank {id: lowest allowed rank}: an entry ranked below it is moved up to that rank."""
    for sid, worst in sorted(data.get("maxRank", {}).items(), key=lambda kv: kv[1]):
        pos = next((i for i, s in enumerate(ranked) if s["id"] == sid), None)
        if pos is not None and pos >= worst:
            ranked.insert(worst - 1, ranked.pop(pos))
    return ranked


ranked = weekly(week_start)
last_week = {s["id"]: i for i, s in enumerate(weekly(week_start - timedelta(days=7)))}
services = ranked[: data["rankLimit"]]
updated = max(date.fromisoformat(data["updated"]), week_start)


def move(i, s):
    """Rank change since last week: ▲ up, ▼ down, – same."""
    diff = last_week.get(s["id"], len(last_week)) - i
    if diff > 0:
        return f'<em class="mv up" aria-label="지난주보다 {diff}계단 상승">▲{diff}</em>'
    if diff < 0:
        return f'<em class="mv down" aria-label="지난주보다 {-diff}계단 하락">▼{-diff}</em>'
    return '<em class="mv same" aria-label="지난주와 같음">–</em>'



top = max(s["index"] for s in services)
metrics_date = date.fromisoformat(data["metricsDate"])


def stars(score):
    filled = round(float(score))
    return "★" * filled + "☆" * (5 - filled)


def card(i, s):
    tags = "".join(f"<i>{e(t)}</i>" for t in s["tags"].split())
    loading = "eager" if i < 3 else "lazy"
    return (
        f'<article class="card{" top" if i < 3 else ""}" style="--brand:{s["color"]}">'
        f'<span class="rank-flag">{i + 1}</span>'
        f'<div class="visual"><img src="{s["logo"]}" alt="{e(s["name"])} 로고" width="170" height="76" loading="{loading}"></div>'
        f'<div class="card-body"><h2>{e(s["name"])}{move(i, s)}</h2><p class="tags">{tags}</p>'
        f'<div class="reason"><b>선정이유</b><span>{e(s["reason"])}</span></div>'
        f'<div class="trust"><b>종합신뢰도</b><span class="stars" aria-hidden="true">{stars(s["score"])}</span>'
        f'<span class="score">{s["score"]}<small>/5</small></span></div>'
        f'<a class="go" href="go/{s["id"]}/" target="_blank" rel="noopener noreferrer sponsored nofollow" '
        f'aria-label="{e(s["name"])} 사이트 새 창으로 열기">사이트 바로가기 ›</a></div></article>'
    )


def live_row(i, s):
    grade = f" r{i + 1}" if i < 3 else ""
    return (
        f'<div class="live-row{grade}"><b>{i + 1}</b><div><span class="live-name">{e(s["name"])}{move(i, s)}</span>'
        f'<i class="live-bar" style="--w:{round(s["index"] / top * 100)}%"></i></div><small>{s["index"]}</small></div>'
    )


PARTS = (("popularity", "인기"), ("usability", "사용감"), ("affection", "애정"))


def bar(i, s):
    """One stacked bar: popularity, usability and affection points, adding up to the index."""
    parts = s.get("parts")
    if parts:
        segs = "".join(f'<i class="seg {k}" style="--p:{parts[k] / s["index"] * 100:.1f}%"></i>' for k, _ in PARTS)
        tip = " · ".join(f"{label} {parts[k]}" for k, label in PARTS)
    else:
        segs, tip = '<i class="seg all" style="--p:100%"></i>', f"모아온 지수 {s['index']}"
    return (
        f'<div class="bar" tabindex="0" style="--h:{round(s["index"] / top * 88)}%;--d:{i * 0.07:.2f}s" '
        f'data-name="{e(s["name"])}" aria-label="{e(s["name"])} 모아온 지수 {s["index"]}, {tip}">'
        f'<b data-v="{s["index"]}">{s["index"]}</b>{segs}<span class="tip" aria-hidden="true">{tip}</span></div>'
    )


names = [s["name"] for s in services]
# what the index is built from, for the summary, chart caption and notes
has_search = any(s.get("metrics", {}).get("search") for s in services)
basis = ("네이버 검색량과 " if has_search else "") + "구글 플레이 한국 스토어의 추정 다운로드·평점·평가 수"
summary = (
    f'{updated.year}년 {updated.month}월 기준 모아온 웹하드 순위 1위는 <b>{e(names[0])}</b>, '
    f"2위 {e(names[1])}, 3위 {e(names[2])}입니다. 순위는 {basis}를 "
    f'합산한 모아온 지수 순서이며, 계산 방식은 <a href="criteria.html#index">순위 검증 가이드</a>에서 확인할 수 있습니다.'
)
item_list = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": f"{updated.year}년 {updated.month}월 웹하드 순위 TOP {len(services)}",
    "itemListOrder": "https://schema.org/ItemListOrderAscending",
    "numberOfItems": len(services),
    "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": s["name"], "url": s["url"], "description": f"{s['reason']} (모아온 지수 {s['index']})"}
        for i, s in enumerate(services)
    ],
}
page = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": f"{updated.year}년 {updated.month}월 웹하드 순위 TOP {len(services)}",
    "url": "https://site-url.invalid/",
    "inLanguage": "ko-KR",
    "dateModified": updated.isoformat(),
    "isPartOf": {"@type": "WebSite", "name": "모아온", "url": "https://site-url.invalid/"},
}
jsonld = "".join(
    f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>' for d in (page, item_list)
)

tokens = {
    "{{updated_ym}}": f"{updated.year}년 {updated.month}월",
    "{{updated_date}}": f"{updated.year}년 {updated.month:02d}월 {updated.day:02d}일",
    "{{updated_iso}}": updated.isoformat(),
    "{{top3}}": "·".join(names[:3]),
    "{{count}}": str(len(services)),
    "{{metrics_date}}": f"{metrics_date.year}년 {metrics_date.month}월 {metrics_date.day}일",
    "{{metrics_basis}}": basis,
    "{{w_popularity}}": str(data["weights"]["popularity"]),
    "{{w_usability}}": str(data["weights"]["usability"]),
    "{{w_affection}}": str(data["weights"]["affection"]),
    "{{ranking_list}}": "\n".join(f"{i + 1}. {s['name']} (모아온 지수 {s['index']}): {s['reason']}" for i, s in enumerate(services)),
}
markers = {
    "cards": "".join(card(i, s) for i, s in enumerate(services)),
    "live": "".join(live_row(i, s) for i, s in enumerate(services[:5])),
    "chart": "".join(bar(i, s) for i, s in enumerate(services)),
    "summary": summary,
    "jsonld": jsonld,
}

failed = False
for name in ("index.html", "llms.txt", "sitemap.xml"):
    path = site / name
    text = path.read_text(encoding="utf-8")
    for key, value in tokens.items():
        text = text.replace(key, value)
    for key, value in markers.items():
        text = text.replace(f"<!-- ranking:{key} -->", value)
    left = re.findall(r"\{\{\w+\}\}|<!-- ranking:\w+ -->", text)
    if left:
        print(f"::error::{name}에 채우지 못한 자리가 남았습니다: {sorted(set(left))}")
        failed = True
    path.write_text(text, encoding="utf-8")
    print(f"{name}: 순위 {len(services)}개 반영")
sys.exit(1 if failed else 0)
