import os
from flask import Flask, jsonify, render_template, request

# from flask_cors import CORS
import sqlite3

from server.utils.scraper import (
    load_json_to_df,
    save_df_to_json,
    get_articles,
    extract_clean_article,
    check_for_required_columns,
    RSS_FEEDS,
    GOOGLE_NEWS_SEARCH_QUERIES,
    required_columns,
)
from server.utils.ml_publication import analyze_themes, label_themes, generate_jot_notes

app = Flask(__name__)
# CORS(app)

ARTICLE_FILE = "articles.json"


@app.route("/")
def index():
    articles_df = load_json_to_df(ARTICLE_FILE, expected_columns=required_columns)

    articles = articles_df.to_dict(orient="records")

    # sorting TODO: should perhaps filter first and then sort
    sort_date = request.args.get("sort_date")
    if sort_date:
        articles.sort(key=lambda x: x["date_published"], reverse=(sort_date == "desc"))

    sort_title = request.args.get("sort_title")
    if sort_title:
        articles.sort(key=lambda x: x["title"], reverse=(sort_title == "desc"))

    # filters
    unfiltered_sources = sorted(list(set(article["source"] for article in articles)))
    selected_sources = request.args.getlist("source")
    if selected_sources:
        articles = [
            article for article in articles if article["source"] in selected_sources
        ]

    selected_google_searches = request.args.getlist("google_search")
    if selected_google_searches:
        articles = [
            article
            for article in articles
            if article["from_rss_or_query"]
            and article["from_rss_or_query"] in selected_google_searches
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

    articles_df = get_articles(
        article_file=ARTICLE_FILE, queries=GOOGLE_NEWS_SEARCH_QUERIES, decode_gnews=True
    )

    results = [
        article
        for _, article in articles_df.iterrows()
        if query.lower() in article["title"].lower()
        or query.lower() in article["summary"].lower()
    ]

    # sorting TODO: should perhaps filter first and then sort
    sort_date = request.args.get("sort_date")
    if sort_date:
        results.sort(key=lambda x: x["date_published"], reverse=(sort_date == "desc"))

    sort_title = request.args.get("sort_title")
    if sort_title:
        results.sort(key=lambda x: x["title"], reverse=(sort_title == "desc"))

    # filters
    unfiltered_sources = sorted(list(set(article["source"] for article in results)))
    selected_sources = request.args.getlist("source")
    if selected_sources:
        results = [
            article for article in results if article["source"] in selected_sources
        ]

    selected_google_searches = request.args.getlist("google_search")
    if selected_google_searches:
        articles_df = [
            article
            for article in articles_df
            if article["from_rss_or_query"]
            and article["from_rss_or_query"] in selected_google_searches
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
def analyze_news():
    articles_df = load_json_to_df(ARTICLE_FILE, expected_columns=required_columns)

    check_for_required_columns(articles_df, required_columns)

    try:

        """
        For each article, extract the content from the link
        """
        articles_df["extracted_content"] = articles_df[
            "extracted_link_url"
        ].swifter.apply(extract_clean_article)
        articles_df, _ = analyze_themes(articles_df)
        articles_df = label_themes(articles_df)

    except Exception as e:
        print("Error analyzing news:")
        print(e)

    save_df_to_json(articles_df, ARTICLE_FILE)
    return articles_df


@app.route("/publication")
def publication():

    results = analyze_news()

    if results.empty:
        return "No results found", 404, {"Content-Type": "text/plain"}

    return (
        results.head(2).to_html(),
        200,
        {"Content-Type": "text/html"},
    )


@app.route("/newsletter")
def newsletter():
    newsletter_required_columns = required_columns + [
        "extracted_content",
        "vectors",
        "theme_cluster",
        "theme_name",
    ]
    articles_df = load_json_to_df(
        ARTICLE_FILE, expected_columns=newsletter_required_columns
    )
    check_for_required_columns(articles_df, newsletter_required_columns)

    results = generate_jot_notes(articles_df)
    # return jsonify(results)

    return render_template("newsletter.html", results=results)


if __name__ == "__main__":
    app.run(port=os.environ.get("PORT") or 5000, debug=True)
