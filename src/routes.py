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
from .app import (
    database_service,
    auth_service,
    news_item_service,
)
from .models import NewsItemSchema

# from .utils import clean_and_normalize_text

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


@client_routes.route("/getting-news", methods=["GET"])
def getting_news():
    return render_template("getting_news.html")


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
        show_remove_article_button=True,
    )


@client_routes.route("/news-items", methods=["GET"])
def news_items():
    page = request.args.get("page", 1, type=int)
    per_page = 15

    db_query = database_service.query_select_news_items_from_db(sort={"id": "asc"})
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
        show_remove_article_button=False,
    )


@api_routes.route("/news", methods=["GET", "POST"])
async def news():
    if request.method == "GET":
        articles = await news_item_service.crawl_all_sources()
        return (
            jsonify(
                {
                    "message": "Articles with the following IDs have been crawled and added to the database.",
                    "data": articles,
                }
            ),
            200,
        )
    elif request.method == "POST":
        articles = await news_item_service.summarize_and_categorize_articles()
        return jsonify(
            {
                "message": "Articles have been scraped and summarized.",
                "data": articles,
            }
        )
    return jsonify({"error": "Invalid request method"}), 405


@api_routes.route("/scrape-articles", methods=["POST"])
async def scrape_articles():
    """
    Endpoint to scrape articles that require scraping.
    """
    try:
        articles = await news_item_service.scrape_articles()
        return (
            jsonify(
                {
                    "message": "Articles with the following IDs have been scraped and updated in the database.",
                    "data": articles,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


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
