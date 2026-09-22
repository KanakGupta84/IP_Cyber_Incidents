"""
classify_ai_in_articles.py

Given an Excel/CSV file with a 'url' and 'article' column (full scraped
article text), determines which articles actually describe AI being used
—not just mentioned in passing—and splits them into two categories:

  financial_fraud_ai        - AI was used as part of an actual scam/fraud
                               that cost someone money (or was an attempt to)
  deepfake_misinfo_or_other - AI/deepfake content is present, but it's not
                               a financial-fraud case (e.g. political
                               deepfakes, misinformation, AI-in-cybersecurity
                               commentary, unrelated product/feature news)

Output: an Excel file with one row per AI-related article, including the
matched keyword, a short context snippet, and the suggested category —
meant for a quick manual review pass, not as a final automated verdict.

WATCH MODE (new):
    This script can be run *while extract_articles_parallel.py is still
    scraping*. With WATCH_MODE = True (the default), it doesn't just run
    once and exit — it loops:

      1. Re-reads the input file.
      2. Classifies only rows whose article text is newly "final"
         (non-empty and not an [ERROR ...] entry) and that it hasn't
         already classified.
      3. Rows that are still empty/[ERROR ...] (not scraped yet, or the
         scraper is retrying them) are left pending and re-checked on the
         next pass — they are NOT treated as done.
      4. If a pass finds nothing new, it prints a message and sleeps for
         POLL_INTERVAL_SECONDS before checking again.
      5. Results accumulate in the same output file across passes, and
         progress is tracked in a small sidecar `<output>.state.json` file
         so you can Ctrl+C and resume later without reclassifying
         everything.

    Set WATCH_MODE = False to go back to the old single-pass behavior.

Usage:
    python classify_ai_in_articles.py
        (looks for mediacloud_ai_fraud_articles.xlsx in the same folder as
         this script, writes output into that same folder)

    python classify_ai_in_articles.py input.xlsx output.xlsx [workers]

Requirements:
    pip install pandas openpyxl
"""

import os
import sys
import re
import time
import json
from concurrent.futures import ProcessPoolExecutor
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT = os.path.join(SCRIPT_DIR, "candidate_articles_scraped.xlsx")
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "ai_related_articles_review.xlsx")
WORKERS = os.cpu_count() or 4   # CPU-bound work, so default to all cores
CHUNK_SIZE = 200                # rows per worker task

WATCH_MODE = True               # keep polling for newly-scraped articles
POLL_INTERVAL_SECONDS = 60      # how long to wait when a pass finds nothing new
MAX_CONSECUTIVE_EMPTY_POLLS = None  # e.g. 30 to auto-stop after ~30 empty polls;
                                     # None = run forever (Ctrl+C to stop)

STATE_SUFFIX = ".state.json"    # sidecar file tracking which URLs are finalized

# Terms that indicate AI was actually USED (as a method/tool), not just
# referenced abstractly (policy discussion, "AI industry" commentary, etc.)
AI_USAGE_PATTERN = re.compile(
    r"\b("
    r"deepfake\w*|deep-fake\w*|deep fake\w*|"
    r"voice clon\w*|voice-clon\w*|cloned? voice|ai voice|ai-generat\w* voice|"
    r"face swap\w*|face-swap\w*|"  
    r"synthetic (voice|video|identity|media)|synthetic id\w*|"
    r"morphed video|ai-generat\w* video|ai generat\w* video|fake ai video|"
    r"ai (video|audio) call|ai chatbot scam|chatbot scam|"
    r"ai-generat\w*|ai generat\w*|voice-generat\w*|"
    r"ai-powered (scam|fraud|attack|phishing|cybercrime)|"
    r"ai-driven (scam|fraud|attack|cybercrime)|"
    r"ai-enabled (scam|fraud|impersonation)|ai impersonat\w*|"
    r"ai (bot|agent)s? (used|scamming|impersonat\w*)|"
    r"deepfake vishing|voice mimicry|voice phishing|"
    r"generative ai|genai|gen-ai|generative text|large language model\w*|\bllm\b|"
    r"voice synthesis|text-?to-?speech scam|\btts\b scam|"
    r"hyper-realistic impersonat\w*|"
    r"pig butchering|romance scam.{0,30}(ai|chatbot|deepfake)|"
    r"grandparent scam|family emergency scam|cloned voice scam|"
    r"ceo fraud|executive impersonat\w*|"
    r"biometric bypass|kyc bypass|synthetic identity"
    r")\b",
    re.IGNORECASE,
)

