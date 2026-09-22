#!/usr/bin/env python3
"""
Stage 1: Google News URL -> original publisher URL

Input:
  candidate_articles_ai_fraud_cleaned.csv

Output:
  ai_fraud_original_links.csv

The pipeline is parallelized, resumable, and keeps failures instead of
dropping rows. It first follows the Google News URL directly. For difficult
Google News article tokens, it falls back to googlenewsdecoder when available.

Install:
  pip install -U pandas requests googlenewsdecoder

Run:
  python extract_original_links.py
"""

import os
import re
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import pandas as pd
import requests

INPUT = "candidate_articles_ai_fraud_cleaned.csv"
OUTPUT = "ai_fraud_original_links.csv"
MAX_WORKERS = 5
TIMEOUT = 20
RETRIES = 3
CHECKPOINT_EVERY = 100

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


def is_google_news(url):
    try:
        return "news.google.com" in urlparse(str(url)).netloc.lower()
    except Exception:
        return False


def clean_url(url):
    if not url:
        return ""
    url = str(url).strip()
    url = url.split("#")[0]
    return url


def direct_resolve(url):
    s = get_session()

    r = s.get(
        url,
        timeout=TIMEOUT,
        allow_redirects=True,
        stream=True,
    )

    final = clean_url(r.url)
    status = r.status_code

    r.close()

    return final, status


def decoder_resolve(url):
    try:
        from googlenewsdecoder import gnewsdecoder
    except ImportError:
        return "", None, "googlenewsdecoder not installed"

    try:
        result = gnewsdecoder(url, interval=1)

        if isinstance(result, dict):

            if result.get("status"):
                return (
                    clean_url(result.get("decoded_url", "")),
                    200,
                    ""
                )

            return (
                "",
                None,
                str(result.get("message", "decoder failed"))
            )

        return clean_url(str(result)), 200, ""

    except Exception as e:
        return (
            "",
            None,
            f"decoder error: {type(e).__name__}: {e}"
        )


def resolve_one(row):
    idx = row["_row_id"]
    source_url = clean_url(row["url"])

    base = {
        "_row_id": idx,
        "article_id": idx + 1,
        "title": row.get("title", ""),
        "source": row.get("source", ""),
        "published_date": row.get("published_date", ""),
        "google_news_url": source_url,
        "original_url": "",
        "link_status": "",
        "http_status": "",
        "error": "",
    }

    if not source_url:
        base["link_status"] = "failed"
        base["error"] = "empty URL"
        return base

    # If a row already contains a publisher URL, keep it.
    if not is_google_news(source_url):
        base["original_url"] = source_url
        base["link_status"] = "already_original"
        return base

    last_error = ""

    # Direct resolution
    for attempt in range(RETRIES):
        try:
            final, status = direct_resolve(source_url)

            if final and not is_google_news(final):
                base["original_url"] = final
                base["http_status"] = status
                base["link_status"] = (
                    "success"
                    if status and status < 400
                    else "redirected_http_error"
                )
                return base

            last_error = (
                f"redirect remained on Google News "
                f"(HTTP {status})"
            )

        except Exception as e:
            last_error = (
                f"direct attempt {attempt + 1}/{RETRIES}: "
                f"{type(e).__name__}: {e}"
            )

        if attempt < RETRIES - 1:
            time.sleep(
                (2 ** attempt) + random.random()
            )

    # Fallback decoder
    final, status, err = decoder_resolve(source_url)

    if final and not is_google_news(final):
        base["original_url"] = final
        base["http_status"] = status or ""
        base["link_status"] = "success_decoder"
        return base

    # Failed
    base["link_status"] = "failed"
    base["http_status"] = status or ""

    if last_error and err:
        base["error"] = f"{last_error}; decoder: {err}"
    elif last_error:
        base["error"] = last_error
    else:
        base["error"] = err

    return base


