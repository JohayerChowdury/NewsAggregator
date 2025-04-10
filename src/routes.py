from flask import (
    Blueprint,
    request,
    render_template,
    jsonify,
    session,
    redirect,
    url_for,
)
from functools import wraps
from .app import database_service, scraper, openai_service, auth_service
from .models import NewsItemSchema

# from .utils import clean_and_normalize_text
from .services.crawlers.crawler_service import CrawlerService

# Blueprints
client_routes = Blueprint("client_routes", __name__)
api_routes = Blueprint("api_routes", __name__, url_prefix="/api")


def auth_required(f):
    """
    Decorator to require authentication for a route.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("client_routes.home"))
        return f(*args, **kwargs)

    return decorated_function


@client_routes.route("/", methods=["GET"])
def home():
    return render_template("home.html")


@client_routes.route("/crawl-for-news", methods=["GET"])
def crawl_for_news():
    return render_template("crawl_for_news.html")


@client_routes.route("/news-items-on-display", methods=["GET"])
def news_items_on_display():
    page = request.args.get("page", 1, type=int)
    per_page = 15

    db_query = database_service.query_select_news_items_from_db(
        filters={
            "is_removed_from_display": False,
        }
    )
    db_query_response = db_query.execute()

    total_count = 0
    if db_query_response.data:
        total_count = len(db_query_response.data)

    paginated_query = database_service.paginate_query(
        db_query,
        page=page,
        per_page=per_page,
    )
    paginated_news_items = []
    paginated_query_response = paginated_query.execute()
    if paginated_query_response.data:
        paginated_news_items = [
            NewsItemSchema(**item) for item in paginated_query_response.data
        ]

    total_pages = (total_count + per_page - 1) // per_page

    return render_template(
        "news_items/on_display.html",
        news_items=paginated_news_items,
        page=page,
        total_count=total_count,
        total_pages=total_pages,
        pagination_url=lambda page: url_for(
            "client_routes.news_items_on_display", page=page
        ),
        title="News Items on Display",
        show_remove_button=True,
    )


@client_routes.route("/news-items", methods=["GET"])
def news_items():
    page = request.args.get("page", 1, type=int)
    per_page = 15

    db_query = database_service.query_select_news_items_from_db()
    db_query_response = db_query.execute()

    total_count = 0
    if db_query_response.data:
        total_count = len(db_query_response.data)

    paginated_query = database_service.paginate_query(
        db_query,
        page=page,
        per_page=per_page,
    )
    paginated_news_items = []
    paginated_query_response = paginated_query.execute()
    if paginated_query_response.data:
        paginated_news_items = [
            NewsItemSchema(**item) for item in paginated_query_response.data
        ]

    total_pages = (total_count + per_page - 1) // per_page

    return render_template(
        "news_items/view_all.html",
        news_items=paginated_news_items,
        page=page,
        total_count=total_count,
        total_pages=total_pages,
        pagination_url=lambda page: url_for("client_routes.news_items", page=page),
        title="All News Items",
        show_remove_button=False,
    )


@api_routes.route("/crawl-sources-and-insert-into-database", methods=["POST"])
async def crawl_sources_and_insert_into_database():
    """
    Endpoint to crawl articles from all sources and insert articles into database.
    """
    news_items = await CrawlerService.crawl_all_sources()
    if len(news_items) > 0:
        print(f"Crawled {len(news_items)} articles from all sources")
        for item in news_items:
            print(f"Database Insert: Attempting NewsItem with URL: {item.data_URL}")
            response = database_service.insert_news_item(item)
            if response.is_success():
                print(f"Database Insert Success: Created with ID {response.data.id}")
            else:
                print(f"Database Insert Failed: {response.message}")
    return 200


# @api_routes.route("/crawl-sources-and-save-to-file", methods=["POST"])
# async def crawl_sources_and_save_to_file():
#     """
#     Endpoint to crawl articles from all sources and save them to a CSV file.
#     """
#     news_items = await CrawlerService.crawl_all_sources()
#     if len(news_items) > 0:
#         print(f"Crawled {len(news_items)} articles from all sources")
#         with open("news_items.csv", "w") as file:
#             for item in news_items:
#                 file.write(f"{item.extracted_title},{item.extracted_URL}\n")
#     return 200


# @api_routes.route("/assign-category/<article_id>", methods=["POST"])
# def assign_category(article_id: int):
#     """
#     Endpoint to assign a category to an article by its ID.
#     """
#     try:
#         db_query = database_service.query_select_news_items_from_db(
#             filters={"id": article_id},
#             not_null_fields=["article_text"],
#         )
#         db_query_response = db_query.execute()

#         news_items = []
#         if db_query_response.data:
#             news_items = [NewsItemSchema(**item) for item in db_query_response.data]

#         if len(news_items) > 0:
#             item = news_items[0]
#             if item.article_text:
#                 categories = [
#                     "Government Updates regarding Legal & Financing Implications",
#                     "Company Updates regarding Products & Programs Offered",
#                     "Locality Updates regarding Construction & Community Considerations",
#                     "Other Updates regarding Middle Housing Financing in Canada",
#                 ]
#                 generated_category = openai_service.assign_category(
#                     item.article_text, categories
#                 )
#                 item.generated_category = generated_category
#                 database_service.update_news_item(item.id, item)
#                 return jsonify(item), 200

#         return jsonify({"error": "Article not found or no text available."}), 404
#     except Exception as e:
#         return jsonify({"error": f"An error occurred: {str(e)}"}), 500


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


@api_routes.route("/remove_article/<int:article_id>", methods=["POST"])
def remove_article(article_id: int):
    """
    Endpoint to remove an article from display by its ID.
    """
    try:
        response = database_service.update_news_item_removed_from_display(
            article_id, True
        )
        if response:
            return (
                jsonify({"message": "Article removed from display successfully."}),
                200,
            )
        else:
            return (
                jsonify(
                    {"error": "Article not found or could not be removed from display."}
                ),
                404,
            )
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# @api_routes.route("/auth/sign-up", methods=["POST"])
# def sign_up():
#     data = request.json
#     email = data.get("email")
#     password = data.get("password")
#     if not email or not password:
#         return jsonify({"error": "Email and password are required"}), 400

#     response = auth_service.sign_up(email, password)
#     return jsonify(response)


# @api_routes.route("/auth/sign-in", methods=["POST"])
# def sign_in():
#     data = request.json
#     email = data.get("email")
#     password = data.get("password")
#     if not email or not password:
#         return jsonify({"error": "Email and password are required"}), 400

#     response = auth_service.sign_in(email, password)
#     return jsonify(response)


# @api_routes.route("/auth/sign-out", methods=["POST"])
# def sign_out():
#     response = auth_service.sign_out()
#     return jsonify(response)
