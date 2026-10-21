"""Collect this week's metrics for every ranked webhard and recompute the 모아온 지수.

Usage: python3 .github/scripts/collect.py [--dry-run]

- Google Play (Korean store): estimated downloads, rating and rating count from each app's page.
- NAVER API HUB search trend: weekly search ratios for each name over the last 8 finished weeks.
  The API returns ratios relative to the largest group in one request (max 5 groups), so every
  request carries the same anchor name and the other names are scaled against it.
- NAVER 검색광고 keyword tool (optional, only when its keys are set): monthly PC + mobile searches.

Writes the metrics into data/webhards.json, appends them to data/metrics-history.json and runs
score.py. With --dry-run it only prints what it collected. Secrets come from the environment and
are never printed.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ranking import weekly

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/webhards.json"
HISTORY = ROOT / "data/metrics-history.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
DRY = "--dry-run" in sys.argv

data = json.loads(DATA.read_text(encoding="utf-8"))
rows = [s for s in data["webhards"] if s["status"] == "ready" and s.get("metrics")]
today = datetime.now(timezone(timedelta(hours=9))).date()


def fetch(url, body=None, headers=None):
    req = urllib.request.Request(url, data=body, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def play(app):
    page = fetch(f"https://play.google.com/store/apps/details?id={app}&hl=ko&gl=KR")
    ld = re.search(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', page, re.S)
    rating = json.loads(ld.group(1)).get("aggregateRating") if ld else None
    installs = re.search(r'\["[\d,.]+\+",(\d+),(\d+),"[^"]*"\]', page)
    if not rating or not installs:
        raise ValueError("page format changed")
    return {
        "downloads": int(installs.group(2)),
        "rating": round(float(rating["ratingValue"]), 2),
        "ratingCount": int(rating["ratingCount"]),
    }


def search_trend():
    """Per id: search level over the last 4 finished weeks (anchor = 100) and last week's change."""
    cid, secret = os.environ.get("NAVER_CLIENT_ID"), os.environ.get("NAVER_CLIENT_SECRET")
    if not (cid and secret):
        print("검색어 트렌드 키가 없어 검색량은 건너뜁니다.")
        return {}
    end = today - timedelta(days=today.weekday() + 1)  # last finished Sunday
    start = end - timedelta(weeks=8) + timedelta(days=1)
    anchor = next((s for s in rows if s["id"] == data.get("searchAnchor")), None)
    if anchor is None:
        print("::warning::searchAnchor 업체가 목록에 없어 검색량은 건너뜁니다.")
        return {}
    others = [s for s in rows if s is not anchor]
    words = lambda s: s.get("searchKeywords", [s["name"]])
    out = {}
    for i in range(0, len(others), 4):
        batch = [anchor] + others[i : i + 4]
        body = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "timeUnit": "week",
            "keywordGroups": [{"groupName": s["id"], "keywords": words(s)} for s in batch],
        }
        res = json.loads(fetch(
            "https://naverapihub.apigw.ntruss.com/search-trend/v1/search",
            json.dumps(body).encode(),
            {"X-NCP-APIGW-API-KEY-ID": cid, "X-NCP-APIGW-API-KEY": secret, "Content-Type": "application/json"},
        ))
        series = {g["title"]: [d["ratio"] for d in g["data"]] for g in res["results"]}
        base = sum(series[anchor["id"]][-4:]) or 1
        for s in batch:
            w = series.get(s["id"], [])
            prev = sum(w[-5:-1]) / 4 if len(w) >= 5 else 0
            out[s["id"]] = {
                "search": round(sum(w[-4:]) / base * 100, 2),
                "searchChange": round(w[-1] / prev - 1, 3) if prev else 0.0,
            }
    return out


def search_monthly():
    """Per id: monthly PC + mobile searches from the 검색광고 keyword tool, when its keys are set."""
    key, secret, customer = (os.environ.get(n) for n in ("NAVER_AD_API_KEY", "NAVER_AD_SECRET", "NAVER_AD_CUSTOMER_ID"))
    if not (key and secret and customer):
        return {}
    count = lambda v: 5 if isinstance(v, str) else int(v)  # "< 10" comes back as a string
    out = {}
    for i in range(0, len(rows), 5):
        batch = rows[i : i + 5]
        ts, uri = str(int(time.time() * 1000)), "/keywordstool"
        sig = base64.b64encode(hmac.new(secret.encode(), f"{ts}.GET.{uri}".encode(), hashlib.sha256).digest()).decode()
        q = urllib.parse.urlencode({"hintKeywords": ",".join(s["name"].replace(" ", "") for s in batch), "showDetail": 1})
        res = json.loads(fetch(f"https://api.searchad.naver.com{uri}?{q}", headers={
            "X-Timestamp": ts, "X-API-KEY": key, "X-Customer": customer, "X-Signature": sig}))
        found = {k["relKeyword"]: k for k in res.get("keywordList", [])}
        for s in batch:
            k = found.get(s["name"].replace(" ", ""))
            if k:
                out[s["id"]] = count(k["monthlyPcQcCnt"]) + count(k["monthlyMobileQcCnt"])
    return out


# remember the ranks the page showed during the week that is ending, for next week's ▲▼
# (on the Monday run that is the week before; on a manual run mid-week it is the current week)
monday = today - timedelta(days=today.weekday())
shown_week = monday - timedelta(days=7) if today.weekday() == 0 else monday
previous = {"week": shown_week.isoformat(), "ranks": {s["id"]: i for i, s in enumerate(weekly(data, shown_week))}}

failed = []
for s in rows:
    try:
        s["metrics"].update(play(s["metrics"]["playApp"]))
    except (OSError, ValueError, KeyError) as e:  # OSError covers URLError, HTTPError and timeouts
        failed.append(s["name"])
        print(f"::warning::{s['name']} 구글 플레이 수집 실패({type(e).__name__}), 지난 값을 씁니다.")
for source in (search_trend, search_monthly):
    try:
        for sid, value in source().items():
            m = next(s for s in rows if s["id"] == sid)["metrics"]
            m.update(value if isinstance(value, dict) else {"searchMonthly": value})
    except (OSError, ValueError, KeyError) as e:
        print(f"::warning::{source.__name__} 수집 실패({type(e).__name__}), 지난 값을 씁니다.")

for s in rows:
    m = s["metrics"]
    print(f"{s['name']:6} 다운로드 {m['downloads']:>9,} 평점 {m['rating']} 평가 {m['ratingCount']:>6,} "
          f"검색 {m.get('search', '-')} 변동 {m.get('searchChange', '-')} 월간 {m.get('searchMonthly', '-')}")
if DRY:
    sys.exit()

if len(failed) == len(rows):
    sys.exit("::error::구글 플레이 수집이 모두 실패해 이번 주 값을 저장하지 않습니다.")
data["metricsDate"] = data["updated"] = today.isoformat()
data["previousRanks"] = previous
DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
history = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else {}
history[today.isoformat()] = {s["id"]: {k: v for k, v in s["metrics"].items() if k != "playApp"} for s in rows}
history = dict(sorted(history.items())[-26:])  # about half a year of weeks
HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
subprocess.run([sys.executable, str(ROOT / ".github/scripts/score.py")], check=True)
