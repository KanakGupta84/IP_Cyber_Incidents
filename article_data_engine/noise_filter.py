import os
import sys
import pandas as pd
from config_keywords_reject_terms.reject_term_pass_2 import REJECT_TERMS
from config_keywords_reject_terms.states_term import INDIA_STATES_CITIES


if len(sys.argv) < 2:
    print("Usage: python noise_filter.py <state_name>")
    sys.exit(1)

STATE = sys.argv[1]

INPUT_FILE = "data/deduplicated_url_based/unique_rss_results_"+ STATE +  ".csv"

OUTPUT_ALL = "data/deduplicated_url_based/noise_filtered_" + STATE + ".csv"
OUTPUT_CANDIDATES = "data/deduplicated_url_based/candidate_articles_" + STATE + ".csv"

os.makedirs("data/processed", exist_ok=True)


# ==================================================
# FUNCTIONS
# ==================================================

def check_state_and_cities(title):

    title = str(title).lower()

    return any(
        term.lower() in title
        for term in INDIA_STATES_CITIES[STATE]
    )

def check_noise(title):
        
    title = str(title).lower()

    return any(
        term in title
        for term in REJECT_TERMS
    )
# ==================================================
# MAIN
# ==================================================

def main():
    
    print("Loading CSV...")

    df = pd.read_csv(INPUT_FILE)

    print(
        f"Rows Loaded: {len(df)}"
    )

    # ------------------------------------------
    # Flags
    # ------------------------------------------

    df["is_state_and_cities"] = (
        df["title"]
        .apply(check_state_and_cities)
    )

    df["is_noise"] = (
        df["title"]
        .apply(check_noise)
    )

    def classify_row(row):

        if row["is_state_and_cities"] and not row["is_noise"]:
            return "candidate"

        if row["is_noise"]:
            return "noise"

        if not row["is_state_and_cities"]:
            return "non_cities_and_non_state"

        return "other"


    df["row_type"] = df.apply(
        classify_row,
        axis=1
    )

    # ------------------------------------------
    # Candidate Articles
    # ------------------------------------------

    candidate_df = df[
        df["row_type"] == "candidate"
    ].copy()

    print("\nROW TYPE BREAKDOWN")
    print(
        df["row_type"]
        .value_counts()
    )

    # ------------------------------------------
    # Save Files
    # ------------------------------------------

    df.to_csv(
        OUTPUT_ALL,
        index=False
    )

    candidate_df.to_csv(
        OUTPUT_CANDIDATES,
        index=False
    )

    # ------------------------------------------
    # Stats
    # ------------------------------------------

    print()
    print("====================")
    print("SUMMARY")
    print("====================")

    print(
        f"Total Rows: {len(df)}"
    )

    print(
        f"State and Cities Rows: "
        f"{df['is_state_and_cities'].sum()}"
    )

    print(
        f"Noise Rows: "
        f"{df['is_noise'].sum()}"
    )

    print(
        f"Candidate Rows: "
        f"{len(candidate_df)}"
    )

    print("====================")

    print()
    print("Saved:")

    print(
        OUTPUT_ALL
    )

    print(
        OUTPUT_CANDIDATES
    )

if __name__ == "__main__":
    main()
