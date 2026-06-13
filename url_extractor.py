import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config_keywords_reject_terms.config import STATE

tqdm.pandas()

INPUT_FILE = "data/deduplicated_url_based/candidate_articles_" + STATE + ".csv"
OUTPUT_FILE = "data/processed/main_article_" + STATE + ".csv"

# Setup headless Chrome
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

driver = create_driver()

def get_real_url(google_url):
    try:
        driver.get(google_url)
        # Wait for redirect to complete
        import time
        time.sleep(2)
        final_url = driver.current_url
        
        # If still on google, wait a bit more
        if "google.com" in final_url:
            time.sleep(2)
            final_url = driver.current_url
        
        return final_url
    except:
        return google_url

df = pd.read_csv(INPUT_FILE)
print(f"Total URLs to process: {len(df)}")

df["real_url"] = df["url"].head(5).progress_apply(get_real_url)

# Cleanup
driver.quit()

# Stats
success = df[~df["real_url"].str.contains("google.com", na=False)]
print(f"\nSuccessfully decoded: {len(success)}/{len(df)}")

df.to_csv(OUTPUT_FILE, index=False)
print(f"Saved to {OUTPUT_FILE}")
print(df[["url", "real_url"]].head(10))