# Terms suggesting an actual reported INCIDENT (money lost, arrest, blackmail)
# as opposed to abstract commentary, product features, or policy discussion.
INCIDENT_PATTERN = re.compile(
    r"\b("
    r"duped of|cheated of|conned (into|of)|swindled|lost (rs\.?|₹|inr)|"
    r"blackmail\w*|extort\w*|arrested for (creating|sharing|using|circulating|posting)|"
    r"held for (creating|sharing|using|circulating|posting)|"
    r"defrauded of|scammed (out of|of)|"
    r"(rs\.?|₹)\s?[\d,]+\s?(lakh|crore)?\s+(was )?(stolen|lost|duped|cheated|siphoned)|"
    r"victim\w*.{0,40}(rs\.?|₹)[\d,]+"
    r")\b",
    re.IGNORECASE,
)

# Phrases where "fraud/scam" is used as an abstract noun (detection systems,
# policy discussion, industry commentary) rather than describing a real case.
DEFENSIVE_CONTEXT_PATTERN = re.compile(
    r"(fraud|scam)\s+(detection|prevention|management|system\w*|tool\w*|concerns?|"
    r"protection|monitoring|analytics|alert\w*)",
    re.IGNORECASE,
)

# Taxonomy from the "AI Related Fraud/Exploitation Classification" chart —
# used to tag each genuine incident with a top-level category + subtype.
# Checked in order; first match wins.
TAXONOMY = [
    ("Financial Fraud", "Investment Fraud", r"investment (fraud|scam)|fake trading app|ponzi|crypto scam"),
    ("Financial Fraud", "Banking & Payment Fraud", r"bank(ing)? fraud|payment fraud|upi fraud|otp fraud"),
    ("Financial Fraud", "Loan Fraud", r"loan (fraud|scam|app)"),
    ("Financial Fraud", "Insurance & Tax Fraud", r"insurance fraud|tax fraud|tax scam"),
    ("Financial Fraud", "Employment Fraud", r"(job|employment) (fraud|scam)"),
    ("Financial Fraud", "Money Laundering", r"money launder\w*"),
    ("Social Engineering Fraud", "Impersonation", r"impersonat\w*"),
    ("Social Engineering Fraud", "Phishing/Vishing/Smishing", r"phishing|vishing|smishing"),
    ("Crimes Against Women & Children", "Romance Based Exploitation", r"romance scam|pig butchering|dating scam"),
    ("Crimes Against Women & Children", "Online Child Exploitation", r"child (exploitation|abuse|sexual)"),
    ("Crimes Against Women & Children", "Cyberstalking & Harassment", r"cyberstalk\w*|online harassment"),
    ("Crimes Against Women & Children", "Non Consensual Intimate Imagery", r"non.?consensual|nude deepfake|obscene (image|video|content)|morphed (image|photo|picture)"),
    ("Identity & Data Fraud", "Identity Theft", r"identity theft"),
    ("Identity & Data Fraud", "Account Takeover", r"account takeover"),
    ("Identity & Data Fraud", "Data Theft", r"data (theft|breach|leak)"),
    ("Platform & E-Commerce Fraud", "Fake Platform", r"fake (platform|website|app)\b"),
    ("Platform & E-Commerce Fraud", "E-commerce Fraud", r"e-?commerce fraud|online shopping (fraud|scam)"),
    ("Technical Attacks", "Malware", r"\bmalware\b"),
    ("Technical Attacks", "Ransomware & Unauthorized Access", r"ransomware|unauthorized access|hack\w*"),
    ("Scams", "Lottery/Prize Scam", r"lottery scam|prize scam"),
    ("Scams", "Charity/Donation Scam", r"charity scam|donation scam"),
    ("Scams", "Digital Arrest / Impersonation Call", r"digital arrest"),
    ("Scams", "Sextortion", r"sextortion|blackmail\w*.{0,30}(photo|video|image)"),
]
TAXONOMY_COMPILED = [(cat, sub, re.compile(pat, re.IGNORECASE)) for cat, sub, pat in TAXONOMY]


