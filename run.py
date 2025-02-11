import feedparser
import ssl

import json

from flask import Flask, render_template, request

from server.utils import format_published_date, find_rss_links

# from server.utils.news_api import search_news_articles
from server.utils.pygooglenews import search_news, get_news_search_dates

from server.utils.text_processing import clean_text

from server.utils.ml_publication import analyze_themes, label_themes, generate_jot_notes

# from server.utils.ml_publication import (
#     load_documents,
#     split_documents,
#     create_vector_store,
# )

import pandas as pd

import ollama

app = Flask(__name__)

# Add the appropriate RSS feeds
RSS_FEEDS = {
    # "Canadian Mortgage Trends": "https://www.canadianmortgagetrends.com/feed/",  # works
    "Google News: Canadian Accessory Dwelling Unit": "https://news.google.com/rss/search?q=canadian%20accessory%20dwelling%20unit&hl=en-CA&gl=CA&ceid=CA%3Aen",  # works
    # "Government of Canada: Finance": "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentfinance&type=newsreleases&sort=publishedDate&orderBy=desc&publishedDate%3E=2020-08-09&pick=100&format=atom&atomtitle=Canada%20News%20Centre%20-%20Department%20of%20Finance%20Canada%20-%20News%20Releases",  # doesnt work,
    # TODO: look into podcasts and how to parse them
    "Podcast: The Hidden Upside: Real Estate": "https://feeds.libsyn.com/433605/rss",
    # "Podcast: The Real Estate REplay": "https://feeds.buzzsprout.com/1962859.rss",
}

# TODO: stay away from company websites (have sales objectives that have "vendor" stuff)
WEBSITES = {
    # "Accessorry Dwelling Finance News": "https://accessorydwellings.org/category/news/financing-news/",
    # "Flexobuild News": "https://flexobuild.com/media" # not works
}

