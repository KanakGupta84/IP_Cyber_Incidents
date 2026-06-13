import os
import time
import requests
import trafilatura
import pandas as pd
import requests

from langdetect import detect

# INPUT_FILE = "data/deduplicated_url_based/candidate_articles_maharashtra.csv"

# OUTPUT_FILE = "data/raw/raw_articles_noisefilter_maharashtra.csv"

# os.makedirs(
# "data/raw",
# exist_ok=True
# )

# def extract_article(url):

#     try:

#         downloaded = trafilatura.fetch_url(
#             url
#         )

#         if downloaded:

#             text = trafilatura.extract(
#                 downloaded
#             )

#             if text:

#                 return (
#                     text,
#                     "trafilatura",
#                     "success"
#                 )

#     except Exception:
#         pass

#     return (
#         "",
#         "none",
#         "failed"
#     )

# def detect_language(text):

#     try:

#         return detect(text)

#     except Exception:

#         return "unknown"

# def main():

#     df = pd.read_csv(
#         INPUT_FILE
#     )

#     TEST_SIZE = 50
#     df = df.head(TEST_SIZE)
#     print(
#         f"Testing on {len(df)} articles"
#     )

#     records = []

#     total = len(df)

#     for idx, row in df.iterrows():

#         print(
#             f"[{idx+1}/{total}]"
#         )

#         url = row["url"]

#         text, method, status = (
#             extract_article(url)
#         )

#         language = (
#             detect_language(text)
#             if text
#             else "unknown"
#         )

#         record = row.to_dict()

#         record[
#             "article_text"
#         ] = text

#         record[
#             "language"
#         ] = language

#         record[
#             "extraction_method"
#         ] = method

#         record[
#             "extraction_status"
#         ] = status

#         records.append(
#             record
#         )

#         time.sleep(1)

#     result = pd.DataFrame(
#         records
#     )

#     result.to_csv(
#         OUTPUT_FILE,
#         index=False
#     )

#     print()

#     print(
#         f"Saved {len(result)} rows"
#     )

url = "https://news.google.com/rss/articles/CBMi1gFBVV95cUxNTFJyMFlWb29tc0x4T1FIeW5hOHN0eHRmV044bGtUMlRjN0R3b0IxdVNZT2RfTnl2NC1yYlpjeWlyanhnRTJvbFFjRUVHN0JYdW0zQ2szdW56czExREp6RXd0M1liWmI5VUpPUDVRNXNQSWtKTE0wVjRVUHNfU0lTbG4wYS1nS1MwOGdSeFByU0JTY0lCbGxOWFNoWDNiQlYtcVZaOVpEU1BaMmJfUFFnU1JtVXhoYTBSVUVjVzBMdTZQQ05aZ0lrS21kVzhSMklRTXJQSUVR0gHcAUFVX3lxTFBFN1JSVS1aU2xna0N2WEctQjhFRXZHd28tZFp4SXFhSXVDN29sejZmTUhoUmxuVnVPeWY4S04tMHdDNWcxc3AxY0dsR1Z6cVc0MUZQejhCdkdxVUdvQWJaQTBjYl9pUXJuY25OcC14QzNTUURqaTVvWmVENFIwdUlVQ3Bvdnc3ZHc5d0ZKZTFGTkhPc2NmSUM5ZjJxVzEyZ0VSUnZnVzIteXF3VlpqRTNRNFduUjVHY2dpejZtUEFXWmZnbEY4NkFFdjNnWXVEM01xVklTdHV1RWdtQmU?oc=5"

r = requests.get(
    url,
    allow_redirects=True,
    timeout=30,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

print(r.url)

# if __name__ == "__main__":
#     main()
