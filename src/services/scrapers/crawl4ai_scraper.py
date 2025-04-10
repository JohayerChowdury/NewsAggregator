import os
from dotenv import load_dotenv
import json
from pydantic import BaseModel

from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    AsyncWebCrawler,
    CrawlResult,
    CacheMode,
    LLMExtractionStrategy,
    LLMConfig,
    PruningContentFilter,
    DefaultMarkdownGenerator,
)

# imports for the patch
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.browser_manager import BrowserManager


load_dotenv()  # Load environment variables from .env file


class ArticleData(BaseModel):
    """
    Data model for the article content.
    """

    title: str
    content: str
    summary: str


class Crawl4AIScraper:
    _patch_applied = False  # class-level flag to ensure we only patch once

    def __init__(self, openai_api_key=None):
        """
        Initialize the scraper with reusable configurations.
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if not Crawl4AIScraper._patch_applied:
            self._apply_patch()
            Crawl4AIScraper._patch_applied = True

        self.filter = PruningContentFilter(
            threshold=0.5, threshold_type="dynamic", min_word_threshold=5
        )
        self.llm_config_provider = (
            "ollama/llama3.2:latest" if not self.openai_api_key else "openai/gpt-4o"
        )
        self.llm_config = LLMConfig(provider=self.llm_config_provider)
        self.extraction_strategy = LLMExtractionStrategy(
            llm_config=self.llm_config,
            schema=ArticleData.model_json_schema(),
            extraction_type="schema",
            instruction="Extract the main content from the page. The content will be used to generate a summary of the page.",
        )
        self.browser_config = BrowserConfig(
            browser_mode="firefox",
            headless=True,
            text_mode=True,
            verbose=False,
            # light_mode=True,
        )
        self.run_config = CrawlerRunConfig(
            word_count_threshold=20,  # content threshold; minimum words per block
            # tag exclusions
            excluded_tags=["nav", "footer", "header", "form", "img", "a"],
            # link filtering
            exclude_social_media_links=True,
            exclude_external_links=True,
            remove_overlay_elements=True,
            cache_mode=CacheMode.BYPASS,
            # user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", # unneeded if magic=True
            # magic=True,
            page_timeout=20000,  # in ms
            # extraction_strategy=self.extraction_strategy,
            markdown_generator=DefaultMarkdownGenerator(content_filter=self.filter),
        )

    # TODO: when fix is released, upgrade crawl4ai (https://github.com/unclecode/crawl4ai/pull/899) and remove this patch
    def _apply_patch(self):
        """
        Apply necessary patches for crawl4ai.
        """

        async def patched_async_playwright__crawler_strategy_close(self):
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

        AsyncPlaywrightCrawlerStrategy.close = (
            patched_async_playwright__crawler_strategy_close
        )

    def _handle_result(self, result: CrawlResult):
        """
        Handle the result of the crawl.
        """
        if not result.success:
            print(f"Crawl error: {result.error_message}")
            return

        # Basic info
        print("Crawled URL:", result.url)
        print("Status code:", result.status_code)

        # HTML
        print("Cleaned HTML size:", len(result.cleaned_html or ""))

        # Markdown output
        if result.markdown:
            print("Raw Markdown length:", len(result.markdown.raw_markdown))
            print("Fit Markdown length:", len(result.markdown.fit_markdown))

        if result.extracted_content:
            data = json.loads(result.extracted_content)
            print("Extracted content:", data)
            # return data

        return result

    async def scrape_url(self, url) -> dict | None:
        """
        Process a single URL asynchronously.
        """
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            try:
                result = self._handle_result(
                    await crawler.arun(url=url, config=self.run_config)
                )
                if result:
                    return {
                        "cleaned_html": result.cleaned_html,
                        "raw_markdown": result.markdown.raw_markdown,
                        "fit_markdown": result.markdown.fit_markdown,
                        "fit_html": result.markdown.fit_html,
                        "extracted_content": result.extracted_content,
                        "metadata": result.metadata,
                    }
                else:
                    print(f"Failed to extract data from {url}")

            except Exception as e:
                print(f"Exception while processing {url}: {e}")

            return None
