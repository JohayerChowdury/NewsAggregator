import aiohttp
import asyncio
import feedparser
import ssl

from ...models import NewsItemSchema, ValidationError

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
    for source, feed_url in RSS_FEEDS.items():
        tasks.append(extract_articles_from_feed(feed_url))

    results = await asyncio.gather(*tasks)

    news_items = []
    for source, articles_from_feed in zip(RSS_FEEDS.keys(), results):
        for entry in articles_from_feed:
            try:
                # entry_str = json.dumps(entry)

                # Validate the news item against the NewsItemBase model
                news_item = NewsItemSchema(
                    data_source_type="Specific RSS Feed",
                    # data_json=entry_str,
                    data_json=entry,
                    data_URL=entry["link"],
                    extracted_title=entry.get("title"),
                    extracted_news_source=source,
                    extracted_date_published=entry.get("published"),
                    extracted_author=entry.get("author"),
                    extracted_summary=entry.get("summary"),
                )
                news_items.append(news_item)
                # print(
                #     f"News item crawled from {source} RSS Feed: {news_item.extracted_title}"
                # )
            except ValidationError as e:
                print(
                    f"Validation error for entry from {entry.get('title', 'Unknown Title')}: {e}"
                )
            except Exception as e:
                print(f"Error processing entry from {feed_url}: {e}")

    return news_items


async def main() -> list[NewsItemSchema]:
    """
    Main entry point for the asynchronous RSS feed crawler.
    """
    articles = await retrieve_articles_from_rss_feeds()
    return articles


if __name__ == "__main__":
    asyncio.run(main())
