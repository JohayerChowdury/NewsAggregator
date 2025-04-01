import json
import csv

from flask import Flask, request, render_template, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import distinct

from .models import NewsItem
from .crawlers import rss_feed_crawl, google_news_crawl

from .scrapers.beautifulsoup_scraper import extract_clean_article
from .scrapers.crawl4ai_scraper import extract_clean_article_crawl4ai


def get_all_sources(db: SQLAlchemy):
    return [
        source[0]
        for source in db.session.query(distinct(NewsItem.article_news_source)).all()
    ]


def register_routes(app: Flask, db: SQLAlchemy):
    @app.route("/", methods=["GET"])
    def index():
        if request.method == "GET":
            query = NewsItem.query

            # filters
            unfiltered_sources = get_all_sources(db)
            selected_sources = request.args.getlist("source")
            if selected_sources:
                query = query.filter(NewsItem.article_news_source.in_(selected_sources))

            # sorting
            sort_date = request.args.get("sort_date")
            if sort_date:
                query = query.order_by(
                    NewsItem.article_date_published.desc()
                    if sort_date == "desc"
                    else NewsItem.article_date_published.asc()
                )

            sort_title = request.args.get("sort_title")
            if sort_title:
                query = query.order_by(
                    NewsItem.article_title.desc()
                    if sort_title == "desc"
                    else NewsItem.article_title.asc()
                )

            # pagination
            page = request.args.get("page", 1, type=int)
            per_page = 20
            paginated_articles = query.paginate(
                page=page, per_page=per_page, error_out=False
            )

            return render_template(
                "index.html",
                news_items=paginated_articles.items,
                sources=unfiltered_sources,
                selected_sources=selected_sources,
                sort_date=sort_date,
                sort_title=sort_title,
                page=page,
                total_pages=paginated_articles.pages,
            )
        elif request.method == "POST":
            # Handle form submission here if needed
            pass

    @app.route("/search")
    def search():
        query = request.args.get("query", "").strip()
        if not query:
            return "No query provided", 400, {"Content-Type": "text/plain"}

        # query_embedding = get_model_embeddings([query])

        results = [
            article
            for _, article in articles_df.iterrows()
            if query.lower() in article["title"].lower()
            or query.lower() in article["summary"].lower()
        ]

        # sorting TODO: should perhaps filter first and then sort
        sort_date = request.args.get("sort_date")
        if sort_date:
            results.sort(
                key=lambda x: x["date_published"], reverse=(sort_date == "desc")
            )

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
                if article["crawled_from"]
                and article["crawled_from"] in selected_google_searches
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
            # rss_feeds=RSS_FEEDS,
            # google_queries=GOOGLE_NEWS_SEARCH_QUERIES,
        )

    @app.route("/api/relevant-news", methods=["POST"])
    async def relevant_news():
        if request.method == "POST":

            async def process_news_items(news_items):
                debug_news_items = []
                new_articles_count = 0

                for entry in news_items:
                    article_data = entry["data_entry"]
                    data_source = entry.get("data_source", "Unknown")
                    article_link = entry["article_link"]

                    # Check if the article already exists in the database
                    existing_article = NewsItem.query.filter_by(
                        article_link=article_link
                    ).first()

                    if not existing_article:
                        # # Scrape article data asynchronously
                        # article_text = await extract_clean_article_crawl4ai(
                        #     article_link
                        # )

                        # Create a new NewsItem object
                        news_item = NewsItem(
                            data_source=data_source,
                            article_data=article_data,
                            article_link=article_link,
                            # article_text=article_text,
                        )
                        db.session.add(news_item)
                        new_articles_count += 1
                        debug_news_items.append(article_data)

                # Commit the new articles to the database
                db.session.commit()
                return debug_news_items, new_articles_count

            news_items = []

            # Crawl articles using the RSS feed crawler
            crawled_articles_from_rss = rss_feed_crawl.main()
            news_items.extend(crawled_articles_from_rss)

            # # Crawl articles using the Google News crawler
            # crawled_articles_from_google = google_news_crawl.main()
            # news_items.extend(crawled_articles_from_google)

            # Process the news items asynchronously
            debug_news_items, new_articles_count = await process_news_items(news_items)

            return (
                jsonify(
                    {
                        "message": f"{new_articles_count} new articles added to the database.",
                        "debug_news_items": debug_news_items,
                    }
                ),
                200,
            )

    @app.route("/api/toggle_display/<int:article_id>", methods=["POST"])
    def toggle_display(article_id):
        data = request.get_json()
        selected = data.get("selected", False)
        article = NewsItem.query.get(article_id)
        if article:
            article.selected_for_display = selected
            db.session.commit()
            return {"message": "Updated successfully"}, 200
        return {"message": "Article not found"}, 404

    @app.route("/api/download_csv", methods=["GET"])
    def download_csv():
        articles = NewsItem.query.filter_by(selected_for_display=True).all()
        csv_data = [["Title", "Link", "Source", "Published Date"]]
        for article in articles:
            csv_data.append(
                [
                    article.article_title,
                    article.article_link,
                    article.article_news_source,
                    article.article_date_published,
                ]
            )

        def generate():
            for row in csv_data:
                yield ",".join(map(str, row)) + "\n"

        return Response(
            generate(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment;filename=selected_articles.csv"
            },
        )
