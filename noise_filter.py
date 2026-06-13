import os
import pandas as pd

INPUT_FILE = "data/deduplicated_url_based/unique_rss_results_maharashtra.csv"

OUTPUT_ALL = "data/deduplicated_url_based/noise_filtered_maharashtra.csv"
OUTPUT_CANDIDATES = "data/deduplicated_url_based/candidate_articles_maharashtra.csv"

os.makedirs("data/processed", exist_ok=True)

# ==================================================
# MAHARASHTRA TERMS
# ==================================================

MAHARASHTRA_TERMS = [

    "maharashtra", "mumbai", "navi mumbai", "bombay",
    "pune", "nagpur", "nashik", "thane", "aurangabad", "chhatrapati sambhajinagar", "kolhapur", "solapur", "amravati",
    "jalgaon", "satara", "latur", "pimpri", "chinchwad", "akola", "ahmednagar", "sangli", "beed", "parbhani",
    "osmanabad", "wardha", "yavatmal", "bhandara", "gondia", "ratnagiri", "sindhudurg", "raigad", "dhule", "buldhana",
    "washim", "hingoli", "nanded", "chandrapur", "gadchiroli", "palghar", "jalna", "bid", "karad", "ichalkaranji",
    "panvel", "vasai", "virar", "bhiwandi", "ulhasnagar", "mira bhayandar", "kalyan", "dombivli", "badlapur", "ambarnath",
    "barshi", "nanded waghala", "gondiya", "achalpur", "deolali", "shirdi", "lonavala", "khopoli", "alibaug", "mahad", 
    "chiplun", "malegaon", "shirpur", "pandharpur", "udgir", "ahmadnagar", "shrirampur", "manmad", "bhusawal", "chalisgaon",

]

# ==================================================
# NOISE TERMS
# ==================================================

REJECT_TERMS = [

    # Awareness
    "awareness campaign", "cyber awareness drive",
    "awareness drive", "cyber awareness", "cyber safety",

    # Tips
    "how to avoid", "how to protect", "safety tips",
    "tips to stay safe", "stay safe", "protect yourself",
    "stay vigilant", "personal safety",

    # Advisory
    "advisory", "issued advisory", "government advisory",
    "warning", "warns citizens", "police warning",

    # Reports
    "survey", "study",
    "research", "statistics", "annual report",

    # Education
    "what is", "explained", "guide to",

    "tops list", "logs",
    "cases in 2026", "cases in 2025", "cases in 2024", "cases in 2023", "cases in 2022", "cases in 2021", "cases in 2020", 
    "cases in 2019", "cases in 2018", "cases in 2017",  
    "report", "statistics", "under scanner",
    "official says", "official urges", "assembly session",
    "chain of command", "policy", "response framework",

    # Government schemes / policy noise (not incidents)
    "loan waiver", "msp scam", "yojana", "scheme launched",
    "crop insurance scheme", "fasal bima",

    # Elections / political noise
    "assembly polls", "municipal election", "civic polls",
    "voters list", "election commission", "poll campaign",
    "vidhan sabha", "lok sabha", "mla", "mlc", "deputy cm", "chief minister",
    "bitcoin scam", "bjp", "congress", "ncp", "shiv sena",

    # QR code mandates / govt initiatives (not fraud incidents)
    "qr code initiative", "qr code mandatory",
    "know your doctor", "verification mandatory",

    # Generic civic/infra/weather news leaking via keyword overlap
    "weather forecast", "rain alert", "imd issues", "monsoon",
    "traffic update", "road closed", "school closed", "public holiday",
    "cabinet approves", "govt orders inquiry", "irrigation scam",
    "land scam", "toll tax",

    # Old/aggregated stat pieces, churnalism
    "sprouts news", "in last 5 years", "in 10 years", "over the years",
    "crosses rs", "tops list",

    # Court/legal procedural updates (not new incidents)
    "grants bail", "denies bail", "anticipatory bail",
    "chargesheet filed", "court rejects", "court grants",

    # Generic finance/market news unrelated to fraud incidents
    "share price", "ipo allotment", "stock market closed",
    "market holiday", "rbi proposes", "rbi launches", "new upi rules", "sebi bans", "sebi advises",
    "sebi launches", "sebi proposes",

]

# ==================================================
# FUNCTIONS
# ==================================================

def check_maharashtra(title):

    title = str(title).lower()

    return any(
        term in title
        for term in MAHARASHTRA_TERMS
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

    df["is_maharashtra"] = (
        df["title"]
        .apply(check_maharashtra)
    )

    df["is_noise"] = (
        df["title"]
        .apply(check_noise)
    )

    def classify_row(row):

        if row["is_maharashtra"] and not row["is_noise"]:
            return "candidate"

        if row["is_noise"]:
            return "noise"

        if not row["is_maharashtra"]:
            return "non_maharashtra"

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
        f"Maharashtra Rows: "
        f"{df['is_maharashtra'].sum()}"
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
