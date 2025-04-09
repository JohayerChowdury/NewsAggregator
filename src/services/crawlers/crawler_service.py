from ..crawlers import rss_feed_crawl, google_news_crawl
from ...models import NewsItemSchema


class CrawlerService:
    @staticmethod
    async def crawl_all_sources() -> list[NewsItemSchema]:
        """
        Crawl articles from all sources (RSS feeds and Google News).
        """
        news_items = []

        # Crawl RSS feeds
        try:
            print("Crawling RSS feeds...")
            crawled_articles_from_rss = await rss_feed_crawl.main()
            news_items.extend(crawled_articles_from_rss)
        except Exception as e:
            print(f"Error crawling RSS feeds: {e}")

        # Crawl Google News
        try:
            print("Crawling Google News...")
            crawled_articles_from_google = await google_news_crawl.main()
            news_items.extend(crawled_articles_from_google)
        except Exception as e:
            print(f"Error crawling Google News: {e}")

        return news_items
