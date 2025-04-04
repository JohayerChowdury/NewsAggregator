import asyncio
import json

from pygooglenews import GoogleNews
from googlenewsdecoder import gnewsdecoder

from ..utils import get_news_search_dates
from ..models import NewsItemSchema, ValidationError

# TODO: Yunji provided financing glossary, look into those terms and add them here
GOOGLE_NEWS_SEARCH_QUERIES = [
    # "Canadian accessory dwelling unit",  # NOTE: looks like adding "Canadian" doesn't work well
    "Canadian mortgage regulations",
    # "zoning laws in Toronto, Ontario",
    # "accessory dwelling unit",
    # "mortgage regulations",
    # # TODO: look into how these queries are being used
    # "purchase financing",
    # "renovation financing",
    # "construction financing",
    # "private financing",
    # "mortgage financing",
    # "home equity financing",
    # "refinancing mortgage",
    # "multiplex conversion",
    # "multiplex renovation",
    # "multiplex financing",
    # "multiplex construction",
    # "multiplex purchase",
    # "multiplex refinance",
    "middle housing",
    "corporate programs tied to housing",
]

# Initialize GoogleNews with Canadian settings
gn = GoogleNews(lang="en", country="CA")


def decode_gnews_url(url):
    try:
        decoded = gnewsdecoder(url)
        if decoded.get("status"):
            return decoded["decoded_url"]
    except Exception as e:
        print(f"Error decoding URL {url}: {e}")
    return url


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
                # Validate the news item against the NewsItemBase model
                news_item = NewsItemSchema(
                    data_source_type="Google News RSS Feed",
                    data_json=json.dumps(entry),
                    data_URL=(
                        decode_gnews_url(entry.get("link"))
                        if decode_gnews
                        else entry.get("link")
                    ),
                )
                news_items.append(news_item)
            except ValidationError as e:
                print(
                    f"Validation error for entry from {entry.get('title', 'Unknown Title')}: {e}"
                )
            except Exception as e:
                print(f"Error processing entry from query '{query}': {e}")
    return news_items


async def main() -> list:
    articles = await retrieve_articles_from_google_news()
    return articles


if __name__ == "__main__":
    asyncio.run(main())
