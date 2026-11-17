# Daily Market Brief → Telegram

A free, zero-cost morning brief on markets, M&A/deals, IPOs, and "what to focus on today."
Pulls public RSS feeds, summarises them with a free LLM, and pushes a 1-page brief to Telegram
every morning. Runs itself on GitHub Actions — your laptop doesn't need to be on.

## What you'll set up (all free, ~10 minutes)

1. **A GitHub repo** — push these files to a new repo (private is fine).
2. **A Telegram bot** — in Telegram, message `@BotFather` → `/newbot` → copy the **bot token**.
3. **Your chat id** — send your new bot any message ("hi"), then run locally:
   ```
   pip install -r requirements.txt
   TELEGRAM_BOT_TOKEN=your_token python get_chat_id.py
   ```
   Copy the `chat_id` it prints.
4. **A Groq API key** — sign up at https://console.groq.com (free) → create an API key.

## Add your secrets to GitHub

In your repo: **Settings → Secrets and variables → Actions → New repository secret**. Add:

| Secret name          | Value                                  |
|----------------------|----------------------------------------|
| `GROQ_API_KEY`       | your Groq key                          |
| `TELEGRAM_BOT_TOKEN` | your bot token                         |
| `TELEGRAM_CHAT_ID`   | the chat id from step 3                |
| `GROQ_MODEL`         | *(optional)* override the default model|

## Test it now

Go to the **Actions** tab → **Daily Market Brief** → **Run workflow**. Within a minute you
should get a brief on Telegram. After that it runs automatically every morning.

## Tune it

- **What it covers:** edit `FEEDS` and `FOCUS` in `config.py`.
- **When it runs:** edit the `cron` line in `.github/workflows/daily.yml` (it's in UTC;
  `45 1 * * *` = 07:15 IST).
- **If the model name breaks** (Groq rotates models): set the `GROQ_MODEL` secret to a current
  one from https://console.groq.com/docs/models.

## Cost

GitHub Actions (free tier), RSS feeds (free), Groq (free tier), Telegram (free). Total: ₹0.
