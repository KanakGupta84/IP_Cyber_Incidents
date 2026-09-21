import os
import time
import sys
import pandas as pd
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.chrome import ChromeDriverManager

# from config_keywords_reject_terms.config import STATE

if len(sys.argv) < 2:
    print("Usage: python url_extractor.py <state_name>")
    sys.exit(1)

STATE = sys.argv[1]



INPUT_FILE = f"final_data/candidate_articles_{STATE}.csv"
OUTPUT_FILE = f"data/processed/decoded_url_candidate_articles_{STATE}.csv"

CACHE_FILE = "data/cache/cache_decoded_urls.csv"

CHECKPOINT_EVERY = 25
RESTART_DRIVER_EVERY = 100
WAIT_SECONDS = 1


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

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )

    driver = webdriver.Chrome(
        service=Service(
            ChromeDriverManager().install()
        ),
        options=options
    )

    driver.set_page_load_timeout(5)

    return driver


def get_real_url(driver, url):

    try:

        driver.get(url)

        WebDriverWait(driver, WAIT_SECONDS).until(
            lambda d: "news.google.com" not in d.current_url
        )

        final_url = driver.current_url

        try:
            driver.execute_script("window.stop();")
        except:
            pass

        return final_url

    except Exception:

        try:
            driver.execute_script("window.stop();")
        except:
            pass

        try:
            return driver.current_url
        except:
            return url


# ---------------------------------------
# Create folders
# ---------------------------------------

os.makedirs("data/cache", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

# ---------------------------------------
# Load main dataset
# ---------------------------------------

df = pd.read_csv(INPUT_FILE)

print(f"Loaded {len(df)} URLs")

# ---------------------------------------
# Load cache
# ---------------------------------------

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

# ---------------------------------------
# Resume support
# ---------------------------------------

if os.path.exists(OUTPUT_FILE):

    old_df = pd.read_csv(OUTPUT_FILE)

    if "real_url" in old_df.columns:

        df["real_url"] = old_df["real_url"]

        print(
            "Resuming previous run"
        )

else:

    df["real_url"] = None

# ---------------------------------------
# Apply cache instantly
# ---------------------------------------

cached_hits = 0

for idx in df.index:

    if pd.notna(df.at[idx, "real_url"]):
        continue

    url = df.at[idx, "url"]

    if url in cache_dict:

        df.at[idx, "real_url"] = cache_dict[url]

        cached_hits += 1

print(
    f"Cache hits: {cached_hits}"
)

# ---------------------------------------
# Selenium decoding
# ---------------------------------------

driver = create_driver()

processed_since_restart = 0
newly_decoded = []

try:

    for idx in tqdm(df.index):

        if pd.notna(df.at[idx, "real_url"]):
            continue

        url = df.at[idx, "url"]

        real_url = get_real_url(
            driver,
            url
        )

        df.at[idx, "real_url"] = real_url

        newly_decoded.append(
            {
                "google_url": url,
                "real_url": real_url
            }
        )

        processed_since_restart += 1

        # Save checkpoints

        if processed_since_restart % CHECKPOINT_EVERY == 0:

            df.to_csv(
                OUTPUT_FILE,
                index=False
            )

            if len(newly_decoded) > 0:

                cache_append = pd.DataFrame(
                    newly_decoded
                )

                if os.path.exists(
                    CACHE_FILE
                ):

                    cache_append.to_csv(
                        CACHE_FILE,
                        mode="a",
                        header=False,
                        index=False
                    )

                else:

                    cache_append.to_csv(
                        CACHE_FILE,
                        index=False
                    )

                newly_decoded = []

            print(
                f"\nCheckpoint saved"
            )

        # Restart browser

        if (
            processed_since_restart
            >= RESTART_DRIVER_EVERY
        ):

            print(
                "\nRestarting browser..."
            )

            driver.quit()

            driver = create_driver()

            processed_since_restart = 0

except KeyboardInterrupt:

    print(
        "\nStopping safely..."
    )

# ---------------------------------------
# Final save
# ---------------------------------------

driver.quit()

df.to_csv(
    OUTPUT_FILE,
    index=False
)

if len(newly_decoded) > 0:

    cache_append = pd.DataFrame(
        newly_decoded
    )

    if os.path.exists(
        CACHE_FILE
    ):

        cache_append.to_csv(
            CACHE_FILE,
            mode="a",
            header=False,
            index=False
        )

    else:

        cache_append.to_csv(
            CACHE_FILE,
            index=False
        )

decoded = (
    ~df["real_url"]
    .fillna("")
    .str.contains(
        "news.google.com",
        na=False
    )
).sum()

print("\nFinished")

print(
    f"Decoded URLs: "
    f"{decoded}/{len(df)}"
)

print(
    f"Saved: {OUTPUT_FILE}"
)