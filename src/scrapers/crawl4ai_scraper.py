import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig


class Crawl4AIScraper:
    def __init__(self):
        """
        Initialize the scraper with reusable configurations.
        """
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
            page_timeout=20000,  # in ms: 20s
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

    async def _process_multiple_urls(self, urls):
        """
        Process multiple URLs concurrently while reusing the same browser instance.
        """
        results = []
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            for url in urls:
                try:
                    result = await crawler.arun(url=url, config=self.run_config)
                    if result.success:
                        results.append(result.markdown)
                    else:
                        print(f"Error crawling {url}: {result.error_message}")
                        results.append(None)  # Append None for failed URLs
                except Exception as e:
                    print(f"Exception while processing {url}: {e}")
                    results.append(None)  # Append None for exceptions
        return results

    def extract_clean_article(self, url):
        """
        Wrapper to process a single URL synchronously.
        """
        return asyncio.run(self._process_single_url(url))

    def extract_clean_articles(self, urls):
        """
        Wrapper to process multiple URLs synchronously.
        """
        return asyncio.run(self._process_multiple_urls(urls))
