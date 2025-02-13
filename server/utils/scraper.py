import json
import pandas as pd

import feedparser
from requests_cache import CachedSession
from bs4 import BeautifulSoup
import urllib.parse
import ssl
from googlenewsdecoder import gnewsdecoder

from .pygooglenews import search_news, get_news_search_dates
from .date_helpers import format_published_date
from .text_processing import clean_text

rss_feeds_file = open("input/rss_feeds.json")
RSS_FEEDS = json.load(rss_feeds_file)
rss_feeds_file.close()

# Custom headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
session = CachedSession(cache_name="cache", backend="sqlite", expire_after=3000)


def parse_feed(feed_url):
    try:
        if hasattr(ssl, "_create_unverified_context"):
            ssl._create_default_https_context = ssl._create_unverified_context
        parsed_feed = feedparser.parse(feed_url)
        articles = []
        if parsed_feed.bozo:
            print(f"Error parsing feed {feed_url}: {parsed_feed.bozo_exception}")
        else:
            for entry in parsed_feed.entries:
                date_published = format_published_date(
                    entry.get("published_parsed") or entry.get("published")
                )
                articles.append((entry, date_published))
    except Exception as e:
        print(f"Error parsing feed {feed_url}: {e}")

    return articles


def decode_gnews_url(url):
    try:
        decoded = gnewsdecoder(url)
        if decoded.get("status"):
            return decoded["decoded_url"]
        else:
            return url
    except Exception as e:
        print(f"Error decoding URL {url}: {e}")
        decoded_url = url


"""
Get articles from last 6 months

Parameters:
- queries: list of strings to query
- json_file: string representing the file path
- using_df: boolean value
"""


# get articles from last 6 months
def get_articles(queries=[""], json_file=None, using_df=False, decode_gnews=False):
    articles = []
    seen_titles = set()
    _, six_months_ago_date = get_news_search_dates()

    # Define consistent column order for all entries
    columns = ["source", "entry", "date_published", "is_rss_or_query", "link"]

    # Process RSS feeds
    for source, feed in RSS_FEEDS.items():
        try:
            parsed_articles = parse_feed(feed)
            for entry, date_published in parsed_articles:
                if date_published > format_published_date(six_months_ago_date):
                    articles.append(
                        (
                            (
                                f"Google News: {entry.source.title} "
                                if source.startswith("Google News")
                                else source
                            ),
                            entry,
                            date_published,
                            "RSS Feed",
                            (
                                entry.link
                                if not decode_gnews
                                else decode_gnews_url(entry.link)
                            ),
                        )
                    )
                    seen_titles.add(entry.title.lower())  # Add the title to the set

        except Exception as e:
            print(f"Error fetching articles from {source}: {e}")

    # Process Google News searches
    try:
        for query in queries:
            news_articles = search_news(query)
            for article in news_articles:
                if article.title.lower() not in seen_titles:
                    articles.append(
                        (
                            f"Google News: {article.source.title}",
                            article,
                            format_published_date(
                                article.published_parsed or article.published
                            ),
                            query,
                            article.link,
                        )
                    )
                    seen_titles.add(article.title.lower())
    except Exception as e:
        print(f"Error processing Google News: {e}")

    if using_df:
        if len(articles[0]) != len(columns):
            raise ValueError(
                f"Article tuple length {len(articles[0])} doesn't match columns {len(columns)}"
            )
        df = pd.DataFrame(articles, columns=columns)
        with open("articles.csv", "w") as f:
            df.to_csv(f, index=False)
        return df

    if json_file:
        with open(json_file, "w") as f:
            json.dump(articles, f, indent=4)
        print(f"Saved articles to {json_file}")
    return articles


def get_article_content(url):
    #     """Fetch and extract article text from a given URL."""
    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract article content
        article_content = extract_clean_article(soup)

        # Clean up the extracted text
        return clean_text(article_content)
    except Exception as e:
        print(f"Error getting article content of {url}: {e}")
        return None


