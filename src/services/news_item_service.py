import asyncio
from ..models import NewsItemSchema, ValidationError
from ..utils import decode_gnews_url

from .crawlers.rss_feed_crawl import RSS_FEEDS, extract_articles_from_feed
from .crawlers.google_news_crawl import (
    CANADIAN_LOCATIONS,
    GOOGLE_NEWS_SEARCH_QUERIES,
    search_news,
)
from .database_service import SupabaseDBService
from .scrapers.crawl4ai_scraper import Crawl4AIScraper
from .openai_service import OpenAIService


class NewsItemService:
    def __init__(
        self,
        database_service: SupabaseDBService,
        crawl4ai_scraper: Crawl4AIScraper,
        openai_service: OpenAIService,
    ):
        self.database_service = database_service
        self.crawl4ai_scraper = crawl4ai_scraper
        self.openai_service = openai_service

    def _process_article(
        self,
        data_source_type,
        data_json: dict,
        data_URL,
        **additional_params,
    ) -> int | None:
        """
        Process a single article and return the ID of the created NewsItemSchema.
        This function creates a NewsItemSchema object, checks if it already exists in the database,
        and if not, inserts it into the database. It also handles the extraction of relevant fields
        from the article data.
        If the article already exists in the database, it returns None.
        """
        try:
            crawled_news_item = NewsItemSchema(
                data_source_type=data_source_type,
                data_json=data_json,
                data_URL=data_URL,
            )
            fetched_news_item_response = (
                self.database_service.fetch_news_items_by_data_URL(
                    crawled_news_item.data_URL
                )
            )
            if not fetched_news_item_response.data:
                extracted_URL = decode_gnews_url(crawled_news_item.data_URL)
                if str(extracted_URL) != str(crawled_news_item.data_URL):
                    crawled_news_item.extracted_URL = extracted_URL

                crawled_news_item.extracted_date_published = data_json.get("published")
                crawled_news_item.extracted_title = data_json.get("title")
                crawled_news_item.extracted_news_source = additional_params.get(
                    "source"
                ) or data_json.get("source", {}).get("title")
                crawled_news_item.extracted_author = data_json.get("author") or None
                crawled_news_item.extracted_summary = data_json.get("summary")
                insert_response = self.database_service.insert_news_item(
                    crawled_news_item
                )
                if insert_response.is_success():
                    print(
                        f"Database Insert Success: Created with ID {insert_response.data.id}"
                    )
                    return int(insert_response.data.id)
                else:
                    print(f"Database Insert Failed: {insert_response.message}")
        except Exception as e:
            print(f"Error processing article: {e}")
        return None

    async def _crawl_rss_feeds(self) -> list[int]:
        """
        Crawl articles from RSS feeds and return ID of NewsItemSchema.
        """
        tasks = [
            extract_articles_from_feed(feed_url) for feed_url in RSS_FEEDS.values()
        ]
        results = await asyncio.gather(*tasks)

        news_items_ids = []
        for source, articles in zip(RSS_FEEDS.keys(), results):
            for entry in articles:
                try:
                    data_URL = entry.get("link")
                    news_item_id = self._process_article(
                        data_source_type="Specific RSS Feed",
                        data_json=entry,
                        data_URL=data_URL,
                        additional_params={"source": source},
                    )
                    if news_item_id:
                        news_items_ids.append(news_item_id)
                except Exception as e:
                    print(f"Error for RSS feed entry: {e}")
        return news_items_ids

    async def _crawl_google_news(self) -> list[int]:
        """
        Crawl articles from Google News, create NewsItemSchema objects and return list of IDs.
        """
        tasks = [
            asyncio.get_event_loop().run_in_executor(None, search_news, query, location)
            for query in GOOGLE_NEWS_SEARCH_QUERIES
            for location in CANADIAN_LOCATIONS
        ]
        results = await asyncio.gather(*tasks)

        news_items_ids = []
        for (query, location), articles in zip(
            [(q, l) for q in GOOGLE_NEWS_SEARCH_QUERIES for l in CANADIAN_LOCATIONS],
            results,
        ):
            for entry in articles:
                try:
                    data_URL = entry.get("link")
                    news_item_id = self._process_article(
                        data_source_type="Google News RSS Feed",
                        data_json=entry,
                        data_URL=data_URL,
                    )
                    if news_item_id:
                        news_items_ids.append(news_item_id)
                except Exception as e:
                    print(f"Error for Google News entry: {e}")
        return news_items_ids

    async def crawl_all_sources(self) -> list[int]:
        """
        Crawl all sources (RSS feeds and Google News) and return list of IDs.
        """
        rss_feed_ids = await self._crawl_rss_feeds()
        google_news_ids = await self._crawl_google_news()

        all_ids = rss_feed_ids + google_news_ids
        print(
            f"Crawled and added {len(all_ids)} articles from all sources into the database."
        )
        return all_ids

    async def scrape_articles(self) -> list[int]:
        """
        Using the crawl4ai scraper, scrape articles that require scraping, and update the database.
        """
        db_query = self.database_service.query_select_news_items_from_db(
            filters={
                "crawl4ai_result": "null",
            }
        )
        db_query_response = db_query.execute()

        articles_requiring_scraping = (
            [NewsItemSchema(**item) for item in db_query_response.data]
            if db_query_response.data
            else []
        )

        news_items_ids = []
        for article in articles_requiring_scraping:
            try:
                result = await self.crawl4ai_scraper.scrape_url(
                    article.get_online_url()
                )
                if result:
                    article.crawl4ai_result = result
                    update_response = self.database_service.update_news_item(
                        article.id, article
                    )
                    if update_response.is_success():
                        print(f"Database Update Success: ID {update_response.data.id}")
                        news_items_ids.append(int(update_response.data.id))
                else:
                    print(f"Database Update Failed: {update_response.message}")
            except Exception as e:
                print(f"Error scraping article: {e}")

        return news_items_ids

    async def summarize_and_categorize_articles(self):
        """
        Generate summaries and categories, and update the database.
        """
        db_query = self.database_service.query_select_news_items_from_db(
            not_null_fields=["crawl4ai_result"],
            filters={
                "generated_summary": "null",
                "generated_category": "null",
            },
        )
        db_query_response = db_query.execute()

        articles_requiring_processing = []
        if db_query_response.data:
            articles_requiring_processing = [
                NewsItemSchema(**item).get_json() for item in db_query_response.data
            ]

        for id in articles_requiring_processing:
            try:
                article = self.database_service.fetch_news_items_by_id(id)

                # Generate categories and summaries
                article.generated_category = self.openai_service.assign_category(
                    article.article_text
                )
                article.generated_summary = self.openai_service.generate_summary(
                    article.article_text
                )

                self.database_service.update_news_item(id, article)
            except Exception as e:
                print(f"Error processing article {id.data_URL}: {e}")
