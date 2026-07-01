"""
Cyber-scam-news -> relational SQLite pipeline
================================================

Converts rows like full_articles_<STATE>.csv into the INCIDENTS / PLATFORM_USED /
LOCATION / ACCUSED_NAME / VICTIM_NAMES / SCAM_CATEGORY schema, using Claude for
extraction and a grounding check to catch hallucinated facts before they hit the DB.

Pipeline stages
---------------
1. load_and_filter()      -- drop noise rows, rows with no article_text
2. build_batch_requests() -- one forced-tool-use request per row (temp=0)
3. submit_and_wait()      -- Message Batches API (50% cheaper, async)
4. validate_and_extract() -- grounding check: every extracted string/number
                              must appear in the source article_text, or it's
                              dropped to NULL and logged to review_log.csv
5. insert_into_db()       -- single transaction, executemany

Run:
    export ANTHROPIC_API_KEY=...
    python pipeline.py full_articles_Uttar_Pradesh.csv scams.db --state "Uttar Pradesh"

Run for every state file in a folder:
    python pipeline.py --all ./state_csvs/ scams.db
"""

import argparse
import glob
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

import pandas as pd
import anthropic

MODEL = "claude-sonnet-4-6"  # good accuracy/cost tradeoff for extraction

# ---------------------------------------------------------------------------
# 1. Schema handed to the model as a forced tool call.
#    Keep this MINIMAL -- every field here is a field the model can hallucinate.
#    date_of_reporting / news_url / news_source are NOT here: we already have
#    them from the CSV columns, so they're assigned in code, not inferred.
# ---------------------------------------------------------------------------
EXTRACTION_TOOL = {
    "name": "record_incident",
    "description": (
        "Record structured facts about a cyber-fraud/scam news article. "
        "Only include a fact if it is explicitly stated in the article text. "
        "If something is not mentioned, dont try to forcefully file it use null/empty list. "
        "Never infer, estimate, or guess a value that isn't stated."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "is_specific_incident": {
                "type": "boolean",
                "description": (
                    "True only if the article describes a specific, identifiable "
                    "fraud incident (a particular victim/case/FIR/or about busting a gang/buiness which is"
                    "doing fraud related to tech). False if it is "
                    "a general awareness piece, advisory, statistic roundup, or "
                    "policy announcement with no single incident or a praise news regaring the efficiency of the police"
                ),
            },
            "amount_lost": {
                "type": ["integer", "null"],
                "description": (
                    "Total amount lost in INR as a plain integer, if an "
                    "explicit figure is stated in the text (e.g. 'lost Rs 12 lakh' "
                    "-> 1200000) then convert that into a plain integer , using simple conversion like 1 lakh = 100000"
                    "and 1 crore = 10000000 "
                    ". Null if no figure is given or the article is not "
                    "about a specific incident."
                ),
            },
            "victim_count": {
                "type": ["integer", "null"],
                "description": (
                    "Number of victims explicitly stated or countable from named "
                    "individuals in the article (e.g. 'over 50 people duped' -> 50; "
                    "if only one victim is described, use 1). Null if no count or "
                    "named victim is given."
                ),
            },
            "accused_count": {
                "type": ["integer", "null"],
                "description": (
                    "Number of accused/arrested individuals explicitly stated or "
                    "countable from named individuals in the article (e.g. 'a gang "
                    "of 4 arrested' -> 4; if only one accused is named, use 1). "
                    "Null if no count or named accused is given."
                ),
            },
            "summary": {
                "type": "string",
                "description":  " 50 word sentence summary of the incident in your own words. capuring the main details no filler words",
            },
            "platforms": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Apps/platforms named as used in the scam (e.g. WhatsApp, UPI, Telegram). if they made there own custome fake website/app to fraud people then simple "
                "using custom app or custom website" ,
            },
            "locations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "city": {"type": ["string", "null"]},
                        "state": {"type": ["string", "null"]},
                        "location_role": {
                            "type": "string",
                            "enum": ["incident_location", "victim_location", "accused_location", "other"],
                        },
                    },
                    "required": ["location_role"],
                },
            },
            "accused_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Full names of accused/arrested individuals explicitly named in "
                    "the article. Do not include vague references like 'the accused' "
                    "or 'a gang member' -- only actual names stated in the text. "
                    "Empty list if no one is named."
                ),
            },
            "victim_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Full names of victims explicitly named in the article. Do not "
                    "include vague references like 'the victim' or 'a resident' -- "
                    "only actual names stated in the text. Empty list if no one is "
                    "named (common when the article withholds victim identity)."
                ),
            },
            "scam_categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "The type(s) of scam, using the article's own wording where "
                    "possible (e.g. if the article says 'digital arrest scam', use "
                    "that phrase rather than substituting a different term like "
                    "'impersonation fraud'). Do not introduce a category label that "
                    "isn't reflected in the article's own language. if nothing of the can be get dont force to write anything ,use NULL"
                ),
            },
        },
        "required": [
            "is_specific_incident", "summary", "platforms", "locations",
            "accused_names", "victim_names", "scam_categories",
        ],
    },
}

