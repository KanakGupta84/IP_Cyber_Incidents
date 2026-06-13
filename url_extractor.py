import pandas as pd
from gnews import GNews

google_news = GNews()

df = pd.read_csv("your_file.csv")

def get_real_url(google_url):
    try:
        article = google_news.get_full_article(google_url)
        return article.url if article else google_url
    except:
        return google_url

df["real_url"] = df["url"].apply(get_real_url)  # replace "url" with your column name

df.to_csv("output.csv", index=False)
print(df[["url", "real_url"]].head())