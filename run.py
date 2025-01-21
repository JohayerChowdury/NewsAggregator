import feedparser
import ssl

# import json

from flask import Flask, render_template, request

from server.utils import format_published_date, find_rss_links

# from server.utils.news_api import search_news_articles
from server.utils.pygooglenews import search_news, top_news

app = Flask(__name__)

# Add the appropriate RSS feeds
RSS_FEEDS = {
    # "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",  # works
    # 'Wall Street Journal': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', # works
    # "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",  # works
    # "Canadian Mortgage Trends": "https://www.canadianmortgagetrends.com/feed/",  # works
    # "Google News: Canadian Accessory Dwelling Unit": "https://news.google.com/rss/search?q=canadian%20accessory%20dwelling%20unit&hl=en-CA&gl=CA&ceid=CA%3Aen",  # works
    # "Government of Ontario: All News": "https://news.ontario.ca/newsroom/en/rss/allnews.rss",  # works
    # "Government of Canada: Finance": "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentfinance&type=newsreleases&sort=publishedDate&orderBy=desc&publishedDate%3E=2020-08-09&pick=100&format=atom&atomtitle=Canada%20News%20Centre%20-%20Department%20of%20Finance%20Canada%20-%20News%20Releases" # doesnt work,
    # "CBC News": "https://rss.cbc.ca/lineup/topstories.xml" # unsure
}

WEBSITES = {
    # "Accessorry Dwelling Finance News": "https://accessorydwellings.org/category/news/financing-news/",
    # "Flexobuild News": "https://flexobuild.com/media" # not works
}


def parse_feed(feed_url):
    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context
    parsed_feed = feedparser.parse(feed_url)
    articles = []
    if parsed_feed.bozo:
        print(f"Error parsing feed {feed_url}: {parsed_feed.bozo_exception}")
    else:
        for entry in parsed_feed.entries:
            date_published = format_published_date(
                entry.get("published_parsed") or entry.get("published")
            )
            articles.append((entry, date_published))
    print(f"Total number of articles from source  {feed_url}: {len(articles)}")
    return articles


@app.route("/")
def index():
    articles = []

    for source, feed in RSS_FEEDS.items():
        try:
            print(f"Fetching {source} feed from {feed}")
            parsed_articles = parse_feed(feed)
            articles.extend(
                [
                    (source, entry, date_published)
                    for entry, date_published in parsed_articles
                    if entry is not None
                ]
            )
        except Exception as e:
            print(f"Error fetching articles from {source}: {e}")

    for source, feed in WEBSITES.items():
        try:
            print(f"Fetching {source} feed from {feed}")
            feed_all = find_rss_links(feed)
            for feed in feed_all:
                print(f"Fetching articles from {feed}")
                parsed_articles = parse_feed(feed)
                articles.extend(
                    [
                        (source, entry, date_published)
                        for entry, date_published in parsed_articles
                        if entry is not None
                    ]
                )
        except Exception as e:
            print(f"Error fetching articles from {source}: {e}")

    try:
        news_articles = search_news("canadian accessory dwelling unit")
        for article in news_articles:
            articles.append(
                (
                    f"Google News: {article.source.title} ",
                    article,
                    format_published_date(
                        article.published_parsed or article.published
                    ),
                )
            )
    except Exception as e:
        print(e)

    # TODO: date sorting is wrong, need to fix
    articles = sorted(articles, key=lambda x: x[2], reverse=True) or []

    page = request.args.get("page", 1, type=int)
    per_page = 10
    total_articles = len(articles)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_articles = articles[start:end]
    return render_template(
        "index.html",
        articles=paginated_articles,
        page=page,
        total_pages=total_articles // per_page + 1,
    )


@app.route("/search")
def search():
    query = request.args.get("query")

    articles = []
    for source, feed in RSS_FEEDS.items():
        parsed_articles = parse_feed(feed)
        articles.extend(
            [
                (source, entry, date_published)
                for entry, date_published in parsed_articles
                if entry is not None
            ]
        )

        results = [
            article
            for article in articles
            if query.lower() in article[1].title.lower()
            or query.lower() in article[1].summary.lower()
        ]

    # Fetch news articles using NewsApiClient
    try:
        news_articles = search_news_articles([query])
        for article in news_articles:
            articles.append(("NewsAPI", article, article["publishedAt"]))
    except Exception as e:
        print(e)

    return render_template("search_results.html", articles=results, query=query)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
