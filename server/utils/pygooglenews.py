from pygooglenews import GoogleNews

# Initialize GoogleNews
gn = GoogleNews(lang="en", country="CA")


def search_news(query, when=None):
    """
    Search for news articles using pygooglenews.

    :param query: The search query.
    :param when: The time range for the search (e.g., '1d', '7d', '1m').
    :return: A list of articles.
    """
    if when:
        result = gn.search(query, when=when)
    else:
        result = gn.search(query)

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
