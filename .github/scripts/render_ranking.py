"""Render the ranking from data/webhards.json into static HTML at deploy time.

Search engines and AI answer engines often read pages without running JavaScript,
so the cards, the side ranking, the chart, the summary sentence and the structured
data are written into the files here instead of being built in the browser.

Usage: python3 render_ranking.py <site_dir>
Fills {{...}} tokens and <!-- ranking:... --> markers in index.html, llms.txt and
sitemap.xml, and exits non-zero if any are left over.
"""
import base64
import html
import json
import random
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from ranking import weekly

site = Path(sys.argv[1])
data = json.loads((site / "data/webhards.json").read_text(encoding="utf-8"))
e = html.escape
today = datetime.now(timezone(timedelta(hours=9))).date()
week_start = today - timedelta(days=today.weekday())


ranked = weekly(data, week_start)
# ranks shown last week: saved by collect.py before it replaced the metrics; otherwise rebuilt from this data
prev_start = week_start - timedelta(days=7)
if data.get("previousRanks", {}).get("week") == prev_start.isoformat():
    last_week = data["previousRanks"]["ranks"]
else:
    last_week = {s["id"]: i for i, s in enumerate(weekly(data, prev_start))}
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
        f'<article class="card{" top" if i < 3 else ""}">'
        f'<span class="rank-flag">{i + 1}</span>'
        f'<div class="visual"><img src="{s["logo"]}" alt="{e(s["name"])} 로고" width="170" height="76" loading="{loading}"></div>'
        f'<div class="card-body"><h2><a href="webhard/{s["id"]}/">{e(s["name"])}</a>{move(i, s)}</h2><p class="tags">{tags}</p>'
        f'<div class="reason"><b>선정이유</b><span>{e(s["reason"])}</span></div>'
        f'<div class="trust"><b>종합신뢰도</b><span class="stars" aria-hidden="true">{stars(s["score"])}</span>'
        f'<span class="score">{s["score"]}<small>/5</small></span></div>'
        f'<button type="button" class="go" data-go="{s["id"]}" data-detail '
        f'aria-label="{e(s["name"])} 사이트 새 창으로 열기">사이트 바로가기 ›</button></div></article>'
    )


def live_row(i, s):
    grade = f" r{i + 1}" if i < 3 else ""
    return (
        f'<div class="live-row{grade}"><b>{i + 1}</b><div><span class="live-name">{e(s["name"])}{move(i, s)}</span>'
        f'<i class="live-bar" style="--w:{round(s["index"] / top * 100)}%"></i></div><small>{s["index"]}</small></div>'
    )


PARTS = (("popularity", "인기"), ("usability", "사용성"), ("affection", "애정"))


def bar(i, s):
    """One pastel bar per service; hovering shows that service's three scales, each against its own maximum."""
    parts, w = s.get("parts"), data["weights"]
    if parts:
        total = sum(w.values())
        rows = "".join(
            f'<span class="scale"><span>{label}</span><i style="--v:{min(100, parts[k] / (100 * w[k] / total) * 100):.0f}%"></i>'
            f'<em>{parts[k]}</em></span>'
            for k, label in PARTS
        )
        detail = ", ".join(f"{label} {parts[k]}" for k, label in PARTS)
    else:
        rows, detail = "", ""
    return (
        f'<div class="bar" tabindex="0" style="--h:{round(s["index"] / top * 88)}%;--c:{s["color"]};--d:{i * 0.07:.2f}s" '
        f'data-name="{e(s["name"])}" aria-label="{e(s["name"])} 모아온 지수 {s["index"]}{", " + detail if detail else ""}">'
        f'<b data-v="{s["index"]}">{s["index"]}</b>'
        f'<span class="tip" aria-hidden="true"><strong>{e(s["name"])} {s["index"]}</strong>{rows}</span></div>'
    )


