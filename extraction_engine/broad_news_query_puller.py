"""
broad_news_query_puller.py

Pulls Indian cyber-fraud / AI-fraud news from Google News RSS across a wide
combination of: fraud techniques (AI-specific AND general cyber fraud),
Indian states, and Hindi-language equivalents. This is the "widen the net"
step — the idea is to gather a much larger candidate pool than a narrow
"AI fraud India" search would, so that downstream classification
(classify_ai_in_articles.py) has more genuine AI-incidents to find.

Google News RSS needs no API key and has no official rate limit, but be
polite (built-in delay) to avoid getting temporarily blocked.

Usage:
    python broad_news_query_puller.py
        (writes candidate_articles.csv into the same folder as this script)

    python broad_news_query_puller.py output.csv

Requirements:
    pip install requests feedparser pandas
"""

import os
import sys
import time
import random
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import feedparser
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "candidate_articles.csv")

DELAY_RANGE = (0.5, 1.2)   # small polite per-thread delay before each request
WORKERS = 4                # number of concurrent queries; tune based on results
CHECKPOINT_EVERY = 20      # save progress after this many completed queries

# --- Build the query list ------------------------------------------------

STATES = [
    "Bihar", "Uttar Pradesh", "Maharashtra", "Delhi", "West Bengal",
    "Tamil Nadu", "Karnataka", "Telangana", "Andhra Pradesh", "Kerala",
    "Gujarat", "Rajasthan", "Madhya Pradesh", "Punjab", "Haryana",
    "Odisha", "Jharkhand", "Assam", "Chhattisgarh", "Uttarakhand",
    "Himachal Pradesh", "Goa", "Tripura", "Manipur", "Meghalaya",
    "Nagaland", "Mizoram", "Sikkim", "Arunachal Pradesh",
]

# AI-specific fraud techniques (English)
AI_TECHNIQUE_TERMS_EN = [
    "AI fraud", "AI scam", "deepfake fraud", "deepfake scam",
    "voice cloning fraud", "voice clone scam", "AI voice scam",
    "digital arrest AI video", "face swap scam", "AI video call scam",
    "AI generated video scam", "AI investment scam", "AI trading app scam",
    "AI job scam", "AI KYC fraud", "AI chatbot scam", "sextortion deepfake",
    "morphed video blackmail", "AI photo blackmail",
    # Added from media-buzzword / threat-intel keyword research
    "deepfake vishing", "AI voice mimicry", "voice phishing AI",
    "synthetic identity fraud", "AI-powered cybercrime", "GenAI cybercrime",
    "generative AI phishing", "LLM phishing scam", "AI text scam",
    "voice synthesis scam", "TTS scam call", "AI chatbot romance scam",
    "deepfake face swapping fraud", "deepfake video meeting scam",
    "grandparent scam AI voice", "family emergency scam cloned voice",
    "CEO fraud deepfake", "executive impersonation deepfake",
    "AI pig butchering scam", "AI romance scam", "AI generated sextortion",
    "biometric bypass fraud", "synthetic ID KYC fraud",
]

# AI-specific fraud techniques (Hindi, transliterated search terms as
# commonly typed/searched, plus Devanagari for a few core terms)
AI_TECHNIQUE_TERMS_HI = [
    "एआई धोखाधड़ी", "डीपफेक धोखाधड़ी", "एआई फ्रॉड", "वॉइस क्लोनिंग फ्रॉड",
    "डिजिटल अरेस्ट एआई", "एआई स्कैम",
]

# General cyber-fraud terms (to widen the net — downstream classifier will
# find the AI-method subset within these)
GENERAL_FRAUD_TERMS_EN = [
    "cyber fraud", "digital arrest scam", "online fraud duped",
    "cyber cheating case", "KYC update fraud", "OTP fraud",
    "video call scam duped", "fake investment app fraud",
    "job scam cheated", "online trading fraud",
]

