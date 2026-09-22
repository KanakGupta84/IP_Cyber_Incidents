#!/usr/bin/env python3
"""
Re-fetch previously failed articles from ai_fraud_articles.csv.

Usage:
    pip install requests trafilatura pandas tqdm
    python refetch_failed_articles.py ai_fraud_articles.csv --out ai_fraud_articles_refetched.csv

What it does:
  - Loads the CSV, selects rows where extraction_status is 'failed' or
    'skipped_unresolved_link'.
  - Retries each URL with rotating User-Agents, realistic browser headers,
    and retry/backoff for timeouts, 429, and 5xx errors.
  - Extracts article text with trafilatura (falls back to readability-lxml
    if installed and trafilatura comes up empty).
  - Writes results back into the SAME columns as the original pipeline
    (extraction_status, extracted_title, extracted_author, extracted_date,
    article_text, word_count, error) so the row shapes match.
  - Saves a full merged CSV plus a small run summary.

Notes:
  - 403s from sites like NDTV are often bot-blocking at the CDN/WAF level
    (Akamai/Cloudflare). Rotating headers helps sometimes, but if a site
    keeps blocking, consider: (a) adding a longer delay between requests
    to that domain, (b) trying the site's AMP or mobile URL variant,
    (c) using a headless browser (playwright) for that domain specifically,
    or (d) archive.org's Wayback Machine as a fallback source.
  - Be a good citizen: this script defaults to modest concurrency and a
    per-request delay. Increase at your own risk / the target site's ToS.
"""

import argparse
import random
import sys
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import trafilatura
except ImportError:
    sys.exit("Missing dependency: pip install trafilatura")

# Optional fallback extractor
try:
    from readability import Document as ReadabilityDocument
    HAVE_READABILITY = True
except ImportError:
    HAVE_READABILITY = False


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}


def make_session():
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.5,  # 0, 1.5, 3, 6s ...
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=False,  # some sites send huge Retry-After values
        # that would otherwise make urllib3 sleep for minutes/hours per request.
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


def fetch_html(session, url, timeout=20):
    headers = dict(BASE_HEADERS)
    headers["User-Agent"] = random.choice(USER_AGENTS)
    try:
        resp = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text, None
    except requests.exceptions.HTTPError as e:
        return None, f"HTTPError: {e}"
    except requests.exceptions.Timeout:
        return None, "Timeout: request timed out"
    except requests.exceptions.SSLError as e:
        return None, f"SSLError: {e}"
    except requests.exceptions.ConnectionError as e:
        return None, f"ConnectionError: {e}"
    except requests.exceptions.RequestException as e:
        return None, f"RequestException: {e}"


def extract_article(html, url):
    """Returns dict with title/author/date/text/word_count, or None on failure."""
    downloaded = html
    result = trafilatura.extract(
        downloaded,
        url=url,
        include_comments=False,
        include_tables=False,
        with_metadata=True,
        output_format="json",
    )
    if result:
        import json
        data = json.loads(result)
        text = (data.get("text") or "").strip()
        if text:
            return {
                "extracted_title": data.get("title"),
                "extracted_author": data.get("author"),
                "extracted_date": data.get("date"),
                "article_text": text,
                "word_count": len(text.split()),
            }

    # Fallback: readability-lxml, if installed, just for text (no metadata)
    if HAVE_READABILITY:
        try:
            doc = ReadabilityDocument(html)
            text = doc.summary()
            # crude tag strip
            import re
            plain = re.sub("<[^<]+?>", " ", text)
            plain = re.sub(r"\s+", " ", plain).strip()
            if plain and len(plain.split()) > 40:
                return {
                    "extracted_title": doc.short_title(),
                    "extracted_author": None,
                    "extracted_date": None,
                    "article_text": plain,
                    "word_count": len(plain.split()),
                }
        except Exception:
            pass

    return None


