"""Remove developer comments from the built site so page source and DevTools show no internal notes.

Usage: python3 strip_comments.py <site_dir>
- .css: every /* ... */ block
- .js and inline <script> in .html (not JSON-LD): whole-line // comments
- .html: <!-- ... --> comments
The repository keeps the comments; only the published copy is cleaned.
"""
import re
import sys
from pathlib import Path

site = Path(sys.argv[1])
LINE_COMMENT = re.compile(r"^[ \t]*//.*\n", re.M)


def clean_js(code):
    return LINE_COMMENT.sub("", code)


def clean_script(match):
    tag, body = match.group(1), match.group(2)
    if "application/ld+json" in tag:
        return match.group(0)
    return f"{tag}{clean_js(body)}</script>"


count = 0
for path in site.rglob("*"):
    if path.suffix not in (".css", ".js", ".html"):
        continue
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".css":
        new = re.sub(r"/\*.*?\*/\n?", "", text, flags=re.S)
    elif path.suffix == ".js":
        new = clean_js(text)
    else:
        new = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        new = re.sub(r"(<script\b[^>]*>)(.*?)</script>", clean_script, new, flags=re.S)
    if new != text:
        path.write_text(new, encoding="utf-8")
        count += 1
print(f"주석 정리: 파일 {count}개")
