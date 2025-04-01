import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    RateLimiter,
    CrawlerMonitor,
    DisplayMode,
    CacheMode,
)

# from crawl4ai.content_filter_strategy import BM25ContentFilter
# from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
# from crawl4ai.models import CrawlResult
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_dispatcher import SemaphoreDispatcher

# from ..utils.text_processing import filter_text_content


# dispatcher = SemaphoreDispatcher(
#     max_session_permit=20,
#     rate_limiter=RateLimiter(
#         base_delay=(2.0, 4.0),
#         max_delay=10.0,  # Maximum delay in seconds
#     ),
#     monitor=CrawlerMonitor(max_visible_rows=15, display_mode=DisplayMode.DETAILED),
# )


async def crawl_batch():
    pass
    browser_config = BrowserConfig(headless=True, verbose=False)
    # run_config = CrawlerRunConfig(
    #     cache_mode=CacheMode.BYPASS,
    #     stream=False
    #     exclude_external_links=True,
    #     remove_overlay_elements=True,
    #     # process_iframes=True,
    # )


async def extract_clean_article_crawl4ai(
    article_link,
    excluded_keywords=["advertisement", "subscribe", "click here"],
):
    """
    Extract and clean article content using crawl4ai.
    """
    browser_config = BrowserConfig(headless=True, text_mode=True, verbose=False)
    run_config = CrawlerRunConfig(
        only_text=True,
        excluded_tags=["nav", "footer", "header", "form", "img", "a"],
        exclude_social_media_links=True,
        exclude_external_links=True,
        remove_overlay_elements=True,
        cache_mode=CacheMode.BYPASS,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        page_timeout=20000,  # in ms: 20s
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            result = await crawler.arun(url=article_link, config=run_config)
            raw_content = result.markdown
            return raw_content

            # # Filter out unwanted keywords
            # filtered_content = "\n".join(
            #     [
            #         line
            #         for line in raw_content.splitlines()
            #         if not any(keyword in line.lower() for keyword in excluded_keywords)
            #     ]
            # )

            # # Clean and normalize the content
            # return filter_text_content(filtered_content)
        except Exception as e:
            print(f"Error extracting content from {article_link}: {e}")
            return ""


def extract_clean_article(article_link):
    """
    Wrapper function to run the async extraction synchronously.
    """
    return asyncio.run(extract_clean_article_crawl4ai(article_link))


# def check_robots_txt(urls: list[str]) -> list[str]:
#     """Checks robots.txt files to determine which URLs are allowed to be crawled.

#     Args:
#         urls (list[str]): List of URLs to check against their robots.txt files.

#     Returns:
#         list[str]: List of URLs that are allowed to be crawled according to robots.txt rules.
#             If a robots.txt file is missing or there's an error, the URL is assumed to be allowed.
#     """
#     allowed_urls = []

#     for url in urls:
#         try:
#             robots_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}/robots.txt"
#             rp = RobotFileParser(robots_url)
#             rp.read()

#             if rp.can_fetch("*", url):
#                 allowed_urls.append(url)

#         except Exception:
#             # If robots.txt is missing or there's any error, assume URL is allowed
#             allowed_urls.append(url)

#     return allowed_urls
