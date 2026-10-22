"""Write last week's content rankings (data/contents.json) into content-guide.html at deploy time.

Usage: python3 .github/scripts/render_contents.py <site dir>

Fills {{contents_*}} tokens and the <!-- contents:... --> markers, so the lists are plain HTML
that crawlers read without running JavaScript. collect_contents.py refreshes the data every week.
"""
import json
import sys
from datetime import date
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
site = Path(sys.argv[1])
data = json.loads((ROOT / "data/contents.json").read_text(encoding="utf-8"))
KINDS = {"movie": "영화", "drama": "드라마", "variety": "예능·교양"}


def move(change):
    if change is None:
        return '<em class="mv new" aria-label="이번 주 새로 진입">NEW</em>'
    if change > 0:
        return f'<em class="mv up" aria-label="지난주보다 {change}계단 상승">▲{change}</em>'
    if change < 0:
        return f'<em class="mv down" aria-label="지난주보다 {-change}계단 하락">▼{-change}</em>'
    return '<em class="mv same" aria-label="지난주와 같음">–</em>'


def metric(kind, s):
    if kind == "movie":
        n = s["audience"]
        return f"관객 {n / 10000:.1f}만 명" if n >= 10000 else f"관객 {n:,}명"
    return f"시청률 {s['rating']:.1f}%"


def sub(kind, s):
    return f"{s['opened'].replace('-', '.')} 개봉" if kind == "movie" else f"{s['channel']} · {s['board']}"


def rows(kind):
    items = data.get(kind, {}).get("items", [])
    if not items:
        return '<li class="ct-empty">이번 주 자료를 아직 받지 못했어요.</li>'
    out = ""
    for i, s in enumerate(items, 1):
        ch = s.get("change")
        out += (
            f'\n              <li class="ct-row" data-kind="{kind}" data-title="{e(s["title"])}" data-sub="{e(sub(kind, s))}"'
            f' data-metric="{e(metric(kind, s))}" data-change="{"new" if ch is None else ch}">'
            f'<b class="ct-rank">{i}</b><span class="ct-name"><span class="ct-title">{e(s["title"])}</span>'
            f'<small>{e(sub(kind, s))}</small></span><span class="ct-metric">{metric(kind, s)}</span>{move(ch)}</li>'
        )
    return out + "\n            "


def tops():
    out = ""
    for kind, label in KINDS.items():
        items = data.get(kind, {}).get("items", [])
        if not items:
            continue
        s = items[0]
        out += (
            f'\n        <article class="ct-top {kind}"><span class="ct-chip">{label} 1위</span>'
            f'<b class="ct-top-title">{e(s["title"])}</b>'
            f'<span class="ct-top-meta">{metric(kind, s)}{move(s.get("change"))}</span>'
            f'<small>{e(sub(kind, s))}</small></article>'
        )
    return out + "\n      "


updated = date.fromisoformat(data["updated"]) if data.get("updated") else date.today()
period = next((data[k]["period"] for k in KINDS if data.get(k, {}).get("period")), "")
fills = {
    "{{contents_iso}}": updated.isoformat(),
    "{{contents_date}}": f"{updated.year}년 {updated.month}월 {updated.day}일",
    "{{contents_period}}": period,
    "<!-- contents:top -->": tops(),
    **{f"<!-- contents:{k} -->": rows(k) for k in KINDS},
}
page = site / "content-guide.html"
html = page.read_text(encoding="utf-8")
for key, value in fills.items():
    if key not in html:
        sys.exit(f"::error::content-guide.html에 {key} 자리가 없습니다.")
    html = html.replace(key, value)
page.write_text(html, encoding="utf-8")
# the sitemap dates the content guide by its last collection
sitemap = site / "sitemap.xml"
sitemap.write_text(sitemap.read_text(encoding="utf-8").replace("{{contents_iso}}", fills["{{contents_iso}}"]), encoding="utf-8")
print(f"콘텐츠 순위 채움: {period}")
