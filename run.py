import feedparser
import ssl

# import json

from flask import Flask, render_template, request

from server.utils import format_published_date, find_rss_links

# from server.utils.news_api import search_news_articles
from server.utils.pygooglenews import search_news, get_news_search_dates

app = Flask(__name__)

# Add the appropriate RSS feeds
RSS_FEEDS = {
    # "Canadian Mortgage Trends": "https://www.canadianmortgagetrends.com/feed/",  # works
    # "Google News: Canadian Accessory Dwelling Unit": "https://news.google.com/rss/search?q=canadian%20accessory%20dwelling%20unit&hl=en-CA&gl=CA&ceid=CA%3Aen",  # works
    # "Government of Ontario: All News": "https://news.ontario.ca/newsroom/en/rss/allnews.rss",  # works
    # "Government of Canada: Finance": "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentfinance&type=newsreleases&sort=publishedDate&orderBy=desc&publishedDate%3E=2020-08-09&pick=100&format=atom&atomtitle=Canada%20News%20Centre%20-%20Department%20of%20Finance%20Canada%20-%20News%20Releases",  # doesnt work,
    # TODO: look into podcasts and how to parse them
    "The Hidden Upside: Real Estate Podcast": "https://feeds.libsyn.com/433605/rss"
}

# TODO: stay away from company websites (have sales objectives that have "vendor" stuff)
WEBSITES = {
    # "Accessorry Dwelling Finance News": "https://accessorydwellings.org/category/news/financing-news/",
    # "Flexobuild News": "https://flexobuild.com/media" # not works
}

GOOGLE_NEWS_SEARCH_QUERIES = [
    # "Canadian accessory dwelling unit",  # NOTE: looks like adding "Canadian" doesn't work well
    # "Canadian mortgage regulations",
    # "Canadian zoning laws in Toronto",
    # "zoning laws",
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
]


def parse_feed(feed_url):
    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context
    parsed_feed = feedparser.parse(feed_url)
    articles = []
    if parsed_feed.bozo:
        print(f"Error parsing feed {feed_url}: {parsed_feed.bozo_exception}")
    else:
        for entry in parsed_feed.entries:
            # TODO: look into only getting articles from the last 6 months
            # _, six_months_ago_date = get_news_search_dates()
            date_published = format_published_date(
                entry.get("published_parsed") or entry.get("published")
            )
            # if date_published < six_months_ago_date:
            #     continue
            articles.append((entry, date_published))
    print(f"Total number of articles from source  {feed_url}: {len(articles)}")
    return articles


def get_articles(queries=[""]):
    articles = []
    seen_titles = set()  # Create a set to store seen titles

    for source, feed in RSS_FEEDS.items():
        try:
            print(f"Fetching {source} feed from {feed}")
            parsed_articles = parse_feed(feed)
            for entry, date_published in parsed_articles:
                articles.append(
                    (
                        (
                            f"Google News: {entry.source.title} "
                            if source.startswith("Google News")
                            else source
                        ),
                        entry,
                        date_published,
                        True,
                        "RSS Feed",
                    )
                )
                seen_titles.add(entry.title.lower())  # Add the title to the set
        except Exception as e:
            print(f"Error fetching articles from {source}: {e}")

    # for source, feed in WEBSITES.items():
    #     try:
    #         print(f"Fetching {source} feed from {feed}")
    #         feed_all = find_rss_links(feed)
    #         for feed in feed_all:
    #             print(f"Fetching articles from {feed}")
    #             parsed_articles = parse_feed(feed)
    #             articles.extend(
    #                 [
    #                     (source, entry, date_published)
    #                     for entry, date_published in parsed_articles
    #                     if entry is not None
    #                 ]
    #             )
    #     except Exception as e:
    #         print(f"Error fetching articles from {source}: {e}")

    try:
        # Fetch news articles for each query
        for query in queries:
            news_articles = search_news(query)
            for article in news_articles:
                if (
                    article.title.lower() not in seen_titles
                ):  # Check if the title is already seen
                    seen_titles.add(article.title.lower())  # Add the title to the set
                    articles.append(
                        (
                            f"Google News: {article.source.title} ",
                            article,
                            format_published_date(
                                article.published_parsed or article.published
                            ),
                            False,
                            query,
                        )
                    )
    except Exception as e:
        print(e)
    return articles or []


@app.route("/")
def index():

    articles = get_articles(GOOGLE_NEWS_SEARCH_QUERIES)

    # sorting TODO: should perhaps filter first and then sort
    sort_date = request.args.get("sort_date")
    if sort_date:
        articles.sort(key=lambda x: x[2], reverse=(sort_date == "desc"))

    sort_title = request.args.get("sort_title")
    if sort_title:
        articles.sort(key=lambda x: x[1].title, reverse=(sort_title == "desc"))

    # filters
    unfiltered_sources = sorted(list(set(article[0] for article in articles)))
    selected_source = request.args.get("source")
    if selected_source:
        articles = [article for article in articles if article[0] == selected_source]

    selected_google_search = request.args.get("google_search")
    if selected_google_search:
        articles = [
            article
            for article in articles
            if article[4] and article[4] == selected_google_search
        ]

    # pagination
    page = request.args.get("page", 1, type=int)
    per_page = 19
    total_articles = len(articles)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_articles = articles[start:end]

    return render_template(
        "index.html",
        articles=paginated_articles,
        sources=unfiltered_sources,
        selected_sources=selected_source,
        selected_google_search=selected_google_search,
        sort_date=sort_date,
        sort_title=sort_title,
        page=page,
        total_pages=total_articles // per_page + 1,
        rss_feeds=RSS_FEEDS,
        google_queries=GOOGLE_NEWS_SEARCH_QUERIES,
    )


@app.route("/search")
def search():
    query = request.args.get("query")

    articles = get_articles(GOOGLE_NEWS_SEARCH_QUERIES)

    results = [
        article
        for article in articles
        if query.lower() in article[1].title.lower()
        or query.lower() in article[1].summary.lower()
    ]

    # sorting TODO: should perhaps filter first and then sort
    sort_date = request.args.get("sort_date")
    if sort_date:
        results.sort(key=lambda x: x[2], reverse=(sort_date == "desc"))

    sort_title = request.args.get("sort_title")
    if sort_title:
        results.sort(key=lambda x: x[1].title, reverse=(sort_title == "desc"))

    # filters
    unfiltered_sources = sorted(list(set(article[0] for article in results)))
    selected_source = request.args.get("source")
    if selected_source:
        results = [article for article in results if article[0] == selected_source]

    selected_google_search = request.args.get("google_search")
    if selected_google_search:
        articles = [
            article
            for article in articles
            if article[4] and article[4] == selected_google_search
        ]

    # pagination
    page = request.args.get("page", 1, type=int)
    per_page = 19
    total_articles = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_articles = results[start:end]

    return render_template(
        "search_results.html",
        articles=paginated_articles,
        query=query,
        sources=unfiltered_sources,
        selected_sources=selected_source,
        selected_google_search=selected_google_search,
        sort_date=sort_date,
        sort_title=sort_title,
        page=page,
        total_pages=total_articles // per_page + 1,
        rss_feeds=RSS_FEEDS,
        google_queries=GOOGLE_NEWS_SEARCH_QUERIES,
    )


if __name__ == "__main__":
    app.run(port=5000, debug=True)
