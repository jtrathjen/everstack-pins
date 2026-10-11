#!/usr/bin/env python3
"""Build one RSS 2.0 feed per board from pins.json for Pinterest auto-publish.

Only pins whose publish_after date (America/Chicago) has arrived go in, so the daily run drips
them out one per board per day. Output goes to _site/, which the workflow deploys to GitHub Pages.
Plain RSS 2.0 with one <enclosure> image per item: the format Pinterest documents for auto-publish.
Every item links to everstackstudio.com, the website claimed on the Pinterest account."""
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html import escape as html_escape
from pathlib import Path
from xml.sax.saxutils import escape

BASE = "https://jtrathjen.github.io/everstack-pins"
SITE = "https://everstackstudio.com"
MAX_ITEMS = 50  # newest due pins per feed; Pinterest only makes Pins from items it hasn't seen

try:
    from zoneinfo import ZoneInfo
    CHI = ZoneInfo("America/Chicago")
except Exception:
    CHI = timezone(timedelta(hours=-5))

now = datetime.now(CHI)
today = now.date().isoformat()
data = json.loads(Path("pins.json").read_text())

problems = []
for p in data["pins"]:
    if not p["link"].startswith(SITE + "/"):
        problems.append(f"{p['id']}: the link must be on everstackstudio.com")
    if p["board"] not in data["boards"]:
        problems.append(f"{p['id']}: unknown board {p['board']}")
    if not (Path("pins") / f"{p['id']}.png").exists():
        problems.append(f"{p['id']}: image missing")
if problems:
    for line in problems:
        print(f"::error title=Pin feed problem::{line}")
    sys.exit(1)

out = Path("_site")
shutil.rmtree(out, ignore_errors=True)
(out / "pins").mkdir(parents=True)

summary = []
for board, name in data["boards"].items():
    mine = [p for p in data["pins"] if p["board"] == board]
    due = sorted((p for p in mine if p["publish_after"] <= today), key=lambda p: p["publish_after"], reverse=True)
    due = due[:MAX_ITEMS]
    rows = []
    for p in due:
        img = Path("pins") / f"{p['id']}.png"
        shutil.copy(img, out / "pins" / img.name)
        when = datetime.fromisoformat(p["publish_after"]).replace(hour=9, tzinfo=CHI)
        rows.append(f"""  <item>
   <title>{escape(p['title'])}</title>
   <link>{escape(p['link'])}</link>
   <description>{escape(p['description'])}</description>
   <guid isPermaLink="false">everstack-{escape(p['id'])}</guid>
   <pubDate>{format_datetime(when)}</pubDate>
   <enclosure url="{BASE}/pins/{img.name}" length="{img.stat().st_size}" type="image/png"/>
  </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
 <channel>
  <title>Everstack Studio: {escape(name)}</title>
  <link>{SITE}</link>
  <description>Pins from Everstack Studio for the board {escape(name)}</description>
  <language>en-us</language>
  <lastBuildDate>{format_datetime(now)}</lastBuildDate>
{chr(10).join(rows)}
 </channel>
</rss>
"""
    ET.fromstring(feed.encode())  # fail the build rather than publish broken XML
    (out / f"{board}.xml").write_text(feed)
    queued = sorted(p["publish_after"] for p in mine if p["publish_after"] > today)
    summary.append((board, name, len(due), len(mine), queued[0] if queued else ""))
    print(f"{board}: {len(due)} in feed, {len(queued)} queued")

lines = "".join(
    f'<li><a href="{board}.xml">{html_escape(name)}</a>: {n} pin{"" if n == 1 else "s"} in the feed'
    + (f", next one {html_escape(nxt)}" if nxt else "") + "</li>"
    for board, name, n, _total, nxt in summary)
(out / "index.html").write_text(
    '<!doctype html><html lang="en"><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Everstack Studio pin feeds</title>'
    '<body style="font:16px/1.5 system-ui,sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem">'
    '<h1 style="font-size:1.4rem">Everstack Studio pin feeds</h1>'
    f'<p>RSS feeds Pinterest reads for <a href="{SITE}">Everstack Studio</a>.</p><ul>{lines}</ul>'
    f'<p style="color:#6E6A63">Built {html_escape(now.strftime("%Y-%m-%d %H:%M %Z"))}.</p></body></html>\n')

note = ", ".join(f"{board}.xml {n} in feed (of {total})" for board, _name, n, total, _nxt in summary)
print(f"::notice title=Pin feeds built {today}::{note}")
if os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write(f"### Pin feeds built {today}\n\n{note}\n")
