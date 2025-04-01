import asyncio
import json

import feedparser
import ssl

# Add the appropriate RSS feeds
RSS_FEEDS = {
    "Canadian Mortgage Trends": "https://www.canadianmortgagetrends.com/feed/",  # works
    # "Government of Canada: Finance": "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentfinance&type=newsreleases&sort=publishedDate&orderBy=desc&publishedDate%3E=2020-08-09&pick=100&format=atom&atomtitle=Canada%20News%20Centre%20-%20Department%20of%20Finance%20Canada%20-%20News%20Releases",  # doesnt work,
    # TODO: look into podcasts and how to parse them
    # "Podcast: The Hidden Upside: Real Estate": "https://feeds.libsyn.com/433605/rss",
    # "Podcast: The Real Estate REplay": "https://feeds.buzzsprout.com/1962859.rss",  # doesnt work (for now)
}


def extract_articles_from_feed(feed_url) -> list:
    """
    Extract articles from a given RSS feed URL.

    :param feed_url: The URL of the RSS feed.
    """
    articles = []
    try:
        if hasattr(ssl, "_create_unverified_context"):
            ssl._create_default_https_context = ssl._create_unverified_context
    except:
        pass

    try:
        parsed_feed = feedparser.parse(feed_url)
        for entry in parsed_feed.entries:
            articles.append(entry)
    except Exception as e:
        print(f"Error parsing feed {feed_url}: {e}")

    return articles


def retrieve_articles_from_rss_feeds() -> list:
    entries = []
    for source, feed_url in RSS_FEEDS.items():
        articles_from_feed = extract_articles_from_feed(feed_url)
        for entry in articles_from_feed:
            entries.append(
                {
                    "data_source": f"RSS Feed: {source}",
                    "data_entry": entry,
                    "article_link": entry["link"],
                }
            )

    return entries


def main() -> list:
    articles = retrieve_articles_from_rss_feeds()
    return articles


# asyncio.run(main())

if __name__ == "__main__":
    main()

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