names = [s["name"] for s in services]
# what the index is built from, for the summary, chart caption and notes
has_search = any(s.get("metrics", {}).get("search") for s in services)
basis = ("네이버 검색 관심도와 " if has_search else "") + "구글 플레이 공개 지표"
summary = (
    f'현재 모아온 웹하드 순위 1위는 <b>{e(names[0])}</b>, '
    f"2위 {e(names[1])}, 3위 {e(names[2])}입니다.<br>순위는 {basis}를 "
    f'종합한 모아온 지수 순서이며,<br>산정 기준은 <a href="criteria.html#index">순위 검증 가이드</a>에서 확인할 수 있습니다.'
)
item_list = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": f"{updated.year}년 {updated.month}월 웹하드 순위 TOP {len(services)}",
    "itemListOrder": "https://schema.org/ItemListOrderAscending",
    "numberOfItems": len(services),
    "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": s["name"], "url": f"https://site-url.invalid/webhard/{s['id']}/", "description": f"{s['reason']} (모아온 지수 {s['index']})"}
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
# "</" is escaped so text from the data can never close the script tag early
jsonld = "".join(
    '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    for d in (page, item_list)
)

tokens = {
    "{{updated_ym}}": f"{updated.year}년 {updated.month}월",
    "{{this_month}}": f"{today.month}월",
    "{{updated_date}}": f"{updated.year}년 {updated.month:02d}월 {updated.day:02d}일",
    "{{updated_iso}}": updated.isoformat(),
    "{{top3}}": "·".join(names[:3]),
    "{{count}}": str(len(services)),
    "{{metrics_date}}": f"{metrics_date.year}년 {metrics_date.month}월 {metrics_date.day}일",
    "{{metrics_short}}": metrics_date.strftime("%Y.%m.%d"),
    "{{metrics_iso}}": metrics_date.isoformat(),
    "{{metrics_basis}}": basis,
    "{{w_popularity}}": str(data["weights"]["popularity"]),
    "{{w_usability}}": str(data["weights"]["usability"]),
    "{{w_affection}}": str(data["weights"]["affection"]),
    "{{detail_links}}": "\n".join(
        f"- [{s['name']}](https://site-url.invalid/webhard/{s['id']}/): 모아온 지수·가입 혜택" for s in ranked
    ),
    "{{ranking_list}}": "\n".join(f"{i + 1}. {s['name']} (모아온 지수 {s['index']}): {s['reason']}" for i, s in enumerate(services)),
}
def benefit_rows():
    """Home side box: every benefit of this week's top services, one row each. The page script shows five services
    with one of their lines, a new draw on every load; without the script the first draw below stays visible."""
    rng = random.Random(today.isoformat())
    pool = [s for s in services if s.get("benefits")]
    shown = {s["id"] for s in rng.sample(pool, min(5, len(pool)))}
    rows, used = "", set()
    for s in pool:
        for b in s["benefits"]:
            first = s["id"] in shown and s["id"] not in used
            used |= {s["id"]} if first else set()
            rows += (f'\n            <li data-id="{s["id"]}"{"" if first else " hidden"}><a href="webhard/{s["id"]}/">{e(s["name"])}</a>'
                     f'<b title="{e(b["text"])}">{e(b["text"])}</b></li>')
    return rows + "\n          "


