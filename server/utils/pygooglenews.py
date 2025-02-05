from datetime import date, timedelta

from pygooglenews import GoogleNews


def get_news_search_dates():
    today = date.today() + timedelta(
        days=1
    )  # Add 1 day to today's date to include today's articles
    six_months_ago = today - timedelta(days=181)  # Approximately 6 months
    return today, six_months_ago


# Initialize GoogleNews
gn = GoogleNews(lang="en", country="CA")


def search_news(query, from_=None, to_=None):
    if not from_ and not to_:
        today_date, six_months_ago_date = get_news_search_dates()
        from_ = six_months_ago_date
        to_ = today_date
        # print(f"Searching for articles from {from_} to {to_}")
    result = gn.search(query, from_=from_, to_=to_)

    articles = result["entries"]
    return articles


def top_news():
    """
    Get the top news articles.

    :return: A list of top news articles.
    """
    result = gn.top_news()
    articles = result["entries"]
    return articles


def topic_headlines(topic):
    """
    Get news articles by topic.

    :param topic: The topic to search for.
    :return: A list of articles related to the topic.
    """
    result = gn.topic_headlines(topic)
    articles = result["entries"]
    return articles


def geo_headlines(location):
    """
    Get news articles by geolocation.

    :param location: The location to search for.
    :return: A list of articles related to the location.
    """
    result = gn.geo_headlines(location)
    articles = result["entries"]
    return articles
