import os
import sys
import pandas as pd
import trafilatura
from tqdm import tqdm

if len(sys.argv) < 2:
    print("Usage: python noise_filter.py <state_name>")
    sys.exit(1)

STATE = sys.argv[1]

INPUT_FILE = f"processed/decoded_url_candidate_articles_{STATE}.csv"
OUTPUT_FILE = f"data/article_revealed/full_articles_{STATE}.csv"

CHECKPOINT_EVERY = 25


def get_article_text(url):

    if pd.isna(url):
        return None

    url = str(url).strip()

    if not url.startswith("http"):
        return None

    try:

        downloaded = trafilatura.fetch_url(url)

        if not downloaded:
            return None

        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            include_links=False
        )

        return text

    except Exception as e:
        print(f"\nError extracting {url}")
        return None


# ---------------------------------
# Load source file
# ---------------------------------

df = pd.read_csv(INPUT_FILE)

print(f"Loaded {len(df)} rows")

# ---------------------------------
# Resume support
# ---------------------------------

if os.path.exists(OUTPUT_FILE):

    old_df = pd.read_csv(OUTPUT_FILE)

    if "article_text" in old_df.columns:

        df["article_text"] = old_df["article_text"]

        print("Resuming previous extraction run")

else:

    if "article_text" not in df.columns:
        df["article_text"] = None


# ---------------------------------
# Extraction loop
# ---------------------------------

processed = 0

try:

    for idx in tqdm(df.index):

        existing_text = df.at[idx, "article_text"]

        # Skip already processed rows
        if pd.notna(existing_text) and str(existing_text).strip():
            continue

        url = df.at[idx, "real_url"]

        article_text = get_article_text(url)

        df.at[idx, "article_text"] = article_text

        processed += 1

        # Save checkpoint
        if processed % CHECKPOINT_EVERY == 0:

            df.to_csv(
                OUTPUT_FILE,
                index=False
            )

            print(
                f"\nCheckpoint saved "
                f"({processed} new articles processed)"
            )

except KeyboardInterrupt:

    print("\nStopping safely...")

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Progress saved to {OUTPUT_FILE}"
    )

    raise


# ---------------------------------
# Final save
# ---------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ---------------------------------
# Statistics
# ---------------------------------

article_lengths = (
    df["article_text"]
    .fillna("")
    .str.len()
)

successful = (article_lengths > 500).sum()

partial = (
    (article_lengths > 50)
    & (article_lengths <= 500)
).sum()

failed = (article_lengths <= 50).sum()

print("\n========== EXTRACTION SUMMARY ==========")

print(f"Total Articles     : {len(df)}")
print(f"Successful         : {successful}")
print(f"Partial Extraction : {partial}")
print(f"Failed             : {failed}")

print("\nColumns retained:")

for col in df.columns:
    print(f" - {col}")

print(f"\nSaved to: {OUTPUT_FILE}")