import json
import pandas as pd

import feedparser
from requests_cache import CachedSession
from bs4 import BeautifulSoup
import ssl
from googlenewsdecoder import gnewsdecoder

from .pygooglenews import search_news, get_news_search_dates
from .date_helpers import standardize_date, serialize_datetime
from .text_processing import filter_text_content, normalize_html_content


# Add the appropriate RSS feeds
# RSS_FEEDS = {
# "Canadian Mortgage Trends": "https://www.canadianmortgagetrends.com/feed/",  # works
# "Google News: Canadian Accessory Dwelling Unit": "https://news.google.com/rss/search?q=canadian%20accessory%20dwelling%20unit&hl=en-CA&gl=CA&ceid=CA%3Aen",  # works
# "Government of Canada: Finance": "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentfinance&type=newsreleases&sort=publishedDate&orderBy=desc&publishedDate%3E=2020-08-09&pick=100&format=atom&atomtitle=Canada%20News%20Centre%20-%20Department%20of%20Finance%20Canada%20-%20News%20Releases",  # doesnt work,
# TODO: look into podcasts and how to parse them
# "Podcast: The Hidden Upside: Real Estate": "https://feeds.libsyn.com/433605/rss",
# "Podcast: The Real Estate REplay": "https://feeds.buzzsprout.com/1962859.rss", # doesnt work (for now)
# }

# TODO: stay away from company websites (have sales objectives that have "vendor" stuff)
# WEBSITES = {
# "Accessorry Dwelling Finance News": "https://accessorydwellings.org/category/news/financing-news/",
# "Flexobuild News": "https://flexobuild.com/media" # not works
# }

rss_feeds_file = open("input/rss_feeds.json")
RSS_FEEDS = json.load(rss_feeds_file)
rss_feeds_file.close()

# TODO: Yunji provided financing glossary, look into those terms and add them here
GOOGLE_NEWS_SEARCH_QUERIES = [
    # "Canadian accessory dwelling unit",  # NOTE: looks like adding "Canadian" doesn't work well
    # "Canadian mortgage regulations",
    # "Canadian zoning laws in Toronto",
    # "zoning laws",
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

# Custom headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
session = CachedSession(cache_name="cache", backend="sqlite", expire_after=3000)


def load_json_to_df(filename: str, expected_columns: list) -> pd.DataFrame:
    """Load a JSON file into a Pandas DataFrame and ensure expected columns."""
    try:
        print(f"Loading {filename}...")
        with open(filename, "r") as file:
            data = json.load(file)  # Load JSON manually to handle missing fields

        df = pd.DataFrame(data)  # Convert to DataFrame
        df = df.reindex(columns=expected_columns)  # Ensure all expected columns exist
        if df.empty:
            print(f"Warning: {filename} is empty. Returning an empty DataFrame.")
        return df
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error: Unable to read {filename}. Returning an empty DataFrame.")
        return pd.DataFrame(columns=expected_columns)


def save_df_to_json(df: pd.DataFrame, filename: str) -> None:
    try:
        """Save a DataFrame to a JSON file."""
        print(f"Saving {filename}...")
        df.to_json(filename, orient="records", indent=4)  # Save as a list of records
        print(f"Saved {filename}.")
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        raise e


required_columns = [
    "link",
    "extracted_link_url",
    "source",
    "date_published",
    "title",
    "summary",  # useless
    "from_rss_or_query",
    "entry",
]
# "extracted_content",


def check_for_required_columns(df, required_columns):
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        print("DF columns are: ", df.columns)
        raise KeyError(f"Missing required columns: {missing}")


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
                date_published = standardize_date(
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

    except Exception as e:
        print(f"Error decoding URL {url}: {e}")
    return url


def get_articles_from_rss_feeds(
    seen_titles, articles_df, six_months_ago_date, decode_gnews
):
    for source, feed in RSS_FEEDS.items():
        try:
            parsed_articles = parse_feed(feed)
            for entry, date_published in parsed_articles:

                if (
                    entry.link in articles_df["link"].values
                    or entry.link in seen_titles
                ):
                    continue
                if date_published > standardize_date(six_months_ago_date):
                    link_url = (
                        entry.link if not decode_gnews else decode_gnews_url(entry.link)
                    )
                    new_row = pd.DataFrame(
                        {
                            "link": [entry.link],
                            "extracted_link_url": [link_url],
                            "source": [
                                (
                                    f"Google News: {entry.source.title} "
                                    if source.startswith("Google News")
                                    else source
                                )
                            ],
                            "date_published": [date_published],
                            "title": [entry.title],
                            "summary": [normalize_html_content(entry.summary)],
                            "from_rss_or_query": ["RSS Feed"],
                            "entry": [entry],
                            "extracted_content": [""],
                        },
                    )

                    articles_df = pd.concat([articles_df, new_row], ignore_index=True)
                    seen_titles.add(entry.link)

        except Exception as e:
            print(f"Error fetching articles from {source}: {e}")
    return articles_df


# get articles from last 6 months
def get_articles(article_file, queries=[""], decode_gnews=False):

    initial_articles_df = load_json_to_df(
        article_file, expected_columns=required_columns
    )
    if not initial_articles_df.empty:
        seen_titles = set(initial_articles_df["link"])
    else:
        seen_titles = set()
    _, six_months_ago_date = get_news_search_dates()

    # Process RSS feeds
    articles_df = get_articles_from_rss_feeds(
        seen_titles, initial_articles_df, six_months_ago_date, decode_gnews
    )

    # Process Google News searches
    try:
        for query in queries:
            news_articles = search_news(query)
            for article in news_articles:
                if article["link"] not in seen_titles:
                    link_url = (
                        article.link
                        if not decode_gnews
                        else decode_gnews_url(article.link)
                    )
                    new_row = pd.DataFrame(
                        {
                            "link": [article.link],
                            "extracted_link_url": [link_url],
                            "source": f"Google News: {article.source.title}",
                            "date_published": [
                                standardize_date(
                                    article.published_parsed or article.published
                                )
                            ],
                            "title": [article.title],
                            "summary": [normalize_html_content(article.summary) or ""],
                            "from_rss_or_query": [query],
                            "entry": [article],
                            "extracted_content": [""],
                        },
                    )
                    articles_df = pd.concat([articles_df, new_row])
                    seen_titles.add(article.link)
    except Exception as e:
        print(f"Error processing Google News: {e}")

    save_df_to_json(articles_df, article_file)
    return articles_df


def fetch_article_soup(url):
    #     """Fetch and extract article text from a given URL."""
    try:
        response = session.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")

    try:
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching article content of {url}")
        print(e)
        return None


def extract_clean_article(
    url,
    excluded_classes=["ad", "sponsored", "promo", "sidebar", "footer"],
    excluded_keywords=["advertisement", "subscribe", "click here"],
    max_depth=3,
):
    soup = fetch_article_soup(url)
    if not soup:
        return ""
    p_tags = soup.find_all("p")

    clean_paragraphs = []

    for p in p_tags:
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

    return str(filter_text_content("\n".join(clean_paragraphs)))


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
