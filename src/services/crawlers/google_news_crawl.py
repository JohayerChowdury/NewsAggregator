import asyncio
from pygooglenews import GoogleNews
from ...models import NewsItemSchema, ValidationError

from ...utils import get_news_search_dates, decode_gnews_url

# NOTE: Add search queries as you would here: https://news.google.com/home?hl=en-CA&gl=CA&ceid=CA:en
# TODO: financing glossary in Finance Hub Drive, look into those terms and add them here
GOOGLE_NEWS_SEARCH_QUERIES = [
    # "Canadian accessory dwelling unit",  # NOTE: looks like adding "Canadian" doesn't work well
    # "Canadian mortgage regulations",
    "zoning laws in Toronto, Ontario",
    "accessory dwelling unit",
    "mortgage regulations",
    "multiplex conversion",
    "multiplex financing",
    "middle housing",
    "corporate programs tied to housing",
    "government regulations on housing",
]

# Initialize GoogleNews with Canadian settings
gn = GoogleNews(lang="en", country="CA")


def search_news(query, from_=None, to_=None):
    """
    Search for news articles using Google News.
    This function is synchronous and can be run in a thread pool.
    """
    if not from_ and not to_:
        today_date, six_months_ago_date = get_news_search_dates()
        from_ = six_months_ago_date
        to_ = today_date
    result = gn.search(query, from_=from_, to_=to_)
    return result["entries"]


async def retrieve_articles_from_google_news(
    decode_gnews: bool = True,
) -> list[NewsItemSchema]:
    """
    Retrieve articles from all Google News queries concurrently.
    """
    loop = asyncio.get_event_loop()
    tasks = []
    for query in GOOGLE_NEWS_SEARCH_QUERIES:
        # Run the synchronous search_news function in a thread pool
        tasks.append(loop.run_in_executor(None, search_news, query))

    results = await asyncio.gather(*tasks)

    news_items = []
    for query, articles_from_query in zip(GOOGLE_NEWS_SEARCH_QUERIES, results):
        for entry in articles_from_query:
            try:
                # entry_str = json.dumps(entry)

                news_item = NewsItemSchema(
                    data_source_type="Google News RSS Feed",
                    # data_json=entry_str,
                    data_URL=entry.get("link"),
                    data_json=entry,
                    extracted_title=entry.get("title"),
                    extracted_news_source=entry.get("source", {}).get("title"),
                    extracted_date_published=entry.get("published"),
                    extracted_summary=entry.get("summary"),
                )

                if decode_gnews:
                    decoded_url = decode_gnews_url(entry["link"])
                    news_item.extracted_URL = decoded_url

                news_items.append(news_item)
                # print(
                #     "News item crawled from Google News RSS Feed:",
                #     news_item.extracted_title,
                # )
            except ValidationError as e:
                print(
                    f"Validation error for entry from {entry.get('title', 'Unknown Title')}: {e}"
                )
            except Exception as e:
                print(f"Error processing entry from query '{query}': {e}")
    return news_items


async def main() -> list[NewsItemSchema]:
    articles = await retrieve_articles_from_google_news()
    return articles


if __name__ == "__main__":
    asyncio.run(main())