def tag_taxonomy(text: str):
    """Return (category, subtype) from the Miro fraud-classification taxonomy,
    or ('Uncategorized', 'Others') if nothing matches."""
    for cat, sub, pattern in TAXONOMY_COMPILED:
        if pattern.search(text):
            return cat, sub
    return "Uncategorized", "Others"


def classify(text: str):
    if not isinstance(text, str) or not text:
        return None
    m = AI_USAGE_PATTERN.search(text)
    if not m:
        return None
    has_incident = bool(INCIDENT_PATTERN.search(text))
    category = "financial_fraud_ai_incident" if has_incident else "other_ai_mention"
    taxonomy_category, taxonomy_subtype = tag_taxonomy(text)
    start = max(0, m.start() - 150)
    end = min(len(text), m.end() + 150)
    context = text[start:end].replace("\n", " ").strip()
    return m.group(), context, category, taxonomy_category, taxonomy_subtype


def classify_chunk(records):
    """Runs in a worker process. `records` is a list of (row_index, row_dict)
    tuples; row_dict must include an 'article' key. Returns a list of
    (row_index, result_or_None)."""
    results = []
    for idx, row in records:
        results.append((idx, classify(row.get("article"))))
    return results


def is_final_text(text) -> bool:
    """True if this article text represents a completed, successful scrape
    (non-empty and not an [ERROR ...] placeholder). False means the scraper
    hasn't produced usable text for this row yet (or is still retrying it),
    so it should be checked again on a later pass rather than treated as
    done."""
    return isinstance(text, str) and bool(text) and not text.startswith("[ERROR")


def load_state(output_path):
    state_path = output_path + STATE_SUFFIX
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_state(output_path, finalized_urls):
    state_path = output_path + STATE_SUFFIX
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(sorted(finalized_urls), f)


def load_existing_output(output_path):
    if os.path.exists(output_path):
        return pd.read_excel(output_path, engine="openpyxl")
    return pd.DataFrame()


