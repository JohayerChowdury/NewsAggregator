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
    # auth_service,
    news_item_service,
)
from .models import NewsItemSchema

# Blueprints
client_routes = Blueprint("client_routes", __name__)
api_routes = Blueprint("api_routes", __name__, url_prefix="/api")


# TODO: Add authentication service and implement auth_service.login_user() and auth_service.logout_user()
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
        show_actions_button=True,
    )


@client_routes.route("/all-news-items", methods=["GET"])
def all_news_items():
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
        pagination_url=lambda page: url_for("client_routes.all_news_items", page=page),
        title="All News Items",
        show_actions_button=False,
    )


@api_routes.route("/crawl-for-news", methods=["GET"])
async def crawl_for_news():
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
    return jsonify({"error": "Invalid request method"}), 405


@api_routes.route("/scrape-articles", methods=["GET"])
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


@api_routes.route("/generate-categories", methods=["GET"])
async def generate_categories():
    """
    Endpoint to generate content for articles that require it.
    """
    try:
        articles = await news_item_service.categorize_articles()
        return (
            jsonify(
                {
                    "message": "Content for articles with the following IDs have been generated and updated in the database.",
                    "data": articles,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@api_routes.route("/generate-summaries", methods=["GET"])
async def generate_summaries():
    """
    Endpoint to generate content for articles that require it.
    """
    try:
        articles = await news_item_service.summarize_articles()
        return (
            jsonify(
                {
                    "message": "Content for articles with the following IDs have been generated and updated in the database.",
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


@api_routes.route("/toggle_select_for_download/<int:article_id>", methods=["POST"])
def toggle_select_for_download(article_id: int):
    """
    Endpoint to toggle the 'is_selected_for_download' status of an article by its ID.
    """
    try:
        data = request.get_json()
        is_selected_for_download = data.get("is_selected_for_download", False)
        response = database_service.update_news_item_selected_for_download(
            article_id, is_selected_for_download
        )
        if response:
            return (
                jsonify(
                    {
                        "message": "Article 'Select for Download' status updated successfully."
                    }
                ),
                200,
            )
        else:
            return (
                jsonify({"error": "Article not found or could not be updated."}),
                404,
            )
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@api_routes.route("/download-articles", methods=["GET"])
def download_articles():
    """
    Endpoint to download articles that are selected for download.
    """
    try:
        articles = news_item_service.download_selected_articles_as_csv(
            "selected_articles.csv"
        )
        return jsonify({"message": "Articles downloaded successfully."}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
