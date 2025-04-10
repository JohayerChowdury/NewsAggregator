from pygooglenews import GoogleNews
from ...utils import get_news_search_dates

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
    """
    if not from_ and not to_:
        today_date, six_months_ago_date = get_news_search_dates()
        from_ = six_months_ago_date
        to_ = today_date

    combined_query = f"{base_query} in {location}"
    result = gn.search(combined_query, from_=from_, to_=to_)
    return result["entries"]