def read_input(input_path, retries=5, retry_delay=3):
    """Read the input file, tolerating the case where the scraper is
    mid-write to the same path (a half-written .xlsx isn't a valid zip
    yet). Retries a few times with a short delay before giving up."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            if input_path.lower().endswith(".csv"):
                df = pd.read_csv(input_path)
            else:
                df = pd.read_excel(input_path, engine="openpyxl")
            for col in ("url", "article"):
                if col not in df.columns:
                    print(f"Expected a '{col}' column; not found in {input_path}.")
                    sys.exit(1)
            return df
        except Exception as e:
            last_err = e
            print(f"  (read of {input_path} failed on attempt {attempt}/{retries} — "
                  f"likely mid-write by the scraper. Retrying in {retry_delay}s: {e})")
            time.sleep(retry_delay)
    raise last_err


def run_one_pass(df, finalized_urls, workers, keep_cols):
    """Classify only rows not already finalized and whose article text is
    ready (non-empty, non-error). Returns (new_result_rows, newly_finalized_urls)."""
    pending = [
        (idx, row.to_dict())
        for idx, row in df.iterrows()
        if row["url"] not in finalized_urls and is_final_text(row.get("article"))
    ]

    if not pending:
        return [], set()

    chunks = [pending[i:i + CHUNK_SIZE] for i in range(0, len(pending), CHUNK_SIZE)]
    print(f"  {len(pending)} newly-finalized articles to classify across {len(chunks)} chunks...")

    results_by_index = {}
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for chunk_results in executor.map(classify_chunk, chunks):
            for idx, result in chunk_results:
                if result is not None:
                    results_by_index[idx] = result

    new_rows = []
    newly_finalized = set()
    for idx, row_dict in pending:
        newly_finalized.add(row_dict["url"])
        if idx in results_by_index:
            matched_keyword, context, category, taxonomy_category, taxonomy_subtype = results_by_index[idx]
            record = {c: row_dict.get(c) for c in keep_cols}
            record["matched_keyword"] = matched_keyword
            record["context_snippet"] = context
            record["likely_category"] = category
            record["taxonomy_category"] = taxonomy_category
            record["taxonomy_subtype"] = taxonomy_subtype
            new_rows.append(record)

    return new_rows, newly_finalized


def print_summary(all_rows, finalized_count, total):
    out = pd.DataFrame(all_rows)
    ai_related = len(out)
    incidents = (out["likely_category"] == "financial_fraud_ai_incident").sum() if ai_related else 0
    other = ai_related - incidents

    print(f"\nArticles finalized (scraped) so far:  {finalized_count}/{total}")
    print(f"Articles with genuine AI usage:       {ai_related}")
    print(f"  - financial_fraud_ai_incident:      {incidents}")
    print(f"  - other_ai_mention:                 {other}")

    if ai_related:
        print("\nBreakdown by taxonomy category (incidents only):")
        inc_df = out[out["likely_category"] == "financial_fraud_ai_incident"]
        print(inc_df["taxonomy_category"].value_counts().to_string())


def main():
    workers = WORKERS
    args = sys.argv[1:]
    if len(args) == 0:
        input_path, output_path = DEFAULT_INPUT, DEFAULT_OUTPUT
    elif len(args) == 2:
        input_path, output_path = args
    elif len(args) == 3:
        input_path, output_path, workers = args[0], args[1], int(args[2])
    else:
        print("Usage: python classify_ai_in_articles.py [input.xlsx output.xlsx [workers]]")
        sys.exit(1)

    keep_cols_cache = None
    finalized_urls = load_state(output_path)
    existing_out = load_existing_output(output_path)
    all_rows = existing_out.to_dict("records") if not existing_out.empty else []
    if finalized_urls:
        print(f"Resuming — {len(finalized_urls)} articles already classified previously "
              f"(tracked in {output_path}{STATE_SUFFIX}).")

    consecutive_empty = 0

    while True:
        if not os.path.exists(input_path):
            print(f"Waiting for input file to appear: {input_path}")
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        try:
            df = read_input(input_path)
        except Exception as e:
            print(f"Still couldn't read {input_path} after retries ({e}). "
                  f"Will try again in {POLL_INTERVAL_SECONDS}s.")
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        if keep_cols_cache is None:
            keep_cols_cache = [c for c in ["title", "media_name", "publish_date", "url"] if c in df.columns]

        new_rows, newly_finalized = run_one_pass(df, finalized_urls, workers, keep_cols_cache)

        if new_rows or newly_finalized:
            all_rows.extend(new_rows)
            finalized_urls |= newly_finalized
            out = pd.DataFrame(all_rows)
            out.to_excel(output_path, index=False, engine="openpyxl")
            save_state(output_path, finalized_urls)
            consecutive_empty = 0
            print(f"  -> {len(new_rows)} AI-related matches this pass "
                  f"({len(finalized_urls)}/{len(df)} articles finalized overall). "
                  f"Wrote {output_path}", flush=True)
        else:
            consecutive_empty += 1
            print(f"No newly-finalized articles this pass "
                  f"({len(finalized_urls)}/{len(df)} finalized so far).", flush=True)

        if not WATCH_MODE:
            break
        if MAX_CONSECUTIVE_EMPTY_POLLS and consecutive_empty >= MAX_CONSECUTIVE_EMPTY_POLLS:
            print("No new articles for a while — stopping. "
                  "Set MAX_CONSECUTIVE_EMPTY_POLLS = None to run forever instead.")
            break

        print(f"Waiting {POLL_INTERVAL_SECONDS}s before checking for more scraped articles... (Ctrl+C to stop)",
              flush=True)
        try:
            time.sleep(POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break

    if all_rows:
        total = len(df) if 'df' in dir() else len(finalized_urls)
        print_summary(all_rows, len(finalized_urls), total)
    print(f"\nOutput file: {output_path}")


if __name__ == "__main__":
    main()