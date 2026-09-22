#!/usr/bin/env python3
"""
Stage 2: original publisher URL -> extracted article content

Input:
  ai_fraud_original_links.csv   (output of Stage 1)

Output:
  ai_fraud_articles.csv

For every row whose link was actually resolved in Stage 1
(link_status in {"success", "success_decoder", "already_original"}),
this fetches the real publisher page and pulls out the article's main
text, title, author, and date - stripping nav bars, ads, related-article
widgets, comments, etc. Rows that were never resolved (failed_rerun,
unfixable_no_source_url, etc.) are carried through as "skipped", not
silently dropped.

Like Stage 1, this is parallelized, resumable (checkpoints every
CHECKPOINT_EVERY rows, safe to re-run), and never touches rows that
already succeeded on a prior run.

Install:
  pip install -U pandas requests trafilatura

Run:
  python extract_article_content.py \
      --input ai_fraud_original_links.csv \
      --output ai_fraud_articles.csv
"""

import argparse
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

MAX_WORKERS = 5
TIMEOUT = 20
RETRIES = 2
CHECKPOINT_EVERY = 100

# Only these Stage 1 statuses mean "we have a real publisher URL worth
# fetching". Everything else (failed_rerun, unfixable_no_source_url, ...)
# gets carried through untouched as "skipped".
RESOLVED_STATUSES = {"success", "success_decoder", "already_original"}

thread_local = threading.local()


def get_session():
    if not hasattr(thread_local, "session"):
        s = requests.Session()
        s.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })
        thread_local.session = s
    return thread_local.session


def fetch_html(url):
    s = get_session()
    r = s.get(url, timeout=TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    r.encoding = r.encoding or "utf-8"
    return r.text


def extract_article(url, html):
    """Returns a dict with title/author/date/text/word_count, or None if
    trafilatura couldn't pull out a real article body."""
    import trafilatura

    result = trafilatura.extract(
        html,
        url=url,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_tables=False,
        favor_recall=True,
    )

    if not result:
        return None

    data = json.loads(result)
    text = (data.get("text") or "").strip()

    if not text:
        return None

    return {
        "extracted_title": data.get("title") or "",
        "extracted_author": data.get("author") or "",
        "extracted_date": data.get("date") or "",
        "article_text": text,
        "word_count": len(text.split()),
    }


def process_row(row):
    idx = row["_row_id"]
    link_status = row.get("link_status")
    original_url = row.get("original_url")

    base = {
        "_row_id": idx,
        "article_id": row.get("article_id"),
        "title": row.get("title"),
        "source": row.get("source"),
        "published_date": row.get("published_date"),
        "original_url": original_url,
        "link_status": link_status,
        "extraction_status": "",
        "extracted_title": "",
        "extracted_author": "",
        "extracted_date": "",
        "article_text": "",
        "word_count": 0,
        "error": "",
    }

    if link_status not in RESOLVED_STATUSES or pd.isna(original_url) or not str(original_url).strip():
        base["extraction_status"] = "skipped_unresolved_link"
        base["error"] = f"link_status={link_status!r} not resolved, nothing to fetch"
        return base

    url = str(original_url).strip()
    last_error = ""

    for attempt in range(RETRIES):
        try:
            html = fetch_html(url)
            article = extract_article(url, html)

            if article:
                base.update(article)
                base["extraction_status"] = "success"
                return base

            last_error = "trafilatura found no extractable article text"

        except Exception as e:
            last_error = f"attempt {attempt + 1}/{RETRIES}: {type(e).__name__}: {e}"

        if attempt < RETRIES - 1:
            time.sleep((2 ** attempt) + random.random())

    base["extraction_status"] = "failed"
    base["error"] = last_error
    return base


def save_checkpoint(old, results, output):
    new = pd.DataFrame(results)

    if not old.empty and not new.empty:
        combined = pd.concat([old, new], ignore_index=True)
        combined = combined.drop_duplicates("_row_id", keep="last")
    elif not old.empty:
        combined = old.copy()
    else:
        combined = new.copy()

    if combined.empty:
        return combined

    combined = combined.sort_values("_row_id")
    combined.to_csv(output, index=False)
    return combined


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="ai_fraud_original_links.csv")
    parser.add_argument("--output", default="ai_fraud_articles.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df = df.reset_index(drop=True)
    df["_row_id"] = range(len(df))

    print(f"Input rows: {len(df):,}")
    print(f"Resolved (fetchable) rows: {df['link_status'].isin(RESOLVED_STATUSES).sum():,}")

    # Resume from a prior run of THIS script (keyed on article_id, which
    # is stable across both stage 1 and stage 2 outputs).
    if os.path.exists(args.output):
        print(f"Checkpoint found: {args.output}")
        old = pd.read_csv(args.output)

        if "article_id" in old.columns:
            done_ids = set(
                old.loc[
                    old["extraction_status"].isin(["success", "skipped_unresolved_link"]),
                    "article_id"
                ].dropna()
            )
            # Recover _row_id by joining back on article_id so the
            # checkpoint file can be combined with new results later.
            id_to_row = dict(zip(df["article_id"], df["_row_id"]))
            old["_row_id"] = old["article_id"].map(id_to_row)
            completed = set(
                old.loc[old["article_id"].isin(done_ids), "_row_id"].dropna().astype(int)
            )
        else:
            completed = set()

        print(f"Already done: {len(completed):,}")
    else:
        old = pd.DataFrame()
        completed = set()
        print("No checkpoint found. Starting from beginning.")

    todo = df[~df["_row_id"].isin(completed)].copy()
    print(f"Remaining rows: {len(todo):,}")

    if todo.empty:
        print("\nAll rows already processed.")
        combined = old.sort_values("_row_id")
    else:
        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = [ex.submit(process_row, row) for _, row in todo.iterrows()]

            for n, future in enumerate(as_completed(futures), 1):
                result = future.result()
                results.append(result)

                print(
                    f"[{n:,}/{len(todo):,}] "
                    f"article_id={result.get('article_id')} "
                    f"-> {result.get('extraction_status')} "
                    f"({result.get('word_count', 0)} words)"
                )

                if result["extraction_status"] == "failed":
                    print(f"    ERROR: {result['error']}")

                if n % CHECKPOINT_EVERY == 0:
                    combined = save_checkpoint(old, results, args.output)
                    print(f"\n*** CHECKPOINT SAVED: {n:,}/{len(todo):,} ***\n")

        combined = save_checkpoint(old, results, args.output)

    final_cols = [
        "article_id", "title", "source", "published_date", "original_url",
        "link_status", "extraction_status", "extracted_title",
        "extracted_author", "extracted_date", "article_text", "word_count",
        "error",
    ]
    combined = combined.sort_values("_row_id")
    combined[final_cols].to_csv(args.output, index=False)

    print("\nDONE")
    print(f"Output rows: {len(combined):,}")
    print("\nExtraction status counts:")
    print(combined["extraction_status"].value_counts(dropna=False).to_string())
    print(f"\nSaved: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
