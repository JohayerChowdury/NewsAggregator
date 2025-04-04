import aiohttp
import asyncio
import feedparser
from feedparser import FeedParserDict
import ssl
import json

from ..models import NewsItemSchema, ValidationError, PydanticJson

# This object is for seeing which RSS feeds are working and which are not
RSS_FEEDS_JSON = {
    "Canadian Mortgage Trends": "https://www.canadianmortgagetrends.com/feed/",  # works
    # "Government of Canada: Finance": "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentfinance&type=newsreleases&sort=publishedDate&orderBy=desc&publishedDate%3E=2020-08-09&pick=100&format=atom&atomtitle=Canada%20News%20Centre%20-%20Department%20of%20Finance%20Canada%20-%20News%20Releases",  # doesnt work,
    # TODO: look into podcasts and how to parse them
    # "Podcast: The Hidden Upside: Real Estate": "https://feeds.libsyn.com/433605/rss",
    # "Podcast: The Real Estate REplay": "https://feeds.buzzsprout.com/1962859.rss",  # doesnt work (for now)
}

RSS_FEEDS = ["https://www.canadianmortgagetrends.com/feed/"]

# Create an SSL context to ignore verification
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


async def fetch_feed(session, feed_url):
    """
    Fetch the RSS feed content asynchronously with optional SSL bypass.

    :param session: The aiohttp session.
    :param feed_url: The URL of the RSS feed.
    """
    try:
        async with session.get(feed_url, ssl=ssl_context) as response:
            content = await response.text()
            parsed_feed = feedparser.parse(content)
            return parsed_feed
    except Exception as e:
        print(f"Error fetching feed {feed_url}: {e}")
        return None


async def extract_articles_from_feed(feed_url) -> list:
    """
    Extract articles from a given RSS feed URL asynchronously.

    :param feed_url: The URL of the RSS feed.
    """
    articles = []
    try:
        async with aiohttp.ClientSession() as session:
            parsed_feed = await fetch_feed(session, feed_url)
            if parsed_feed and parsed_feed.entries:
                for entry in parsed_feed.entries:
                    try:
                        # Convert FeedParserDict to a regular dict
                        entry_dict = {k: v for k, v in entry.items()}
                        articles.append(entry_dict)
                    except Exception as e:
                        print(f"Error processing entry: {e}")
    except Exception as e:
        print(f"Error parsing feed {feed_url}: {e}")

    return articles


async def retrieve_articles_from_rss_feeds() -> list[NewsItemSchema]:
    """
    Retrieve articles from all RSS feeds concurrently.
    """
    tasks = []
    for feed_url in RSS_FEEDS:
        tasks.append(extract_articles_from_feed(feed_url))

    results = await asyncio.gather(*tasks)

    news_items = [NewsItemSchema]
    for feed_url, articles_from_feed in zip(RSS_FEEDS, results):
        for entry in articles_from_feed:
            try:
                entry_str = json.dumps(entry)

                # Validate the news item against the NewsItemBase model
                news_item = NewsItemSchema(
                    data_source_type="Specific RSS Feed",
                    data_json=entry_str,
                    # data_json=entry,
                    data_URL=entry["link"],
                )
                news_items.append(news_item)
            except ValidationError as e:
                print(
                    f"Validation error for entry from {entry.get('title', 'Unknown Title')}: {e}"
                )
            except Exception as e:
                print(f"Error processing entry from {feed_url}: {e}")

    return news_items


async def main() -> list:
    """
    Main entry point for the asynchronous RSS feed crawler.
    """
    articles = await retrieve_articles_from_rss_feeds()
    return articles


if __name__ == "__main__":
    # Ensure the asynchronous main function is properly awaited
    asyncio.run(main())

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