markers = {
    "cards": "".join(card(i, s) for i, s in enumerate(services)),
    "live": "".join(live_row(i, s) for i, s in enumerate(services[:5])),
    "chart": "".join(bar(i, s) for i, s in enumerate(services)),
    "summary": summary,
    "benefits": benefit_rows(),
    "jsonld": jsonld,
    "sitemap_details": "\n".join(
        f"<url><loc>https://site-url.invalid/webhard/{s['id']}/</loc><lastmod>{updated.isoformat()}</lastmod></url>" for s in ranked
    ),
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


# ---- one detail page per ranked service: webhard/<id>/index.html
TEMPLATE = (Path(__file__).resolve().parents[1] / "templates/webhard.html").read_text(encoding="utf-8")
weights_total = sum(data["weights"].values())


def scales(s):
    if not s.get("parts"):
        return ""
    out = ""
    for k, label in PARTS:
        full = 100 * data["weights"][k] / weights_total
        out += (f'<span class="scale"><span>{label}</span><i style="--v:{min(100, s["parts"][k] / full * 100):.0f}%"></i>'
                f'<em>{s["parts"][k]}</em></span>')
    return out


def benefit(s, kind):
    """One benefit panel: the service's sign-up benefits or events, filled in by hand in data/webhards.json."""
    items = [b["text"] for b in s.get("benefits", []) if b["kind"] == kind]
    if not items:
        return '<p class="benefit-empty">공식 사이트에서 확인하세요.</p>'
    rows = "".join(f"<li>{e(t)}</li>" for t in items)
    return f'<ul class="benefit-list">{rows}</ul>'


def icon(x):
    """App icon when assets/app/<id>.webp exists, otherwise the wordmark logo in the same rounded tile."""
    if (site / "assets/app" / f"{x['id']}.webp").exists():
        return f'<img src="../../assets/app/{x["id"]}.webp" alt="" width="44" height="44" loading="lazy" />'
    return f'<img class="wordmark" src="../../{x["logo"]}" alt="" width="44" height="44" loading="lazy" />'


def other_row(x):
    """A linked row: icon, name and one-line reason. No rank numbers."""
    return (
        f'\n          <a class="other-row" href="../{x["id"]}/"><span class="other-icon">{icon(x)}</span>'
        f'<span class="other-text"><b>{e(x["name"])}</b><small>{e(x["reason"])}</small></span></a>'
    )


for i, s in enumerate(ranked):
    # five other services from this week's ranking, a different mix per page and per week
    pool = [x for x in services if x["id"] != s["id"]]
    others = random.Random(f"{week_start.isoformat()}-{s['id']}").sample(pool, min(5, len(pool)))
    page_ld = [
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "모아온", "item": "https://site-url.invalid/"},
            {"@type": "ListItem", "position": 2, "name": s["name"], "item": f"https://site-url.invalid/webhard/{s['id']}/"}]},
        {"@context": "https://schema.org", "@type": "WebPage", "name": f"{s['name']} 순위·가입 혜택 정보",
         "url": f"https://site-url.invalid/webhard/{s['id']}/", "inLanguage": "ko-KR", "dateModified": updated.isoformat()},
    ]
    fill = {
        "{{root}}": "../../",
        "{{id}}": s["id"],
        "{{name}}": e(s["name"]),
        "{{reason}}": e(s["reason"]),
        "{{logo}}": s["logo"],
        "{{rank}}": str(i + 1),
        "{{total}}": str(len(ranked)),
        "{{move}}": move(i, s),
        "{{index}}": str(s["index"]),
        "{{score}}": s["score"],
        "{{stars}}": stars(s["score"]),
        "{{tags}}": "".join(f"<i>{e(t)}</i>" for t in s["tags"].split()),
        "{{scales}}": scales(s),
        "{{benefit_join}}": benefit(s, "join"),
        "{{benefit_event}}": benefit(s, "event"),
        "{{metrics_short}}": metrics_date.strftime("%Y.%m.%d"),
        "{{metrics_basis}}": basis,
        "{{updated_ym}}": f"{updated.year}년 {updated.month}월",
        "{{description}}": e(f"{s['name']} {updated.year}년 {updated.month}월 모아온 지수 {s['index']}·{i + 1}위. "
                             f"{s['reason']}. 모아온 지수 구성과 가입 혜택을 한눈에 확인하세요."),
        "{{jsonld}}": "".join('<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
                              + "</script>" for d in page_ld),
        "{{others}}": "".join(other_row(x) for x in others),
    }
    text = TEMPLATE
    for key, value in fill.items():
        text = text.replace(key, value)
    left = re.findall(r"\{\{\w+\}\}", text)
    if left:
        print(f"::error::webhard/{s['id']}에 채우지 못한 자리가 남았습니다: {sorted(set(left))}")
        failed = True
    out = site / "webhard" / s["id"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(text, encoding="utf-8")
print(f"webhard/: 상세 페이지 {len(ranked)}개")

# ---- go/<id>/: the page "사이트 바로가기" opens. The official address is only in data/webhards.json; here it is
# stored base64-encoded and reversed, so the page source and developer tools show no plain address.
GO = """<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <meta name="robots" content="noindex,nofollow" />
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'" />
    <title>{name}(으)로 이동 중 | 모아온</title>
  </head>
  <body>
    <p>{name} 공식 사이트로 이동 중입니다.</p>
    <noscript><p>이동하려면 브라우저의 자바스크립트를 켜 주세요.</p></noscript>
    <script>location.replace(atob("{code}".split("").reverse().join("")));</script>
  </body>
</html>
"""
gone = 0
for s in data["webhards"]:
    if s["status"] != "ready" or not s.get("url"):
        continue
    code = base64.b64encode(s["url"].encode()).decode()[::-1]
    out = site / "go" / s["id"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(GO.format(name=e(s["name"]), code=code), encoding="utf-8")
    gone += 1
print(f"go/: 이동 페이지 {gone}개")
sys.exit(1 if failed else 0)
