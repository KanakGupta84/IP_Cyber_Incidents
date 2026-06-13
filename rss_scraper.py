import os
import sys
import time
import feedparser
import pandas as pd
from urllib.parse import quote_plus
from datetime import datetime
from config_keywords_reject_terms.config import FRAUD_CATEGORIES

if len(sys.argv) < 2:
    print("Usage: python rss_scraper_for_one_state.py <state_name>")
    sys.exit(1)

STATE = sys.argv[1]
OUTPUT_FILE = f"data/raw/raw_rss_results_{STATE}.csv"
os.makedirs("data/raw", exist_ok=True)


def search_google_news(query):
    rss_url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query)}"
        "&hl=en-IN"
        "&gl=IN"
        "&ceid=IN:en"
    )
    rows = []
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            rows.append({
                "query": query,
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "source": entry.get("source", {}).get("title", "Unknown"),
                "published_date": entry.get("published", ""),
                "collected_at": datetime.now().isoformat()
            })
    except Exception as e:
        print(f"[ERROR] {query}")
        print(e)
    return rows


def main():
    queries = []
    for category, keywords in FRAUD_CATEGORIES.items():
        for keyword in keywords:
            queries.append({
                "query": f"{keyword} {STATE}",
                "search_intent": category
            })

    all_rows = []
    print(f"Generated {len(queries)} queries for {STATE}")

    for i, item in enumerate(queries, start=1):
        query = item["query"]
        search_intent = item["search_intent"]

        print(f"[{i}/{len(queries)}] {search_intent} | {query}")

        rows = search_google_news(query)
        for row in rows:
            row["search_intent"] = search_intent
        all_rows.extend(rows)

        print(f"Found {len(rows)} articles")
        time.sleep(1)

    df = pd.DataFrame(all_rows)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(df)} rows → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()