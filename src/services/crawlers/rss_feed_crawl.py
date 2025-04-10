import aiohttp
import feedparser
import ssl

# NOTE: Add RSS feeds and their sources here for crawling {source: feed_url}
RSS_FEEDS = {
    "Canadian Mortgage Trends": "https://www.canadianmortgagetrends.com/feed/",  # works
    # "Government of Canada: Finance": "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentfinance&type=newsreleases&sort=publishedDate&orderBy=desc&publishedDate%3E=2020-08-09&pick=100&format=atom&atomtitle=Canada%20News%20Centre%20-%20Department%20of%20Finance%20Canada%20-%20News%20Releases",  # doesnt work,
    # TODO: look into podcasts and how to parse them
    # "Podcast: The Hidden Upside: Real Estate": "https://feeds.libsyn.com/433605/rss",
    # "Podcast: The Real Estate REplay": "https://feeds.buzzsprout.com/1962859.rss",  # doesnt work (for now)
}

# Create an SSL context to ignore verification
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


async def fetch_feed(session, feed_url):
    """
    Fetch the RSS feed content asynchronously with optional SSL bypass.
    """
    try:
        async with session.get(feed_url, ssl=ssl_context) as response:
            content = await response.text()
            return feedparser.parse(content)
    except Exception as e:
        print(f"Error fetching feed {feed_url}: {e}")
        return None


async def extract_articles_from_feed(feed_url):
    """
    Extract raw articles from a given RSS feed URL asynchronously.
    """
    try:
        async with aiohttp.ClientSession() as session:
            parsed_feed = await fetch_feed(session, feed_url)
            return parsed_feed.entries if parsed_feed and parsed_feed.entries else []
    except Exception as e:
        print(f"Error parsing feed {feed_url}: {e}")
        return []
