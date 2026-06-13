import pandas as pd
import sys

if len(sys.argv) < 2:
    print("Usage: python noise_filter.py <state_name>")
    sys.exit(1)

STATE = sys.argv[1]

INPUT_FILE = "data/raw/raw_rss_results_"+ STATE  +".csv"

OUTPUT_FILE = "data/deduplicated_url_based/unique_rss_results_"+ STATE + ".csv"

def main():

    print("Loading CSV...")

    df = pd.read_csv(INPUT_FILE)

    before = len(df)

    print(f"Original Rows: {before}")

    # Remove duplicate URLs

    df = df.drop_duplicates(
        subset=["url"]
    )

    after = len(df)

    removed = before - after

    print(f"Unique URLs: {after}")

    print(f"Removed: {removed}")

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    
if __name__ == "__main__":
    main()