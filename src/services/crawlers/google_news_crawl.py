import asyncio
from pygooglenews import GoogleNews
from ...models import NewsItemSchema, ValidationError

from ...utils import get_news_search_dates, decode_gnews_url

CANADIAN_LOCATIONS = [
    # "Canada",
    "Ontario",
    # "Quebec",
    # "Alberta",
    # "British Columbia",
    # "Manitoba",
    # "Saskatchewan",
    # "New Brunswick",
    # "Nova Scotia",
    # "Prince Edward Island",
    # "Newfoundland and Labrador",
    # "Yukon",
    # "Northwest Territories",
    # "Nunavut",
]

# NOTE: Add search queries as you would here: https://news.google.com/home?hl=en-CA&gl=CA&ceid=CA:en
# TODO: financing glossary in Finance Hub Drive, look into those terms and add them here
GOOGLE_NEWS_SEARCH_QUERIES = [
    "middle housing",
    "accessory dwelling units",
    # "multiplex conversions",
    # "corporate programs tied to housing",
    # "government programs tied to housing",
    # "government regulations on housing",
    # "mortgage regulations",
    # "zoning bylaws",
]

# Initialize GoogleNews with Canadian settings
gn = GoogleNews(lang="en", country="CA")


def search_news(base_query, location, from_=None, to_=None):
    """
    Search for news articles using Google News.
    This function is synchronous and can be run in a thread pool.
    """
    if not from_ and not to_:
        today_date, six_months_ago_date = get_news_search_dates()
        from_ = six_months_ago_date
        to_ = today_date

    combined_query = f"{base_query} in {location}"
    result = gn.search(combined_query, from_=from_, to_=to_)
    print(f"Found {len(result['entries'])} articles for query: {combined_query}")
    return result["entries"]


def process_article(entry, query, location, decode_gnews):
    try:
        data_URL = entry.get("link")
        news_item = NewsItemSchema(
            data_source_type="Google News RSS Feed",
            data_URL=data_URL,
            data_json=entry,
            extracted_title=entry.get("title"),
            extracted_news_source=entry.get("source", {}).get("title"),
            extracted_date_published=entry.get("published"),
            extracted_summary=entry.get("summary"),
        )

        if decode_gnews:
            decoded_url = decode_gnews_url(data_URL)
            print(f"Decoded URL: {decoded_url}")
            news_item.extracted_URL = decoded_url

        print(
            f"News item crawled from Google News RSS Feed ({query} in {location}):",
            news_item.extracted_title,
        )
        return news_item
    except ValidationError as e:
        print(
            f"Validation error for entry from {entry.get('title', 'Unknown Title')} ({query} in {location}): {e}"
        )
    except Exception as e:
        print(f"Error processing entry from query '{query} in {location}': {e}")
    return None


async def retrieve_articles_from_google_news(
    decode_gnews: bool = True,
) -> list[NewsItemSchema]:
    """
    Retrieve articles from all Google News queries and locations concurrently.
    """
    tasks = []
    for query in GOOGLE_NEWS_SEARCH_QUERIES:
        for location in CANADIAN_LOCATIONS:
            # Run the synchronous search_news function in a thread pool
            tasks.append(
                asyncio.get_event_loop().run_in_executor(
                    None, search_news, query, location
                )
            )

    results = await asyncio.gather(*tasks)

    processed_articles = []
    for (query, location), articles_from_query in zip(
        [(q, l) for q in GOOGLE_NEWS_SEARCH_QUERIES for l in CANADIAN_LOCATIONS],
        results,
    ):
        for entry in articles_from_query:
            processed_article = process_article(entry, query, location, decode_gnews)
            if processed_article is not None:
                processed_articles.append(processed_article)

    news_items = [item for item in processed_articles if item is not None]
    return news_items


async def main() -> list[NewsItemSchema]:
    articles = await retrieve_articles_from_google_news()
    return articles


if __name__ == "__main__":
    asyncio.run(main())
