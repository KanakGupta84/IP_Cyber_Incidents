import feedparser
from urllib.parse import quote_plus
from pprint import pprint

query = "cyber fraud Maharashtra"

rss_url = (
    "https://news.google.com/rss/search?"
    f"q={quote_plus(query)}"
    "&hl=en-IN"
    "&gl=IN"
    "&ceid=IN:en"
)

print(rss_url)

feed = feedparser.parse(rss_url)

print(f"Entries: {len(feed.entries)}")

entry = feed.entries[0]

pprint(entry)