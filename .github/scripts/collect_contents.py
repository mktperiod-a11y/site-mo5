"""Collect last week's most watched movies, dramas and shows for the content guide.

Usage: python3 .github/scripts/collect_contents.py [--dry-run]

- Movies: KOBIS (영화관입장권통합전산망) weekly box office page, Monday to Sunday, by audience.
- TV: Nielsen Korea weekly household ratings, terrestrial TOP 20 + general programming and cable TOP 10.
  News and sports are left out; the rest is split into dramas and "예능·교양" by the title.

Both are public pages that need no key. Each source keeps last week's values when it fails.
Writes data/contents.json (only the top TOP_N of each list). With --dry-run it only prints.
"""
import html
import http.cookiejar
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/contents.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
DRY = "--dry-run" in sys.argv
TOP_N = 5

KOBIS = "https://www.kobis.or.kr/kobis/business/stat/boxs/findWeeklyBoxOfficeList.do"
NIELSEN = "https://www.nielsenkorea.co.kr/tv_terrestrial_day.asp?menu=Tit_1&sub_menu={}_2&area=00"
NIELSEN_BOARDS = {"1": "지상파", "2": "종편", "3": "케이블"}

SKIP = re.compile(r"뉴스|NEWS|news|KBO|리그|스포츠|중계|축구|야구|배구|농구|골프|올림픽|월드컵|아시안게임|특보|날씨")
# OTT originals shown on TV (티빙오리지널 ...) are dramas in practice
DRAMA = re.compile(r"드라마|특별기획|미니시리즈|연속극|일일극|주말극|오리지널")
# labels a channel puts in front of a title: channel name, slot ("금토드라마"), "티빙오리지널" ...
PREFIX = re.compile(
    r"^(?:(?:KBS1|KBS2|KBS|MBC|SBS|TVN|tvN|JTBC|ENA|MBN|TV ?CHOSUN|채널A)?"
    r"(?:특별기획|(?:월화|수목|금토|토일|주말|일일|아침|저녁)?(?:드라마|미니시리즈|연속극)))?"
    r"(?:티빙오리지널|넷플릭스오리지널|디즈니\+오리지널)?"
)

data = json.loads(DATA.read_text(encoding="utf-8"))
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def fetch(url, form=None):
    body = urllib.parse.urlencode(form).encode() if form else None
    req = urllib.request.Request(url, data=body, headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9", "Referer": url})
    with opener.open(req, timeout=30) as r:
        raw = r.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949", "replace")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def rows(table_html):
    return [[text(td) for td in re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)] for tr in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", table_html)]


def movies():
    """Last finished Monday-Sunday week; if KOBIS has not closed it yet, the week before."""
    page = fetch(KOBIS)
    token = re.search(r'name="CSRFToken"\s+value="([^"]*)"', page)
    today = datetime.now(timezone(timedelta(hours=9))).date()
    for back in (1, 2):
        start = today - timedelta(days=today.weekday() + 7 * back)
        end = start + timedelta(days=6)
        res = fetch(KOBIS, {
            "CSRFToken": token.group(1) if token else "", "loadEnd": "0", "searchType": "search",
            "startYMD": start.strftime("%Y%m%d"), "endYMD": end.strftime("%Y%m%d"), "sWeekGb": "0",
            "sMultiMovieYn": "", "sRepNationCd": "", "sWideAreaCd": "",
        })
        body = res[res.find('<tbody id="tbody_0"'):]
        body = body[: body.find("</tbody>")]
        items = []
        for tr in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", body):
            tds = re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)
            title = re.search(r'title="([^"]+)"', tds[1]) if len(tds) > 9 else None
            if not title:
                continue
            if "ico_new" in tds[1] or "신규" in tds[1]:
                change = None
            else:
                step = re.search(r"ico_(rise|fall)\">(\d+)", tds[1])
                change = (int(step.group(2)) * (1 if step.group(1) == "rise" else -1)) if step else 0
            items.append({
                "title": html.unescape(title.group(1)).strip(),
                "opened": text(tds[2]),
                "audience": int(text(tds[7]).replace(",", "") or 0),
                "change": change,
            })
        if items:
            return {"period": f"{start:%Y.%m.%d} ~ {end:%Y.%m.%d}", "items": items[:TOP_N]}
    raise ValueError("no box office rows")


def clean(program):
    inner = re.search(r"\(([^()]+)\)\s*$", program)
    name = inner.group(1) if inner and DRAMA.search(program) else program
    name = PREFIX.sub("", name) or name
    name = re.sub(r"-?\d+부$", "", name).strip()
    return data.get("names", {}).get(name, name)


def tv():
    """Latest published week of all three boards, merged and sorted by household rating."""
    shows, period = {}, None
    for board, label in NIELSEN_BOARDS.items():
        page = fetch(NIELSEN.format(board))
        week = re.search(r"(\d{4}\.\d{2}\.\d{2}) ~ (\d{4}\.\d{2}\.\d{2})", text(page))
        if week:
            period = period or f"{week.group(1)} ~ {week.group(2)}"
        # the first table on the page is household ratings; the viewer counts follow it
        part = page[page.find("가구시청률"): page.find("시청자수 TOP")]
        for cells in rows(part):
            if len(cells) != 4 or not cells[0].isdigit():
                continue
            channel, program = cells[1], cells[2]
            try:
                rating = float(cells[3])
            except ValueError:
                continue
            if SKIP.search(program):
                continue
            name = clean(program)
            kind = data.get("genres", {}).get(name) or ("drama" if DRAMA.search(program) else "variety")
            if name not in shows or shows[name]["rating"] < rating:
                shows[name] = {"title": name, "channel": channel, "rating": rating, "board": label, "kind": kind}
    if not shows:
        raise ValueError("no rating rows")
    ranked = sorted(shows.values(), key=lambda s: -s["rating"])
    return {kind: {"period": period, "items": [s for s in ranked if s["kind"] == kind][:TOP_N]} for kind in ("drama", "variety")}


def with_change(new, old):
    """Rank change against last week's list by title; None marks a newcomer (no marks on the very first run)."""
    before = {s["title"]: i for i, s in enumerate((old or {}).get("items", []))}
    for i, s in enumerate(new["items"]):
        s["change"] = (before[s["title"]] - i if s["title"] in before else None) if before else 0
        s.pop("kind", None)
    return new


failed = []
try:
    data["movie"] = movies()
except (OSError, ValueError, KeyError, IndexError) as e:  # OSError covers URLError, HTTPError and timeouts
    failed.append("movie")
    print(f"::warning::박스오피스 수집 실패({type(e).__name__}), 지난 값을 씁니다.")
try:
    lists = tv()
    for kind in ("drama", "variety"):
        if lists[kind]["period"] != data.get(kind, {}).get("period"):
            data[kind] = with_change(lists[kind], data.get(kind))
except (OSError, ValueError, KeyError, IndexError) as e:
    failed.append("tv")
    print(f"::warning::시청률 수집 실패({type(e).__name__}), 지난 값을 씁니다.")

for kind in ("movie", "drama", "variety"):
    block = data.get(kind, {})
    print(kind, block.get("period"))
    for i, s in enumerate(block.get("items", []), 1):
        print(f"  {i}. {s['title']}  {s.get('audience') or s.get('rating')}  {s.get('change')}")
if DRY:
    sys.exit()
if len(failed) == 2:
    sys.exit("::error::콘텐츠 순위를 하나도 가져오지 못해 저장하지 않습니다.")
data["updated"] = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
