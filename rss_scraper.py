import os
import time
import feedparser
import pandas as pd

from urllib.parse import quote_plus
from datetime import datetime

from query_generator import generate_queries

OUTPUT_FILE = "data/raw/raw_rss_results_maharashtra.csv"
os.makedirs(
    "data/raw",
    exist_ok=True
)

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

                "source": entry.get(
                    "source", {}
                ).get(
                    "title",
                    "Unknown"
                ),

                "published_date": entry.get(
                    "published",
                    ""
                ),

                "collected_at":
                datetime.now().isoformat()

            })

    except Exception as e:

        print(
            f"[ERROR] {query}"
        )

        print(e)

    return rows

def main():

    queries = generate_queries()

    all_rows = []

    print(
        f"Generated {len(queries)} queries"
    )

    for i, item in enumerate(
        queries,
        start=1
    ):

        query = item["query"]

        search_intent = item[
            "search_intent"
        ]

        print(
            f"[{i}/{len(queries)}]"
        )

        print(
            f"{search_intent}"
        )

        print(
            f"{query}"
        )

        rows = search_google_news(
            query
        )

        for row in rows:

            row[
                "search_intent"
            ] = search_intent

        all_rows.extend(rows)

        print(
            f"Found {len(rows)} articles"
        )

        time.sleep(1)

    df = pd.DataFrame(all_rows)

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()

    print(
        f"Saved {len(df)} rows"
    )

    print(
        OUTPUT_FILE
    )

if __name__ == "__main__":
    main()