def save_checkpoint(old, results):
    new = pd.DataFrame(results)

    if not old.empty and not new.empty:
        combined = pd.concat(
            [old, new],
            ignore_index=True
        )

        combined = combined.drop_duplicates(
            "_row_id",
            keep="last"
        )

    elif not old.empty:
        combined = old.copy()

    else:
        combined = new.copy()

    if combined.empty:
        return combined

    combined = combined.sort_values("_row_id")

    checkpoint_cols = [
        "_row_id",
        "article_id",
        "title",
        "source",
        "published_date",
        "google_news_url",
        "original_url",
        "link_status",
        "http_status",
        "error"
    ]

    combined[checkpoint_cols].to_csv(
        OUTPUT,
        index=False
    )

    return combined


def main():

    print(
        "Starting Google News URL resolver...",
        flush=True
    )

    df = pd.read_csv(INPUT)

    if "url" not in df.columns:
        raise ValueError(
            "Input CSV must contain a 'url' column."
        )

    df = df.reset_index(drop=True)
    df["_row_id"] = range(len(df))

    print(
        f"Input rows: {len(df):,}",
        flush=True
    )

    # Load checkpoint
    if os.path.exists(OUTPUT):

        print(
            f"Checkpoint found: {OUTPUT}",
            flush=True
        )

        old = pd.read_csv(OUTPUT)

        if "_row_id" in old.columns:

            completed = set(
                old.loc[
                    old["link_status"].isin(
                        [
                            "success",
                            "success_decoder",
                            "already_original"
                        ]
                    ),
                    "_row_id"
                ].astype(int)
            )

            print(
                f"Completed rows recovered: "
                f"{len(completed):,}",
                flush=True
            )

        else:

            print(
                "WARNING: Existing output has no _row_id. "
                "Starting without resume information.",
                flush=True
            )

            completed = set()

    else:

        old = pd.DataFrame()
        completed = set()

        print(
            "No checkpoint found. Starting from beginning.",
            flush=True
        )

    todo = df[
        ~df["_row_id"].isin(completed)
    ].copy()

    print(
        f"Remaining rows: {len(todo):,}",
        flush=True
    )

    if todo.empty:

        print(
            "\nAll rows are already completed.",
            flush=True
        )

        combined = old.sort_values("_row_id")

    else:

        results = []

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as ex:

            futures = [
                ex.submit(resolve_one, row)
                for _, row in todo.iterrows()
            ]

            for n, future in enumerate(
                as_completed(futures),
                1
            ):

                result = future.result()
                results.append(result)

                status = result.get(
                    "link_status",
                    ""
                )

                error = result.get(
                    "error",
                    ""
                )

                title = str(
                    result.get("title", "")
                ).replace("\n", " ")[:100]

                print(
                    f"[{n:,}/{len(todo):,}] "
                    f"Status={status} "
                    f"| Article={result.get('article_id', '')} "
                    f"| {title}",
                    flush=True
                )

                if status == "failed":
                    print(
                        f"    ERROR: {error}",
                        flush=True
                    )

                # Checkpoint every 100 completed links
                if n % CHECKPOINT_EVERY == 0:

                    combined = save_checkpoint(
                        old,
                        results
                    )

                    print(
                        f"\n*** CHECKPOINT SAVED: "
                        f"{n:,}/{len(todo):,} "
                        f"new links processed ***\n",
                        flush=True
                    )

        # Final save
        combined = save_checkpoint(
            old,
            results
        )

    # Final output
    combined = combined.sort_values(
        "_row_id"
    )

    final_cols = [
        "article_id",
        "title",
        "source",
        "published_date",
        "google_news_url",
        "original_url",
        "link_status",
        "http_status",
        "error"
    ]

    combined[final_cols].to_csv(
        OUTPUT,
        index=False
    )

    print("\nDONE", flush=True)

    print(
        f"Input rows:  {len(df):,}",
        flush=True
    )

    print(
        f"Output rows: {len(combined):,}",
        flush=True
    )

    print(
        "\nStatus counts:",
        flush=True
    )

    print(
        combined["link_status"]
        .value_counts(dropna=False)
        .to_string(),
        flush=True
    )

    print(
        f"\nSaved: {os.path.abspath(OUTPUT)}",
        flush=True
    )


if __name__ == "__main__":
    main()