# TODO: Yunji provided financing glossary, look into those terms and add them here
GOOGLE_NEWS_SEARCH_QUERIES = [
    "Canadian accessory dwelling unit",  # NOTE: looks like adding "Canadian" doesn't work well
    # "Canadian mortgage regulations",
    # "Canadian zoning laws in Toronto",
    "zoning laws",
    # "accessory dwelling unit",
    # "mortgage regulations",
    # # TODO: look into how these queries are being used
    # "purchase financing",
    # "renovation financing",
    "construction financing",
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
            date_published = format_published_date(
                entry.get("published_parsed") or entry.get("published")
            )
            articles.append((entry, date_published))
    return articles


"""
Get articles from last 6 months

Parameters:
- queries: list of strings to query
- json_file: string representing the file path
- using_df: boolean value
"""


# get articles from last 6 months
def get_articles(queries=[""], json_file="", using_df=False):
    articles = []
    seen_titles = set()
    _, six_months_ago_date = get_news_search_dates()

    # Define consistent column order for all entries
    columns = ["source", "entry", "date_published", "is_rss", "query", "summary"]

    # Process RSS feeds
    for source, feed in RSS_FEEDS.items():
        try:
            parsed_articles = parse_feed(feed)
            for entry, date_published in parsed_articles:
                if date_published.date() > six_months_ago_date:
                    articles.append(
                        (
                            (
                                f"Google News: {entry.source.title} "
                                if source.startswith("Google News")
                                else source
                            ),
                            entry,
                            date_published,
                            True,  # is_rss
                            "RSS Feed",
                            clean_text(
                                entry.get(
                                    "summary", entry.get("description", "No Summary")
                                )
                            ),
                        )
                    )
                    seen_titles.add(entry.title.lower())  # Add the title to the set

        except Exception as e:
            print(f"Error fetching articles from {source}: {e}")

    # Process Google News searches
    try:
        for query in queries:
            news_articles = search_news(query)
            for article in news_articles:
                if article.title.lower() not in seen_titles:
                    articles.append(
                        (
                            f"Google News: {article.source.title}",
                            article,
                            format_published_date(
                                article.published_parsed or article.published
                            ),
                            False,  # is_rss
                            query,
                            clean_text(
                                getattr(
                                    article,
                                    "summary",
                                    getattr(article, "description", "No Summary"),
                                )
                            ),
                        )
                    )
                    seen_titles.add(article.title.lower())
    except Exception as e:
        print(f"Error processing Google News: {e}")

    if using_df:
        if len(articles[0]) != len(columns):
            raise ValueError(
                f"Article tuple length {len(articles[0])} doesn't match columns {len(columns)}"
            )
        df = pd.DataFrame(articles, columns=columns)
        with open("articles.csv", "w") as f:
            df.to_csv(f, index=False)
        return df

    if json_file:
        with open(json_file, "w") as f:
            json.dump(articles, f, indent=4)
        print(f"Saved articles to {json_file}")
    return articles


@app.route("/")
def index():

    articles = get_articles(GOOGLE_NEWS_SEARCH_QUERIES)

    # llm_news_feed = get_news_feed(articles)

    # sorting TODO: should perhaps filter first and then sort
    sort_date = request.args.get("sort_date")
    if sort_date:
        articles.sort(key=lambda x: x[2], reverse=(sort_date == "desc"))

    sort_title = request.args.get("sort_title")
    if sort_title:
        articles.sort(key=lambda x: x[1].title, reverse=(sort_title == "desc"))

    # filters
    unfiltered_sources = sorted(list(set(article[0] for article in articles)))
    selected_sources = request.args.getlist("source")
    if selected_sources:
        articles = [article for article in articles if article[0] in selected_sources]

    selected_google_searches = request.args.getlist("google_search")
    if selected_google_searches:
        articles = [
            article
            for article in articles
            if article[4] and article[4] in selected_google_searches
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
        selected_sources=selected_sources,
        selected_google_search=selected_google_searches,
        sort_date=sort_date,
        sort_title=sort_title,
        page=page,
        total_pages=total_articles // per_page + 1,
        rss_feeds=RSS_FEEDS,
        google_queries=GOOGLE_NEWS_SEARCH_QUERIES,
    )


@app.route("/search")
def search():
    query = request.args.get("query") or ""

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
    selected_sources = request.args.getlist("source")
    if selected_sources:
        results = [article for article in results if article[0] in selected_sources]

    selected_google_searches = request.args.getlist("google_search")
    if selected_google_searches:
        articles = [
            article
            for article in articles
            if article[4] and article[4] in selected_google_searches
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
        selected_sources=selected_sources,
        selected_google_search=selected_google_searches,
        sort_date=sort_date,
        sort_title=sort_title,
        page=page,
        total_pages=total_articles // per_page + 1,
        rss_feeds=RSS_FEEDS,
        google_queries=GOOGLE_NEWS_SEARCH_QUERIES,
    )


# Main execution function
def analyze_news(num_themes=10):
    try:
        articles_df = get_articles(GOOGLE_NEWS_SEARCH_QUERIES, using_df=True)

        # Check for required columns
        required_columns = ["summary", "date_published", "entry"]
        missing = [col for col in required_columns if col not in articles_df.columns]
        if missing:
            raise KeyError(f"Missing required columns: {missing}")

        articles_df, _, _ = analyze_themes(articles_df, num_themes)
        articles_df = label_themes(articles_df)
    except Exception as e:
        print(f"Error analyzing news: {e}")
        return "Error analyzing news response"
    return generate_jot_notes(articles_df)


@app.route("/publication")
def publication():

    results = analyze_news()
    # results_to_json_file = "results.json"

    # with open(results_to_json_file, "w") as f:
    #     json.dump(results, f, indent=4)
    if results:
        return results, 200, {"Content-Type": "text/plain"}

    return "No results found", 404, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(port=5000, debug=True)
