import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    PruningContentFilter,
    DefaultMarkdownGenerator,
    LLMExtractionStrategy,
    LLMConfig,
)
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.browser_manager import BrowserManager
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

from ..models import NewsItemSchema
from ..services.database_service import SupabaseDBService


async def patched_async_playwright__crawler_strategy_close(self) -> None:
    """
    Close the browser and clean up resources.

    This patch addresses an issue with Playwright instance cleanup where the static instance
    wasn't being properly reset, leading to issues with multiple crawls.

    Issue: https://github.com/unclecode/crawl4ai/issues/842

    Returns:
        None
    """
    await self.browser_manager.close()

    # Reset the static Playwright instance
    BrowserManager._playwright_instance = None


AsyncPlaywrightCrawlerStrategy.close = patched_async_playwright__crawler_strategy_close


class Crawl4AIScraper:
    def __init__(self):
        """
        Initialize the scraper with reusable configurations.
        """
        self.filter = PruningContentFilter(
            threshold=0.5, threshold_type="fixed", min_word_threshold=10
        )
        # self.llm_config = LLMConfig(provider="ollama/llama3.2:latest", api_token=None)
        # self.extraction_strategy = LLMExtractionStrategy(
        #     llm_config=self.llm_config,
        # )
        self.browser_config = BrowserConfig(
            browser_mode="firefox",
            headless=True,
            text_mode=True,
            verbose=False,
        )
        self.run_config = CrawlerRunConfig(
            only_text=True,
            excluded_tags=["nav", "footer", "header", "form", "img", "a"],
            exclude_social_media_links=True,
            exclude_external_links=True,
            remove_overlay_elements=True,
            cache_mode=CacheMode.BYPASS,
            # user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", # unneeded if magic=True
            # magic=True,
            page_timeout=60000,  # in ms
            markdown_generator=DefaultMarkdownGenerator(content_filter=self.filter),
        )

    async def _process_single_url(self, url):
        """
        Process a single URL asynchronously.
        """
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            try:
                result = await crawler.arun(url=url, config=self.run_config)
                if result.success:
                    return result.markdown
                else:
                    print(f"Error crawling {url}: {result.error_message}")
                    return None
            except Exception as e:
                print(f"Exception while processing {url}: {e}")
                return None

    # async def _process_multiple_urls(self, urls):
    #     """
    #     Process multiple URLs concurrently while reusing the same browser instance.
    #     """
    #     results = []
    #     async with AsyncWebCrawler(config=self.browser_config) as crawler:
    #         for url in urls:
    #             try:
    #                 result = await crawler.arun(url=url, config=self.run_config)
    #                 if result.success:
    #                     results.append(result.markdown)
    #                 else:
    #                     error = f"Error crawling {url}: {result.error_message}"
    #                     print(error)
    #                     results.append(error)
    #             except Exception as e:
    #                 error = f"Exception while processing {url}: {e}"
    #                 print(error)
    #                 results.append(error)  # Append None for exceptions
    #     return results

    async def concurrently_scrape_and_update(
        self, news_items: list[NewsItemSchema], database_service: SupabaseDBService
    ):
        """
        Process multiple URLs concurrently and update the database for successful scrapes.
        """

        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            tasks = []
            for item in news_items:
                url = item.data_URL
                tasks.append(self._process_single_url(url))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for item, result in zip(news_items, results):
                if isinstance(result, str):  # Successful scrape
                    try:
                        # Update the database with the extracted text
                        database_service.update_extracted_text(item.id, result)
                    except Exception as e:
                        print(f"Error updating database for {item.data_URL}: {e}")
                elif isinstance(result, Exception):
                    print(f"Error processing {item.data_URL}: {result}")

    # def extract_clean_article(self, url):
    #     """
    #     Wrapper to process a single URL synchronously.
    #     """
    #     return asyncio.run(self._process_single_url(url))

    # def extract_clean_articles(self, urls):
    #     """
    #     Wrapper to process multiple URLs synchronously.
    #     """
    #     return asyncio.run(self._process_multiple_urls(urls))
