"""
Configuration: which feeds to pull and what the brief should focus on.
Edit the FEEDS and FOCUS lists to tune your morning brief — no other file needs changing.
"""

# Each feed is (category, name, url). Categories just help the summarizer group things.
# All of these are free, public RSS feeds. Add/remove freely.
FEEDS = [
    # --- Indian markets, deals, M&A ---
    ("Markets (India)", "Economic Times Markets", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Markets (India)", "Moneycontrol Markets", "https://www.moneycontrol.com/rss/marketreports.xml"),
    ("Deals / M&A",     "ET M&A / Deals",        "https://economictimes.indiatimes.com/news/company/mergers-acquisitions/rssfeeds/13357270.cms"),
    ("Business (India)", "Business Standard",     "https://www.business-standard.com/rss/markets-106.rss"),
    ("Business (India)", "Livemint Markets",      "https://www.livemint.com/rss/markets"),

    # --- IPOs (current + upcoming) ---
    ("IPO", "Moneycontrol IPO", "https://www.moneycontrol.com/rss/iponews.xml"),

    # --- Global markets ---
    ("Global", "CNBC Finance",     "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"),
]

# A short description of what YOU care about. This steers the summarizer on what to surface
# and what "what should I focus on today" means for you.
FOCUS = """
Reader is a finance-focused PGDM student targeting investment banking (M&A, debt syndication)
and preparing for CFA Level 1. Prioritise: Indian + global M&A and deal activity, debt/equity
issuances, IPOs (live and upcoming), notable earnings, central bank / rate moves, and anything
that would come up in an IB or markets interview. Skip celebrity, sports, and fluff.
"""

# How many hours back to include (24 = last day's news for a morning run).
LOOKBACK_HOURS = 28

# Max items to feed the summarizer (keeps it fast and within free-tier limits).
MAX_ITEMS = 60
