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
import re
import sys
from datetime import date
from pathlib import Path

site = Path(sys.argv[1])
data = json.loads((site / "data/webhards.json").read_text(encoding="utf-8"))
services = [s for s in data["webhards"] if s["status"] == "ready"][: data["rankLimit"]]
updated = date.fromisoformat(data["updated"])
e = html.escape


def clicks(s):
    return float(re.match(r"[\d.]+", s["click"]).group())


top = max(clicks(s) for s in services)


def card(i, s):
    tags = "".join(f"<i>{e(t)}</i>" for t in s["tags"].split())
    loading = "eager" if i < 3 else "lazy"
    return (
        f'<article class="card{" top" if i < 3 else ""}" style="--brand:{s["color"]}">'
        f'<span class="rank-flag">{i + 1}</span>'
        f'<div class="visual"><img src="{s["logo"]}" alt="{e(s["name"])} 로고" width="170" height="76" loading="{loading}"></div>'
        f'<div class="card-body"><h2>{e(s["name"])}</h2><p class="tags">{tags}</p>'
        f'<div class="reason"><b>선정이유</b><span>{e(s["reason"])}</span></div>'
        f'<div class="trust"><b>종합신뢰도</b><span class="stars">★★★★★</span>'
        f'<span class="score">{s["score"]}<small>/5</small></span></div>'
        f'<a class="go" href="go/{s["id"]}/" target="_blank" rel="noopener noreferrer sponsored nofollow" '
        f'aria-label="{e(s["name"])} 사이트 새 창으로 열기">사이트 바로가기 ›</a></div></article>'
    )


def live_row(i, s):
    grade = f" r{i + 1}" if i < 3 else ""
    return (
        f'<div class="live-row{grade}"><b>{i + 1}</b><div><span class="live-name">{e(s["name"])}</span>'
        f'<i class="live-bar" style="--w:{round(clicks(s) / top * 100)}%"></i></div><small>{s["click"]}</small></div>'
    )


def bar(i, s):
    return (
        f'<div class="bar" tabindex="0" style="--h:{round(clicks(s) / top * 88)}%;--c:{s["color"]};--d:{i * 0.07:.2f}s" '
        f'data-name="{e(s["name"])}" aria-label="{e(s["name"])} {s["click"]}"><b data-v="{s["click"]}">{s["click"]}</b></div>'
    )


names = [s["name"] for s in services]
summary = (
    f'{updated.year}년 {updated.month}월 기준 모아온 웹하드 순위 1위는 <b>{e(names[0])}</b>, '
    f"2위 {e(names[1])}, 3위 {e(names[2])}입니다. 순위는 운영 안정성·혜택의 명확성·이용 편의성·결제 안내 "
    f'네 가지 기준을 바탕으로 정한 편집 순위이며, 기준은 <a href="criteria.html">순위 검증 가이드</a>에서 확인할 수 있습니다.'
)
item_list = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": f"{updated.year}년 {updated.month}월 웹하드 순위 TOP {len(services)}",
    "itemListOrder": "https://schema.org/ItemListOrderAscending",
    "numberOfItems": len(services),
    "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": s["name"], "url": s["url"], "description": s["reason"]}
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
    "{{ranking_list}}": "\n".join(f"{i + 1}. {s['name']}: {s['reason']}" for i, s in enumerate(services)),
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
