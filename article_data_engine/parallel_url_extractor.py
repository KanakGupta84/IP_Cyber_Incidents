import os
import time
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.chrome import ChromeDriverManager

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

STATE = "Delhi"

INPUT_FILE = f"data/deduplicated_url_based/candidate_articles_{STATE}.csv"
OUTPUT_FILE = f"data/processed/parallel_decoded_articles_{STATE}.csv"
CACHE_FILE = "data/cache/cache_decoded_urls.csv"

MAX_WORKERS = 4
WAIT_SECONDS = 1.5

SCRIPT_START = time.time()

DRIVER_PATH = ChromeDriverManager().install()

# --------------------------------------------------
# DRIVER
# --------------------------------------------------

def create_driver():

    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")

    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--disable-default-apps")
    options.add_argument("--mute-audio")

    options.page_load_strategy = "eager"

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2
    }

    options.add_experimental_option(
        "prefs",
        prefs
    )

    driver = webdriver.Chrome(
        service=Service(DRIVER_PATH),
        options=options
    )

    driver.set_page_load_timeout(5)

    return driver

# --------------------------------------------------
# URL DECODER
# --------------------------------------------------

def get_real_url(driver, url):

    try:

        driver.get(url)

        WebDriverWait(
            driver,
            WAIT_SECONDS
        ).until(
            lambda d:
            "news.google.com"
            not in d.current_url
        )

        try:
            driver.execute_script(
                "window.stop();"
            )
        except:
            pass

        return driver.current_url

    except Exception:

        try:
            return driver.current_url
        except:
            return url

# --------------------------------------------------
# WORKER
# --------------------------------------------------

def process_chunk(chunk_df):

    print(
        f"Worker started with {len(chunk_df)} URLs"
    )

    driver = create_driver()

    results = []

    try:

        for idx, row in chunk_df.iterrows():

            real_url = get_real_url(
                driver,
                row["url"]
            )

            results.append(
                (
                    idx,
                    real_url
                )
            )

    finally:

        driver.quit()

    print(
        f"Worker finished {len(results)} URLs"
    )

    return results

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print(
    f"Loaded {len(df)} URLs"
)

df["real_url"] = None

# --------------------------------------------------
# LOAD CACHE
# --------------------------------------------------

cache_dict = {}

if os.path.exists(CACHE_FILE):

    cache_df = pd.read_csv(CACHE_FILE)

    cache_dict = dict(
        zip(
            cache_df["google_url"],
            cache_df["real_url"]
        )
    )

    print(
        f"Loaded {len(cache_dict)} cached URLs"
    )

cached_hits = 0

for idx in df.index:

    url = df.at[idx, "url"]

    if url in cache_dict:

        df.at[
            idx,
            "real_url"
        ] = cache_dict[url]

        cached_hits += 1

print(
    f"Cache hits: {cached_hits}"
)

# --------------------------------------------------
# FIND PENDING URLS
# --------------------------------------------------

pending_df = df[
    df["real_url"].isna()
].copy()

print(
    f"URLs needing decode: {len(pending_df)}"
)

if len(pending_df) == 0:

    print(
        "Nothing to decode."
    )

    exit()

# --------------------------------------------------
# SPLIT WORK
# --------------------------------------------------

chunk_size = (
    len(pending_df)
    // MAX_WORKERS
) + 1

chunks = [

    pending_df.iloc[
        i:i + chunk_size
    ].copy()

    for i in range(
        0,
        len(pending_df),
        chunk_size
    )
]

print(
    f"Created {len(chunks)} chunks"
)

# --------------------------------------------------
# PARALLEL EXECUTION
# --------------------------------------------------

try:

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = [

            executor.submit(
                process_chunk,
                chunk
            )

            for chunk in chunks
        ]

        for future in tqdm(
            as_completed(futures),
            total=len(futures)
        ):

            try:

                results = future.result()

            except Exception as e:

                print(
                    f"Worker failed: {e}"
                )

                continue

            for idx, real_url in results:

                df.at[
                    idx,
                    "real_url"
                ] = real_url

except KeyboardInterrupt:

    print(
        "\nStopped by user"
    )

# --------------------------------------------------
# UPDATE CACHE
# --------------------------------------------------

new_cache_rows = df[
    df["real_url"].notna()
][
    ["url", "real_url"]
].copy()

new_cache_rows.columns = [
    "google_url",
    "real_url"
]

if os.path.exists(CACHE_FILE):

    old_cache = pd.read_csv(
        CACHE_FILE
    )

    combined = pd.concat(
        [
            old_cache,
            new_cache_rows
        ],
        ignore_index=True
    )

    combined = combined.drop_duplicates(
        subset=["google_url"]
    )

else:

    combined = new_cache_rows

combined.to_csv(
    CACHE_FILE,
    index=False
)

# --------------------------------------------------
# SAVE OUTPUT
# --------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

decoded = (
    df["real_url"]
    .notna()
    .sum()
)

elapsed = (
    time.time()
    - SCRIPT_START
)

print("\nFinished")

print(
    f"Decoded URLs: "
    f"{decoded}/{len(df)}"
)

print(
    f"Saved: {OUTPUT_FILE}"
)

print(
    f"Total Time: "
    f"{elapsed:.2f} sec"
)

print(
    f"Average Time: "
    f"{elapsed/len(df):.2f} sec/url"
)