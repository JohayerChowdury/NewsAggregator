import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

# TODO: stay away from company websites (have sales objectives that have "vendor" stuff)
# WEBSITES = {
# "Accessorry Dwelling Finance News": "https://accessorydwellings.org/category/news/financing-news/",
# "Flexobuild News": "https://flexobuild.com/media" # not works
# }


async def main():
    browser_config = BrowserConfig(verbose=True)  # verbose for logging

    run_config = CrawlerRunConfig(
        word_count_threshold=10,  # Minimum words per content block
        exclude_external_links=True,  # Remove external links
        remove_overlay_elements=True,  # Remove popups/modals
        process_iframes=True,  # Process iframe content
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com", config=run_config)
        print(result.markdown)  # Print clean markdown content


asyncio.run(main())
