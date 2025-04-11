import asyncio
import csv
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
                ) or data_json.get("source").get("title")
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
                        source=source,
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

    async def _update_article_with_scraped_data(
        self, article: NewsItemSchema
    ) -> int | None:
        """
        Private method to scrape an article and update it in the database.
        """
        try:
            result = await self.crawl4ai_scraper.scrape_url(article.get_online_url())
            if result:
                article.crawl4ai_result = result
                update_response = self.database_service.update_news_item(
                    article.id, article
                )
                if update_response.is_success():
                    print(f"Database Update Success: ID {update_response.data.id}")
                    return int(update_response.data.id)
                else:
                    print(f"Database Update Failed: {update_response.message}")
        except Exception as e:
            print(f"Error updating article: {e}")
        return None

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
                updated_id = await self._update_article_with_scraped_data(article)
                if updated_id:
                    news_items_ids.append(updated_id)
            except Exception as e:
                print(f"Error scraping article: {e}")

        return news_items_ids

    async def update_articles_with_null_extracted_url(self) -> list[int]:
        """
        Filter articles with null 'extracted_URL', scrape them, and update the database.
        """
        db_query = self.database_service.query_select_news_items_from_db(
            filters={"extracted_URL": "null"}
        )
        db_query_response = db_query.execute()

        articles_with_null_extracted_url = (
            [NewsItemSchema(**item) for item in db_query_response.data]
            if db_query_response.data
            else []
        )

        updated_article_ids = []
        for article in articles_with_null_extracted_url:
            try:
                # Decode the URL to get the extracted URL
                decoded_url = decode_gnews_url(article.data_URL)
                if str(decoded_url) != str(article.data_URL):
                    article.extracted_URL = decoded_url

                # Update the article in the database
                update_response = self.database_service.update_news_item(
                    article.id, article
                )
                if update_response.is_success():
                    print(f"Database Update Success: ID {update_response.data.id}")
                    updated_article_ids.append(int(update_response.data.id))
                else:
                    print(f"Database Update Failed: {update_response.message}")
            except Exception as e:
                print(f"Error updating article: {e}")
            updated_id = await self._update_article_with_scraped_data(article)
            if updated_id:
                updated_article_ids.append(updated_id)

        return updated_article_ids

    async def _generate_summary(self, article: NewsItemSchema) -> int | None:
        """
        Generate a summary for the given article and update it in the database.
        """
        try:
            article_text = article.get_article_text()
            article.generated_summary = await self.openai_service.generate_summary(
                article_text
            )

            update_response = self.database_service.update_news_item(
                article.id, article
            )
            if update_response.is_success():
                print(
                    f"Database Update Success (Summary): ID {update_response.data.id}"
                )
                return int(update_response.data.id)
            else:
                print(f"Database Update Failed (Summary): {update_response.message}")
        except Exception as e:
            print(f"Error generating summary: {e}")
        return None

    async def _generate_category(self, article: NewsItemSchema) -> int | None:
        """
        Generate a category for the given article and update it in the database.
        """
        try:
            article_text = article.get_article_text()
            article.generated_category = await self.openai_service.assign_category(
                article_text
            )

            update_response = self.database_service.update_news_item(
                article.id, article
            )
            if update_response.is_success():
                print(
                    f"Database Update Success (Category): ID {update_response.data.id}"
                )
                return int(update_response.data.id)
            else:
                print(f"Database Update Failed (Category): {update_response.message}")
        except Exception as e:
            print(f"Error generating category: {e}")
        return None

    async def summarize_articles(self) -> list[int]:
        """
        Generate summaries for articles with null 'generated_summary' and not null 'crawl4ai_result'.
        """
        db_query = self.database_service.query_select_news_items_from_db(
            not_null_fields=["crawl4ai_result"],
            filters={"generated_summary": "null"},
        )
        db_query_response = db_query.execute()

        articles_requiring_summary = (
            [NewsItemSchema(**item) for item in db_query_response.data]
            if db_query_response.data
            else []
        )

        tasks = [
            self._generate_summary(article) for article in articles_requiring_summary
        ]
        summarized_ids = await asyncio.gather(*tasks)
        return [article_id for article_id in summarized_ids if article_id]

    async def categorize_articles(self) -> list[int]:
        """
        Generate categories for articles with null 'generated_category' and not null 'crawl4ai_result'.
        """
        db_query = self.database_service.query_select_news_items_from_db(
            not_null_fields=["crawl4ai_result"],
            filters={"generated_category": "null"},
        )
        db_query_response = db_query.execute()

        articles_requiring_category = (
            [NewsItemSchema(**item) for item in db_query_response.data]
            if db_query_response.data
            else []
        )

        tasks = [
            self._generate_category(article) for article in articles_requiring_category
        ]
        categorized_ids = await asyncio.gather(*tasks)
        return [article_id for article_id in categorized_ids if article_id]

    def download_selected_articles_as_csv(self, output_file_path: str):
        """
        Download articles marked as 'is_selected_for_download' into a CSV file.
        """
        db_query = self.database_service.query_select_news_items_from_db(
            filters={"is_selected_for_download": True}
        )
        db_query_response = db_query.execute()

        if not db_query_response.data:
            print("No articles found for download.")
            return

        articles = [NewsItemSchema(**item) for item in db_query_response.data]

        try:
            with open(
                output_file_path, mode="w", newline="", encoding="utf-8"
            ) as csv_file:
                writer = csv.writer(csv_file)
                # Write header
                writer.writerow(
                    [
                        "ID",
                        "Title",
                        "URL",
                        "Published Date",
                        "News Source",
                        "Summary",
                        "Category",
                    ]
                )
                # Write article data
                for article in articles:
                    writer.writerow(
                        [
                            article.id,
                            article.get_title(),
                            article.get_online_url(),
                            article.get_date_published(),
                            article.get_news_source(),
                            article.get_article_summary(),
                            article.get_category(),
                        ]
                    )
            print(f"Articles successfully downloaded to {output_file_path}")
        except Exception as e:
            print(f"Error writing to CSV: {e}")
