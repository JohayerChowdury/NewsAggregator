import os
import json

from pygooglenews import GoogleNews
from googlenewsdecoder import gnewsdecoder

from ..utils import get_news_search_dates

# TODO: Yunji provided financing glossary, look into those terms and add them here
GOOGLE_NEWS_SEARCH_QUERIES = [
    # "Canadian accessory dwelling unit",  # NOTE: looks like adding "Canadian" doesn't work well
    # "Canadian mortgage regulations",
    "zoning laws in Toronto, Ontario",
    # "accessory dwelling unit",
    # "mortgage regulations",
    # # TODO: look into how these queries are being used
    # "purchase financing",
    # "renovation financing",
    # "construction financing",
    # "private financing",
    # "mortgage financing",
    # "home equity financing",
    # "refinancing mortgage",
    # "multiplex conversion",
    # "multiplex renovation",
    # "multiplex financing",
    # "multiplex construction",
    # "multiplex purchase",
    # "multiplex refinance",
]

# Initialize GoogleNews with Canadian settings
gn = GoogleNews(lang="en", country="CA")


def decode_gnews_url(url):
    try:
        decoded = gnewsdecoder(url)
        if decoded.get("status"):
            return decoded["decoded_url"]
    except Exception as e:
        print(f"Error decoding URL {url}: {e}")
    return url


def search_news(query, from_=None, to_=None):
    if not from_ and not to_:
        today_date, six_months_ago_date = get_news_search_dates()
        from_ = six_months_ago_date
        to_ = today_date
    result = gn.search(query, from_=from_, to_=to_)
    articles = result["entries"]
    return articles


def retrieve_articles_from_google_news(decode_gnews: bool = False) -> list:
    entries = []
    for query in GOOGLE_NEWS_SEARCH_QUERIES:
        articles_from_query = search_news(query)
        for entry in articles_from_query:
            entries.append(
                {
                    "data_source": f"Google News: {query}",
                    "data_entry": entry,
                    "article_link": (
                        decode_gnews_url(entry.link) if decode_gnews else entry.link
                    ),
                }
            )
    return entries


def main() -> list:
    articles = retrieve_articles_from_google_news()
    return articles


if __name__ == "__main__":
    main()
