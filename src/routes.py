from flask import Flask, request, render_template, Response, jsonify

from .app import database_service, scraper
from .crawlers import rss_feed_crawl, google_news_crawl
from .services.database_service import PostgrestAPIResponse
from .models import NewsItemSchema

# from .index_server import create_embedding, generate_summary, classify_text


# TODO: create flask blueprint for api routes
def register_routes(app: Flask):
    @app.route("/", methods=["GET"])
    def index():
        if request.method == "GET":
            # search_query = request.args.get("search_query", "").strip()

            # # Filters
            # selected_sources = request.args.getlist("source")

            # Sorting
            # sort_date = request.args.get("sort_date")
            # sort_title = request.args.get("sort_title")
            # sort = {}
            # if sort_date:
            #     sort["extracted_date_published"] = sort_date == "desc"
            # if sort_title:
            #     sort["extracted_title"] = sort_title == "desc"

            # Pagination
            page = request.args.get("page", 1, type=int)
            per_page = 20
            start = (page - 1) * per_page
            end = start + per_page - 1

            response = database_service.fetch_news_items_from_db(
                startIndex=start,
                endIndex=end,
            )

            news_items_list = []
            if response.data:
                news_items_list = [NewsItemSchema(**item) for item in response.data]

            return render_template(
                "index.html",
                news_items=news_items_list,
                # selected_sources=selected_sources,
                # sort_date=sort_date,
                # sort_title=sort_title,
                page=page,
                total_pages=(0 + per_page - 1) // per_page,
            )

    @app.route(
        "/api/news", methods=["POST"]
    )  # crawl for news, scrape news articles for text, generate summaries and categories, insert items into database
    async def generate_news():
        if request.method == "POST":
            news_items = database_service.get_news_items(
                checking_for_nulls={"extracted_text": "null"}
            )

    # async def crawl_scrape_generate_insert_relevant_news():
    #     if request.method == "POST":
    #         news_items = [NewsItemSchema]

    #         # Crawl articles using the RSS feed crawler
    #         try:
    #             crawled_articles_from_rss = await rss_feed_crawl.main()
    #             news_items.extend(crawled_articles_from_rss)
    #         except Exception as e:
    #             print(f"Error crawling RSS feed: {e}")

    #         # Crawl articles using the Google News crawler
    #         try:
    #             crawled_articles_from_google = await google_news_crawl.main()
    #             news_items.extend(crawled_articles_from_google)
    #         except Exception as e:
    #             print(f"Error crawling Google News: {e}")

    #         inserted_items = []
    #         for item in news_items:
    #             # Scrape the article using Crawl4AI scraper

    #             response = database_service.insert_news_item(item)
    #             inserted_items.append(response)

    #         return jsonify(inserted_items)

    # # Debugging purposes
    # async def crawl():
    #     if request.method == "POST":
    #         news_items = [NewsItemSchema]

    #         # # Crawl articles using the RSS feed crawler
    #         # try:
    #         #     crawled_articles_from_rss = await rss_feed_crawl.main()
    #         #     news_items.extend(crawled_articles_from_rss)
    #         # except Exception as e:
    #         #     print(f"Error crawling RSS feed: {e}")

    #         # Crawl articles using the Google News crawler
    #         try:
    #             crawled_articles_from_google = await google_news_crawl.main()
    #             news_items.extend(crawled_articles_from_google)
    #         except Exception as e:
    #             print(f"Error crawling Google News: {e}")

    #         inserted_items = []
    #         for item in news_items:
    #             # Scrape the article using Crawl4AI scraper

    #             response = database_service.insert_news_item(item)
    #             inserted_items.append(response)

    #         return jsonify(inserted_items)

    @app.route("/api/scrape-news-with-null-text", methods=["POST"])
    # Debugging purposes
    async def scrape():
        if request.method == "POST":
            news_items = database_service.get_news_items(
                checking_for_nulls={"extracted_text": "null"}
            )
            try:
                await scraper.concurrently_scrape_and_update(
                    news_items, database_service
                )
                return jsonify({"message": "Scraping completed"}), 200
            except Exception as e:
                print(f"Error during scraping: {e}")
                return jsonify({"error": "An error occurred during scraping"}), 500

    # @app.route("/api/process-text", methods=["POST"])
    # async def process_text():
    #     """Process text to generate embeddings, summaries, and categories."""
    #     if request.method == "GET":
    #         news_item_with_id_14 = database_service.fetch_news_items_by_id(
    #             news_item_id=14
    #         )
    #         return news_item_with_id_14.data[0]
    #     elif request.method == "POST":

    #         try:
    #             # Generate embedding
    #             embedding = create_embedding(text)
    #             database_service.update_embedding(news_item_id, embedding)

    #             # Generate summary
    #             summary = generate_summary(text)
    #             database_service.update_generated_summary(news_item_id, summary)

    #             # Classify text
    #             categories = ["Government", "Company", "Community"]
    #             category = classify_text(text, categories)
    #             database_service.update_generated_category(news_item_id, category)

    #             return jsonify({"message": "Text processing completed"}), 200
    #         except Exception as e:
    #             print(f"Error during processing: {e}")
    #             return jsonify({"error": "An error occurred during processing"}), 500