def process_row(session, row, delay_range, timeout):
    time.sleep(random.uniform(*delay_range))  # be polite / vary timing
    url = row["original_url"]
    if pd.isna(url) or not str(url).strip():
        return {
            "article_id": row["article_id"],
            "extraction_status": "failed",
            "extracted_title": None,
            "extracted_author": None,
            "extracted_date": None,
            "article_text": None,
            "word_count": 0,
            "error": "no source url",
        }

    html, err = fetch_html(session, url, timeout=timeout)
    if html is None:
        return {
            "article_id": row["article_id"],
            "extraction_status": "failed",
            "extracted_title": None,
            "extracted_author": None,
            "extracted_date": None,
            "article_text": None,
            "word_count": 0,
            "error": f"refetch: {err}",
        }

    extracted = extract_article(html, url)
    if extracted is None:
        return {
            "article_id": row["article_id"],
            "extraction_status": "failed",
            "extracted_title": None,
            "extracted_author": None,
            "extracted_date": None,
            "article_text": None,
            "word_count": 0,
            "error": "refetch: no extractable article text",
        }

    return {
        "article_id": row["article_id"],
        "extraction_status": "success",
        "extracted_title": extracted["extracted_title"],
        "extracted_author": extracted["extracted_author"],
        "extracted_date": extracted["extracted_date"],
        "article_text": extracted["article_text"],
        "word_count": extracted["word_count"],
        "error": None,
    }


def main():
    ap = argparse.ArgumentParser(description="Retry failed article fetches.")
    ap.add_argument("input_csv", help="Path to ai_fraud_articles.csv")
    ap.add_argument("--out", default="ai_fraud_articles_refetched.csv",
                     help="Output path for the merged CSV")
    ap.add_argument("--workers", type=int, default=4,
                     help="Concurrent fetch threads (keep modest to avoid bans)")
    ap.add_argument("--timeout", type=int, default=20, help="Per-request timeout (s)")
    ap.add_argument("--min-delay", type=float, default=1.0,
                     help="Min random delay (s) before each request")
    ap.add_argument("--max-delay", type=float, default=3.0,
                     help="Max random delay (s) before each request")
    args = ap.parse_args()

    df = pd.read_csv(args.input_csv)
    mask = df["extraction_status"].isin(["failed", "skipped_unresolved_link"])
    to_retry = df[mask].copy()
    print(f"Retrying {len(to_retry)} articles...")

    session = make_session()
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                process_row, session, row, (args.min_delay, args.max_delay), args.timeout
            ): row["article_id"]
            for _, row in to_retry.iterrows()
        }
        done = 0
        # Hard deadline per article so one stuck request (e.g. a huge
        # Retry-After, or a slow-trickling connection) can never stall
        # the whole run. Anything that blows past this is recorded as
        # failed and we move on.
        hard_deadline = args.timeout * 6 + 30
        pending = set(futures.keys())
        while pending:
            done_now, pending = concurrent.futures.wait(
                pending, timeout=hard_deadline, return_when="FIRST_COMPLETED"
            )
            if not done_now:
                # Nothing finished within the deadline: bail out on whatever
                # is still pending so the script can't hang forever.
                for fut in list(pending):
                    article_id = futures[fut]
                    fut.cancel()
                    results.append({
                        "article_id": article_id,
                        "extraction_status": "failed",
                        "extracted_title": None,
                        "extracted_author": None,
                        "extracted_date": None,
                        "article_text": None,
                        "word_count": 0,
                        "error": "refetch: stalled past hard deadline, skipped",
                    })
                    done += 1
                    print(f"[{done}/{len(to_retry)}] id={article_id} -> stalled/skipped")
                pending = set()
                break
            for fut in done_now:
                article_id = futures[fut]
                try:
                    res = fut.result()
                except Exception as e:
                    res = {
                        "article_id": article_id,
                        "extraction_status": "failed",
                        "extracted_title": None,
                        "extracted_author": None,
                        "extracted_date": None,
                        "article_text": None,
                        "word_count": 0,
                        "error": f"refetch: worker exception: {e}",
                    }
                results.append(res)
                done += 1
                status = res["extraction_status"]
                print(f"[{done}/{len(to_retry)}] id={res['article_id']} -> {status}")

    results_df = pd.DataFrame(results).set_index("article_id")

    # Merge results back into the original dataframe
    df = df.set_index("article_id")
    update_cols = [
        "extraction_status", "extracted_title", "extracted_author",
        "extracted_date", "article_text", "word_count", "error",
    ]
    for col in update_cols:
        df.loc[results_df.index, col] = results_df[col]
    df = df.reset_index()

    df.to_csv(args.out, index=False)

    n_success = (results_df["extraction_status"] == "success").sum()
    n_failed = (results_df["extraction_status"] == "failed").sum()
    print("\n--- Summary ---")
    print(f"Retried:        {len(results_df)}")
    print(f"Now succeeded:  {n_success}")
    print(f"Still failed:   {n_failed}")
    print(f"Saved to:       {args.out}")
    print(f"Run time:       {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()