def extract_clean_article(
    soup,
    excluded_classes=["ad", "sponsored", "promo", "sidebar", "footer"],
    excluded_keywords=["advertisement", "subscribe", "click here"],
    max_depth=3,
):

    paragraphs = soup.find_all("p")

    clean_paragraphs = []

    for p in paragraphs:
        parent = p
        depth = 0
        exclude = False

        # Traverse up to max_depth levels
        while parent and depth < max_depth:
            parent = parent.find_parent("div")
            if parent:
                # Check class-based exclusion
                if any(cls in parent.get("class", []) for cls in excluded_classes):
                    exclude = True
                    break

                # Check keyword-based exclusion
                if any(
                    keyword in parent.get_text(strip=True).lower()
                    for keyword in excluded_keywords
                ):
                    exclude = True
                    break

            depth += 1

        if not exclude:
            clean_paragraphs.append(p.get_text(strip=True))

    return "\n".join(clean_paragraphs)


# # https://marko.tech/journal/python-rss #TODO: find original source
# def resolve_url(base_url, href):
#     return urllib.parse.urljoin(base_url, href)


# def is_rss_feed(feed_url):
#     try:
#         response = session.head(feed_url, allow_redirects=True)
#         if response.status_code == 200:
#             content_type = response.headers.get("Content-Type", "").lower()
#             if "rss" in content_type or "xml" in content_type:
#                 return True
#     except Exception as e:
#         print(f"Error checking feed URL {feed_url}: {e}")
#     return False


# # Find RSS Links on Page
# def find_rss_links(url):

#     if not url.startswith("http"):
#         url = "https://" + url

#     try:
#         raw = session.get(url).text
#         html = BeautifulSoup(raw, "html.parser")
#     except Exception as e:
#         print(f"Error fetching {url}: {e}")
#         return []

#     # Extract RSS feed links from <link> tags with rel="alternate"
#     feed_urls = html.findAll("link", rel="alternate")
#     result = set()

#     for f in feed_urls:
#         feed_type = f.get("type")
#         if feed_type and ("rss" in feed_type or "xml" in feed_type):
#             href = f.get("href")
#             if href:
#                 result.add(resolve_url(url, href))

#     # Extract RSS feed links from <a> tags
#     base_url = (
#         urllib.parse.urlparse(url).scheme + "://" + urllib.parse.urlparse(url).hostname
#     )
#     atags = html.findAll("a")

#     for a in atags:
#         href = a.get("href")
#         if href and any(keyword in href for keyword in ["xml", "rss", "feed", "atom"]):
#             if is_rss_feed(href):
#                 result.add(resolve_url(url, href))

#     # Check common RSS feed routes if no feed links were found
#     if not result:
#         routes = [
#             "atom.xml",
#             "feed.xml",
#             "rss.xml",
#             "index.xml",
#             "atom.json",
#             "feed.json",
#             "rss.json",
#             "index.json",
#             "feed/",
#             "rss/",
#             "feed/index.xml",
#             "rss/index.xml",
#             "feed/index.json",
#             "rss/index.json",
#             "feed/atom",
#             "rss/atom",
#             "feed/rss",
#             "rss/rss",
#             "feed/atom.xml",
#             "rss/atom.xml",
#             "feed/rss.xml",
#             "rss/rss.xml",
#             "feed/atom.json",
#             "rss/atom.json",
#             "feed/rss.json",
#             "rss/rss.json",
#         ]
#         for route in routes:
#             try:
#                 href = base_url + "/" + route
#                 if is_rss_feed(href):
#                     result.add(href)
#             except Exception as e:
#                 print(f"Error parsing {href}: {e}")
#                 continue

#     # TODO: unsure if needed
#     # Parse the URLs in the result set
#     for feed_url in list(result):
#         f = feedparser.parse(feed_url)
#         if f.entries:
#             result.add(feed_url)

#     return list(result)
