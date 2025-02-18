import os
import swifter
from flask import Flask, render_template, request

# from flask_cors import CORS

from server.utils import pd
from server.utils.scraper import (
    load_articles,
    get_articles,
    get_article_content,
    RSS_FEEDS,
)
from server.utils.text_processing import normalize_html_content
from server.utils.ml_publication import analyze_themes, label_themes, generate_jot_notes


app = Flask(__name__)
# CORS(app)

# Add the appropriate RSS feeds
RSS_FEEDS = {
    # "Canadian Mortgage Trends": "https://www.canadianmortgagetrends.com/feed/",  # works
    # "Google News: Canadian Accessory Dwelling Unit": "https://news.google.com/rss/search?q=canadian%20accessory%20dwelling%20unit&hl=en-CA&gl=CA&ceid=CA%3Aen",  # works
    # "Government of Canada: Finance": "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentfinance&type=newsreleases&sort=publishedDate&orderBy=desc&publishedDate%3E=2020-08-09&pick=100&format=atom&atomtitle=Canada%20News%20Centre%20-%20Department%20of%20Finance%20Canada%20-%20News%20Releases",  # doesnt work,
    # TODO: look into podcasts and how to parse them
    "Podcast: The Hidden Upside: Real Estate": "https://feeds.libsyn.com/433605/rss",
    # "Podcast: The Real Estate REplay": "https://feeds.buzzsprout.com/1962859.rss", # doesnt work (for now)
}

# TODO: stay away from company websites (have sales objectives that have "vendor" stuff)
WEBSITES = {
    # "Accessorry Dwelling Finance News": "https://accessorydwellings.org/category/news/financing-news/",
    # "Flexobuild News": "https://flexobuild.com/media" # not works
}

# TODO: Yunji provided financing glossary, look into those terms and add them here
GOOGLE_NEWS_SEARCH_QUERIES = [
    # "Canadian accessory dwelling unit",  # NOTE: looks like adding "Canadian" doesn't work well
    # "Canadian mortgage regulations",
    # "Canadian zoning laws in Toronto",
    "zoning laws",
    "accessory dwelling unit",
    "mortgage regulations",
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

article_file = "articles.json"


@app.route("/")
def index():
    articles = load_articles(article_file)

    # sorting TODO: should perhaps filter first and then sort
    sort_date = request.args.get("sort_date")
    if sort_date:
        articles.sort(key=lambda x: x[3], reverse=(sort_date == "desc"))

    sort_title = request.args.get("sort_title")
    if sort_title:
        articles.sort(key=lambda x: x[2].title, reverse=(sort_title == "desc"))

    # filters
    unfiltered_sources = sorted(list(set(article[1] for article in articles)))
    selected_sources = request.args.getlist("source")
    if selected_sources:
        articles = [article for article in articles if article[1] in selected_sources]

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

    articles = get_articles(
        queries=GOOGLE_NEWS_SEARCH_QUERIES, article_file=article_file
    )

    results = [
        article
        for article in articles
        if query.lower() in article[2].title.lower()
        or query.lower() in normalize_html_content(article[2].summary).lower()
    ]

    # sorting TODO: should perhaps filter first and then sort
    sort_date = request.args.get("sort_date")
    if sort_date:
        results.sort(key=lambda x: x[3], reverse=(sort_date == "desc"))

    sort_title = request.args.get("sort_title")
    if sort_title:
        results.sort(key=lambda x: x[2].title, reverse=(sort_title == "desc"))

    # filters
    unfiltered_sources = sorted(list(set(article[1] for article in results)))
    selected_sources = request.args.getlist("source")
    if selected_sources:
        results = [article for article in results if article[1] in selected_sources]

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
def analyze_news():  # change to 10
    articles_df = get_articles(
        GOOGLE_NEWS_SEARCH_QUERIES,
        using_df=True,
        decode_gnews=True,
        article_file=article_file,
    )
    try:

        # # Check for required columns
        # required_columns = ["id", "source", "date_published", "entry", "link"]
        # missing = [col for col in required_columns if col not in articles_df.columns]
        # if missing:
        #     raise KeyError(f"Missing required columns: {missing}")

        """
        For each article, extract the content from the link
        """
        articles_df["content"] = articles_df["link"].swifter.apply(get_article_content)

        articles_df, _ = analyze_themes(articles_df)
        articles_df = label_themes(articles_df)

        with open("articles.json", "w") as f:
            articles_df.to_json()

    except Exception as e:
        print("Error analyzing news:")
        print(e)
        return None, articles_df

    return generate_jot_notes(articles_df), articles_df


@app.route("/publication")
def publication():

    results, df = analyze_news()

    if results:
        return results, 200, {"Content-Type": "text/plain"}

    return "No results found", 404, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(port=os.environ.get("PORT") or 5000, debug=True)
