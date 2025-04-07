from flask import Blueprint, request, render_template, jsonify

from .app import database_service, scraper, openai_service
from .services.crawlers import rss_feed_crawl, google_news_crawl
from .models import NewsItemSchema
from .utils import filter_text_content

# Blueprints
client_routes = Blueprint("client_routes", __name__)
api_routes = Blueprint("api_routes", __name__, url_prefix="/api")


# Client-side routes
@client_routes.route("/", methods=["GET"])
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page - 1

    sort_date = request.args.get("sort_date", "desc")
    sort_title = request.args.get("sort_title", "asc")
    sort = {
        "extracted_published_date": sort_date == "asc",
        "extracted_title": sort_title == "desc",
    }

    all_news_items = []
    db_query = database_service.query_select_news_items_from_db()
    db_query_response = db_query.execute()

    if db_query_response.data:
        all_news_items = [NewsItemSchema(**item) for item in db_query_response.data]
    else:
        return render_template("index.html", news_items=[], page=page, total_pages=0)

    paginated_news_items = all_news_items[start : end + 1]
    total_count = len(all_news_items)
    total_pages = (total_count + per_page - 1) // per_page

    return render_template(
        "index.html",
        news_items=paginated_news_items,
        page=page,
        total_pages=total_pages,
    )


# API routes
@api_routes.route("/crawl", methods=["POST"])
async def crawl():
    news_items = []
    try:
        crawled_articles_from_rss = await rss_feed_crawl.main()
        news_items.extend(crawled_articles_from_rss)
    except Exception as e:
        print(f"Error crawling RSS feeds: {e}")

    try:
        crawled_articles_from_google = await google_news_crawl.main()
        news_items.extend(crawled_articles_from_google)
    except Exception as e:
        print(f"Error crawling Google News: {e}")

    inserted_items = []
    for item in news_items:
        response = database_service.insert_news_item(item)
        inserted_items.append(response)

    return jsonify(inserted_items)


@api_routes.route("/scrape", methods=["POST"])
async def scrape():
    # db_query = database_service.query_news_items_from_db() # uncomment if you want to scrape all items
    db_query = database_service.query_select_news_items_from_db(
        {
            "article_text": "null",
        }
    )

    db_query_response = db_query.execute()

    news_items = []
    if db_query_response.data:
        news_items = [NewsItemSchema(**item) for item in db_query_response.data]

    inserted_items = []

    if len(news_items) > 0:
        for item in news_items:
            try:
                scraped_text = await scraper.scrape_url(item.get_online_url())
                if scraped_text:
                    # print(f"Scraped text for item id {item.id}: {scraped_text}")
                    filtered_text = filter_text_content(scraped_text)
                    # print(f"Filtered text for item id {item.id}: {filtered_text}")
                    item.article_text = filtered_text
                    database_service.update_news_item(item.id, item)
                    inserted_items.append(item)
                    print(f"Updated item id {item.id} in the database")
                else:
                    inserted_items.append(f"no text with item id {item.id}")
            except Exception as e:
                print(f"Error scraping item id {item.id}: {e}")
                inserted_items.append(f"error with item id {item.id}")

    return jsonify(inserted_items)


@api_routes.route("/assign-categories", methods=["POST"])
def assign_categories():
    db_query = database_service.query_select_news_items_from_db(
        filters={"generated_category": "null"},
        not_null_fields=["article_text"],
    )
    db_query_response = db_query.execute()

    news_items = []
    if db_query_response.data:
        news_items = [NewsItemSchema(**item) for item in db_query_response.data]

    inserted_items = []

    if len(news_items) > 0:

        categories = [
            "Government Updates regarding Legal & Financing Implications",
            "Company Updates regarding Products & Programs Offered",
            "Locality Updates regarding Construction & Community Considerations",
            "Other Updates regarding Middle Housing Financing in Canada",
        ]

        for item in news_items:
            if item.article_text:
                # inserted_items.append(f"item id {item.id} has text")  # DEBUG
                generated_category = openai_service.assign_category(
                    item.article_text, categories
                )
                item.generated_category = generated_category
                database_service.update_news_item(item.id, item)
                inserted_items.append(item)

    return jsonify(inserted_items)


@api_routes.route("/generate-summaries", methods=["POST"])
def generate_summaries():
    db_query = database_service.query_select_news_items_from_db(
        filters={"generated_summary": "null"},
        not_null_fields=["article_text"],
    )
    db_query_response = db_query.execute()

    news_items = []
    if db_query_response.data:
        news_items = [NewsItemSchema(**item) for item in db_query_response.data]

    inserted_items = []

    if len(news_items) > 0:
        for item in news_items:
            if item.article_text:
                generated_summary = openai_service.generate_summary(item.article_text)
                item.generated_summary = generated_summary
                database_service.update_news_item(item.id, item)
                inserted_items.append(item)

    return jsonify(inserted_items)