# Terms mapped from the "AI Related Fraud/Exploitation Classification" taxonomy
# (financial fraud, social engineering, crimes against women & children,
# identity & data fraud, platform/e-commerce fraud, technical attacks, scams).
# Combined with "AI" to keep relevance to this project's scope.
TAXONOMY_TERMS_EN = [
    "AI investment fraud", "AI banking fraud", "AI payment fraud",
    "AI loan fraud", "AI insurance fraud", "AI tax fraud",
    "AI employment fraud", "AI job fraud", "AI money laundering",
    "AI impersonation scam", "AI phishing", "AI vishing", "AI smishing",
    "AI romance exploitation", "AI child exploitation", "AI cyberstalking",
    "AI harassment", "AI non consensual intimate imagery", "AI nude deepfake",
    "AI identity theft", "AI account takeover", "AI data theft",
    "AI fake platform scam", "AI e-commerce fraud", "AI fake website scam",
    "AI malware attack", "AI ransomware attack", "AI unauthorized access",
    "AI lottery scam", "AI prize scam", "AI charity scam", "AI donation scam",
]

# Top-population states for the taxonomy terms above (kept smaller than the
# full STATES list to control total query volume)
TOP_STATES = [
    "Bihar", "Uttar Pradesh", "Maharashtra", "Delhi", "West Bengal",
    "Tamil Nadu", "Karnataka", "Telangana", "Andhra Pradesh", "Kerala",
]


def build_queries():
    queries = set()

    # AI-specific terms combined with "India" and with each state
    for term in AI_TECHNIQUE_TERMS_EN:
        queries.add(f"{term} India")
        for state in STATES:
            queries.add(f"{term} {state}")

    for term in AI_TECHNIQUE_TERMS_HI:
        queries.add(term)

    # General fraud terms combined with "AI" to keep some relevance signal,
    # plus per-state, to surface AI-method cases buried in generic coverage
    for term in GENERAL_FRAUD_TERMS_EN:
        queries.add(f"{term} AI India")
        for state in STATES:
            queries.add(f"{term} {state}")

    # Taxonomy terms — India-wide plus top 10 states (kept smaller to
    # control total query volume, since this list is itself large)
    for term in TAXONOMY_TERMS_EN:
        queries.add(f"{term} India")
        for state in TOP_STATES:
            queries.add(f"{term} {state}")

    return sorted(queries)


# --- Google News RSS fetching --------------------------------------------

def fetch_query(query: str):
    """Fetch one Google News RSS search and return list of dicts."""
    time.sleep(random.uniform(*DELAY_RANGE))
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        return query, [], str(e)

    feed = feedparser.parse(resp.content)
    results = []
    for entry in feed.entries:
        results.append({
            "query": query,
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "source": entry.get("source", {}).get("title", "") if entry.get("source") else "",
            "published_date": entry.get("published", ""),
        })
    return query, results, None


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else WORKERS

    queries = build_queries()
    print(f"Built {len(queries)} queries (states x techniques x languages).")
    print(f"Running with {workers} parallel workers.")

    all_rows = []
    seen_urls = set()
    lock = threading.Lock()
    completed = 0
    completed_since_checkpoint = 0

    def save_progress():
        pd.DataFrame(all_rows).to_csv(output_path, index=False)

    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(fetch_query, q): q for q in queries}
            for future in as_completed(futures):
                query, results, error = future.result()
                with lock:
                    completed += 1
                    completed_since_checkpoint += 1
                    new_count = 0
                    for r in results:
                        if r["url"] and r["url"] not in seen_urls:
                            seen_urls.add(r["url"])
                            all_rows.append(r)
                            new_count += 1

                    if error:
                        print(f"[{completed}/{len(queries)}] ERROR '{query}': {error}", flush=True)
                    else:
                        print(f"[{completed}/{len(queries)}] '{query}' -> "
                              f"{len(results)} results, {new_count} new "
                              f"(total: {len(all_rows)})", flush=True)

                    if completed_since_checkpoint >= CHECKPOINT_EVERY:
                        save_progress()
                        completed_since_checkpoint = 0
                        print(f"    [checkpoint saved: {len(all_rows)} total rows]", flush=True)

    except KeyboardInterrupt:
        print("\nInterrupted — saving progress before exiting...")
    finally:
        save_progress()
        print(f"\nDone. {len(all_rows)} unique candidate articles written to {output_path}")
        print("Next steps: decode/resolve URLs, scrape article text, then run "
              "classify_ai_in_articles.py on the result.")


if __name__ == "__main__":
    main()