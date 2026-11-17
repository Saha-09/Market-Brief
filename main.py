"""
Daily market & deals brief -> Telegram.

Flow:
  1. Pull a set of free RSS feeds (config.py).
  2. Keep only items from the last LOOKBACK_HOURS, dedupe.
  3. Ask a free LLM (Groq) to turn them into a tight 1-page brief.
  4. Send it to you on Telegram.

Runs on GitHub Actions on a schedule. Costs nothing.
Required environment variables (set as GitHub repo secrets):
  GROQ_API_KEY        - from https://console.groq.com  (free)
  TELEGRAM_BOT_TOKEN  - from @BotFather on Telegram     (free)
  TELEGRAM_CHAT_ID    - your chat id (see get_chat_id.py)
Optional:
  GROQ_MODEL          - defaults to a current Groq model; override if it gets deprecated
"""

import os
import sys
import time
import datetime as dt
from email.utils import parsedate_to_datetime

import requests
import feedparser

from config import FEEDS, FOCUS, LOOKBACK_HOURS, MAX_ITEMS

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def _parse_date(entry):
    """Best-effort published time as an aware UTC datetime, or None."""
    for key in ("published", "updated"):
        val = entry.get(key)
        if not val:
            continue
        try:
            d = parsedate_to_datetime(val)
            if d.tzinfo is None:
                d = d.replace(tzinfo=dt.timezone.utc)
            return d.astimezone(dt.timezone.utc)
        except Exception:
            pass
    # feedparser also exposes a parsed struct_time
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return dt.datetime(*t[:6], tzinfo=dt.timezone.utc)
            except Exception:
                pass
    return None


def collect_items():
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=LOOKBACK_HOURS)
    seen_titles = set()
    items = []

    for category, name, url in FEEDS:
        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "market-brief/1.0"})
            feed = feedparser.parse(resp.content)
        except Exception as e:
            print(f"[warn] failed to fetch {name}: {e}", file=sys.stderr)
            continue

        for entry in feed.entries:
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            key = title.lower()
            if key in seen_titles:
                continue

            published = _parse_date(entry)
            # If a feed gives no date, keep it (better to include than silently drop).
            if published is not None and published < cutoff:
                continue

            seen_titles.add(key)
            summary = (entry.get("summary") or "").strip()
            # strip crude HTML
            for tag in ("<p>", "</p>", "<br>", "<br/>"):
                summary = summary.replace(tag, " ")
            items.append({
                "category": category,
                "source": name,
                "title": title,
                "summary": summary[:400],
                "link": entry.get("link", ""),
                "published": published,
            })

    # newest first, cap the count
    items.sort(key=lambda x: x["published"] or cutoff, reverse=True)
    return items[:MAX_ITEMS]


def build_raw_block(items):
    lines = []
    for it in items:
        when = it["published"].astimezone(IST).strftime("%d %b %H:%M") if it["published"] else "—"
        lines.append(f"[{it['category']}] ({it['source']}, {when}) {it['title']}")
        if it["summary"]:
            lines.append(f"    {it['summary']}")
    return "\n".join(lines)


def summarize(raw_block):
    """Call Groq (OpenAI-compatible) to produce the 1-page brief in HTML for Telegram."""
    today = dt.datetime.now(IST).strftime("%A, %d %B %Y")
    system = (
        "You are a sharp buy-side/sell-side research analyst writing a concise morning brief "
        "for a finance student preparing for investment-banking interviews and CFA Level 1."
    )
    user = f"""Today is {today}. Below are raw news headlines from the last day.

READER FOCUS:
{FOCUS}

Write a tight ONE-PAGE morning brief in Telegram-friendly HTML. Rules:
- Use only these HTML tags: <b>, <i>, <a href="...">. No markdown, no other tags.
- Keep the WHOLE message under 3500 characters.
- Structure with bold section headers (as <b>...</b>), each followed by 2-4 short bullet lines using the • character.
- Sections, in order: "📊 Markets Snapshot", "🤝 Deals & M&A", "🧾 IPOs (live + upcoming)", "🌐 Global", "🎯 What to focus on today".
- The final section is YOUR analysis: 2-3 lines on what matters most today and what an IB interviewer might ask about it. Be specific and opinionated, not generic.
- Attribute figures to sources only if present; never invent numbers. If a section has nothing, write "• Nothing notable."
- No preamble, no sign-off. Start directly with the first header.

RAW HEADLINES:
{raw_block}
"""

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.4,
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def send_telegram(html_text):
    """Telegram caps messages at 4096 chars; chunk if needed."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    chunks = []
    while html_text:
        chunk = html_text[:3800]
        # try not to split mid-line
        if len(html_text) > 3800:
            nl = chunk.rfind("\n")
            if nl > 2000:
                chunk = chunk[:nl]
        chunks.append(chunk)
        html_text = html_text[len(chunk):].lstrip("\n")

    for chunk in chunks:
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=30)
        if not r.ok:
            print(f"[error] telegram: {r.status_code} {r.text}", file=sys.stderr)
            r.raise_for_status()
        time.sleep(0.5)


def main():
    missing = [k for k in ("GROQ_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
               if not os.environ.get(k)]
    if missing:
        print(f"[fatal] missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    items = collect_items()
    print(f"[info] collected {len(items)} items")
    if not items:
        send_telegram("<b>Morning brief</b>\n• No fresh items pulled today — feeds may be quiet or blocked.")
        return

    brief = summarize(build_raw_block(items))
    header = dt.datetime.now(IST).strftime("🗞️ <b>Morning Brief — %d %b %Y</b>\n\n")
    send_telegram(header + brief)
    print("[info] sent.")


if __name__ == "__main__":
    main()