SYSTEM_PROMPT = (
    "You extract facts from the csv given to you in which you have to use the article_text , "
    "the articles about cyber fraud for a research "
    "database. You must be strictly grounded: only report what the article text "
    "explicitly says. Do not use outside knowledge about the case. Do not fill in "
    "plausible-sounding details. When unsure, leave the field null/empty. Always "
    "respond by calling the record_incident tool."
)


# ---------------------------------------------------------------------------
# 2. Load + filter
# ---------------------------------------------------------------------------
def load_and_filter(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[df["is_noise"] == False]                 # drop flagged noise
    df = df[df["article_text"].notna()]               # need text to extract from
    df = df[df["article_text"].str.len() > 200]        # drop stubs/empty scrapes
    df = df.reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# 3. Build batch requests
# ---------------------------------------------------------------------------
def build_batch_requests(df: pd.DataFrame) -> list:
    requests = []
    for i, row in df.iterrows():
        text = str(row["article_text"])[:15000]  # guard against extreme outliers
        requests.append({
            "custom_id": f"row-{i}",
            "params": {
                "model": MODEL,
                "max_tokens": 1500,
                "temperature": 0,
                "system": SYSTEM_PROMPT,
                "tools": [EXTRACTION_TOOL],
                "tool_choice": {"type": "tool", "name": "record_incident"},
                "messages": [
                    {"role": "user", "content": f"Article title: {row['title']}\n\nArticle text:\n{text}"}
                ],
            },
        })
    return requests


# ---------------------------------------------------------------------------
# 4. Submit to Message Batches API and wait
# ---------------------------------------------------------------------------
def submit_and_wait(client: anthropic.Anthropic, requests: list, checkpoint_stem: str,
                     poll_seconds: int = 30) -> dict:
    """Submits requests as a Message Batch, with two layers of resumability:

    1. If results were already fetched in a prior run, `<stem>.results.jsonl`
       exists on disk -- load from there and make ZERO API calls.
    2. Otherwise, if a batch was already submitted in a prior run but the
       script died before results were fetched (crash, network drop, Ctrl-C),
       `<stem>.batch_id.txt` exists -- reuse that batch instead of paying to
       resubmit the same rows again.

    Returns a dict of custom_id -> {"succeeded": bool, "tool_input": dict|None},
    a JSON-serializable simplified form (not raw SDK objects) so it round-trips
    cleanly through the results cache file.
    """
    results_file = f"{checkpoint_stem}.results.jsonl"
    batch_id_file = f"{checkpoint_stem}.batch_id.txt"

    if os.path.exists(results_file):
        print(f"  Found cached results at {results_file} -- skipping API entirely.")
        results = {}
        with open(results_file) as f:
            for line in f:
                obj = json.loads(line)
                results[obj["custom_id"]] = obj
        return results

    if os.path.exists(batch_id_file):
        with open(batch_id_file) as f:
            batch_id = f.read().strip()
        print(f"  Resuming previously submitted batch {batch_id} (no new charge).")
    else:
        batch = client.messages.batches.create(requests=requests)
        batch_id = batch.id
        with open(batch_id_file, "w") as f:
            f.write(batch_id)
        print(f"  Submitted batch {batch_id} with {len(requests)} requests")

    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        print(f"  status={batch.processing_status} "
              f"succeeded={counts.succeeded} errored={counts.errored} "
              f"processing={counts.processing}")
        if batch.processing_status == "ended":
            break
        time.sleep(poll_seconds)

    # Write results to disk AS WE GO, not after the loop -- so if this process
    # dies mid-write, the *next* run's file has whatever landed, not nothing.
    results = {}
    with open(results_file, "w") as f:
        for r in client.messages.batches.results(batch_id):
            succeeded = r.result.type == "succeeded"
            tool_input = None
            if succeeded:
                tool_call = next((b for b in r.result.message.content if b.type == "tool_use"), None)
                if tool_call is not None:
                    tool_input = tool_call.input
            record = {"custom_id": r.custom_id, "succeeded": succeeded, "tool_input": tool_input}
            results[r.custom_id] = record
            f.write(json.dumps(record) + "\n")
            f.flush()

    return results


# ---------------------------------------------------------------------------
# 5. Grounding validation -- the actual anti-hallucination gate
# ---------------------------------------------------------------------------
def _in_text(value: str, text: str) -> bool:
    if not value:
        return False
    return value.strip().lower() in text.lower()


def _resolve_count(model_count, grounded_names: list):
    """Reconcile the model's stated count against names that survived grounding.

    Named individuals are directly grounded evidence (each one was independently
    verified to appear in the article text), so if the model listed 5 grounded
    victim names but only said victim_count=2 (or said nothing), we trust the
    names over the number. If no names were extracted at all (e.g. 'over 50
    people duped', no one named), we fall back to the model's stated count.
    Returns (final_count, was_corrected).
    """
    named = len(grounded_names)
    if model_count is None:
        return (named if named else None), False
    if named > model_count:
        return named, True
    return model_count, False


def _amount_in_text(amount: int, text: str) -> bool:
    """Loose check: does some digit-grouping of this number appear in the text,
    or a lakh/crore expression that resolves to it. Not exhaustive by design --
    false negatives (over-cautious NULLing) are far cheaper than false positives."""
    if amount is None:
        return False
    plain = str(amount)
    with_commas = f"{amount:,}"
    if plain in text or with_commas in text:
        return True
    # common Indian phrasing: "12 lakh" == 1,200,000 ; "2.5 crore" == 25,000,000
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*lakh", text, re.IGNORECASE):
        if abs(float(m.group(1)) * 100_000 - amount) < 1:
            return True
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*crore", text, re.IGNORECASE):
        if abs(float(m.group(1)) * 10_000_000 - amount) < 1:
            return True
    return False


def validate_and_extract(df: pd.DataFrame, results: dict, state_hint: str, review_log_path: str) -> list:
    """Returns a list of dicts ready for DB insertion. Writes dropped/flagged
    facts to review_log_path for manual audit."""
    records = []
    review_rows = []

    for i, row in df.iterrows():
        cid = f"row-{i}"
        r = results.get(cid)
        text = str(row["article_text"])

        base = {
            "date_of_reporting": row.get("published_date"),
            "news_url": row.get("real_url") or row.get("url"),
            "news_source": row.get("source"),
            "is_awareness": None,
            "amount_lost": None,
            "victim_count": None,
            "accused_count": None,
            "summary": None,
            "platforms": [],
            "locations": [],
            "accused_names": [],
            "victim_names": [],
            "scam_categories": [],
        }

        if r is None or not r.get("succeeded"):
            review_rows.append({"custom_id": cid, "issue": "batch_failed_or_missing", "url": base["news_url"]})
            records.append(base)
            continue

        data = r.get("tool_input")
        if data is None:
            review_rows.append({"custom_id": cid, "issue": "no_tool_call", "url": base["news_url"]})
            records.append(base)
            continue

        base["is_awareness"] = "False" if data.get("is_specific_incident") else "True"
        base["summary"] = data.get("summary")

        # --- amount_lost: must be grounded in the article text ---
        amt = data.get("amount_lost")
        if amt is not None:
            if _amount_in_text(amt, text):
                base["amount_lost"] = amt
            else:
                review_rows.append({"custom_id": cid, "issue": "amount_not_grounded",
                                     "value": amt, "url": base["news_url"]})

        # --- string entities: must be substrings of the article text ---
        for plat in data.get("platforms", []):
            if _in_text(plat, text):
                base["platforms"].append(plat)
            else:
                review_rows.append({"custom_id": cid, "issue": "platform_not_grounded",
                                     "value": plat, "url": base["news_url"]})

        for name in data.get("accused_names", []):
            if _in_text(name, text):
                base["accused_names"].append(name)
            else:
                review_rows.append({"custom_id": cid, "issue": "accused_name_not_grounded",
                                     "value": name, "url": base["news_url"]})

        for name in data.get("victim_names", []):
            if _in_text(name, text):
                base["victim_names"].append(name)
            else:
                review_rows.append({"custom_id": cid, "issue": "victim_name_not_grounded",
                                     "value": name, "url": base["news_url"]})

        # --- counts: derived AFTER names are grounded, since grounded names are
        # stronger evidence than the model's separately-stated number ---
        base["victim_count"], victim_mismatch = _resolve_count(
            data.get("victim_count"), base["victim_names"])
        base["accused_count"], accused_mismatch = _resolve_count(
            data.get("accused_count"), base["accused_names"])
        if victim_mismatch:
            review_rows.append({"custom_id": cid, "issue": "victim_count_corrected_from_names",
                                 "value": f"model_said={data.get('victim_count')} names_found={len(base['victim_names'])}",
                                 "url": base["news_url"]})
        if accused_mismatch:
            review_rows.append({"custom_id": cid, "issue": "accused_count_corrected_from_names",
                                 "value": f"model_said={data.get('accused_count')} names_found={len(base['accused_names'])}",
                                 "url": base["news_url"]})

        for cat in data.get("scam_categories", []):
            if _in_text(cat, text):
                base["scam_categories"].append(cat)
            else:
                review_rows.append({"custom_id": cid, "issue": "scam_category_not_grounded",
                                     "value": cat, "url": base["news_url"]})

        for loc in data.get("locations", []):
            city, st = loc.get("city"), loc.get("state")
            city_ok = city is None or _in_text(city, text)
            state_ok = st is None or _in_text(st, text)
            if city_ok and state_ok:
                base["locations"].append({
                    "city": city,
                    "state": st or state_hint,
                    "location_role": loc.get("location_role", "other"),
                })
            else:
                review_rows.append({"custom_id": cid, "issue": "location_not_grounded",
                                     "value": f"{city},{st}", "url": base["news_url"]})

        records.append(base)

    if review_rows:
        pd.DataFrame(review_rows).to_csv(review_log_path, index=False)
        print(f"Logged {len(review_rows)} flagged/dropped facts to {review_log_path}")

    return records


# ---------------------------------------------------------------------------
# 6. Insert into SQLite
# ---------------------------------------------------------------------------
def get_existing_urls(db_path: str) -> set:
    """URLs already present in INCIDENTS -- used to skip re-inserting rows from
    a state whose extraction was already committed in a prior (possibly
    interrupted) run."""
    if not os.path.exists(db_path):
        return set()
    conn = sqlite3.connect(db_path)
    urls = {row[0] for row in conn.execute(
        "SELECT news_url FROM INCIDENTS WHERE news_url IS NOT NULL")}
    conn.close()
    return urls


def insert_into_db(records: list, db_path: str):
    existing_urls = get_existing_urls(db_path)
    skipped = 0

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    for rec in records:
        if rec.get("news_url") and rec["news_url"] in existing_urls:
            skipped += 1
            continue

        cur.execute(
            """INSERT INTO INCIDENTS
               (date_of_reporting, is_awareness, amount_lost, news_url, news_source,
                victim_count, accused_count, summary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (rec["date_of_reporting"], rec["is_awareness"], rec["amount_lost"],
             rec["news_url"], rec["news_source"], rec["victim_count"],
             rec["accused_count"], rec["summary"]),
        )
        incident_id = cur.lastrowid

        cur.executemany(
            "INSERT INTO PLATFORM_USED (incident_id, platform_name) VALUES (?, ?)",
            [(incident_id, p) for p in rec["platforms"]],
        )
        cur.executemany(
            "INSERT INTO LOCATION (incident_id, city, state, location_role) VALUES (?, ?, ?, ?)",
            [(incident_id, l.get("city"), l.get("state"), l.get("location_role")) for l in rec["locations"]],
        )
        cur.executemany(
            "INSERT INTO ACCUSED_NAME (incident_id, accused_name) VALUES (?, ?)",
            [(incident_id, n) for n in rec["accused_names"]],
        )
        cur.executemany(
            "INSERT INTO VICTIM_NAMES (incident_id, victim_name) VALUES (?, ?)",
            [(incident_id, n) for n in rec["victim_names"]],
        )
        cur.executemany(
            "INSERT INTO SCAM_CATEGORY (incident_id, scam_name) VALUES (?, ?)",
            [(incident_id, c) for c in rec["scam_categories"]],
        )

    conn.commit()
    conn.close()
    inserted = len(records) - skipped
    print(f"Inserted {inserted} incidents into {db_path}"
          + (f" ({skipped} skipped -- already present from a prior run)" if skipped else ""))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def run_one_state(csv_path: str, db_path: str, state_hint: str, client: anthropic.Anthropic):
    print(f"\n=== {csv_path} ===")
    df = load_and_filter(csv_path)
    print(f"{len(df)} rows after filtering")

    requests = build_batch_requests(df)
    checkpoint_stem = str(Path(csv_path).with_suffix(""))
    results = submit_and_wait(client, requests, checkpoint_stem)

    review_log = checkpoint_stem + "_review_log.csv"
    records = validate_and_extract(df, results, state_hint, review_log)

    insert_into_db(records, db_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_or_folder")
    ap.add_argument("db_path")
    ap.add_argument("--state", default=None, help="State name to use as fallback for LOCATION.state")
    ap.add_argument("--all", action="store_true", help="Treat csv_or_folder as a folder of state CSVs")
    args = ap.parse_args()

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    if args.all:
        for csv_path in sorted(glob.glob(os.path.join(args.csv_or_folder, "*.csv"))):
            # infer state name from filename, e.g. full_articles_Uttar_Pradesh.csv
            stem = Path(csv_path).stem.replace("full_articles_", "").replace("_", " ")
            run_one_state(csv_path, args.db_path, stem, client)
    else:
        state = args.state or Path(args.csv_or_folder).stem.replace("full_articles_", "").replace("_", " ")
        run_one_state(args.csv_or_folder, args.db_path, state, client)


if __name__ == "__main__":
    main()