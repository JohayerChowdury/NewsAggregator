import os
from dotenv import load_dotenv

from flask import Flask

from .config.config import Config

from .services.database_service import SupabaseDBService
from .services.auth_service import SupabaseAuthService
from .services.openai_service import OpenAIService
from .services.scrapers.crawl4ai_scraper import Crawl4AIScraper
from .services.news_item_service import NewsItemService

load_dotenv()  # Load environment variables from .env file

# Supabase service instance
database_service: SupabaseDBService = None

# Supabase auth service instance
auth_service: SupabaseAuthService = None

# OpenAI service
openai_service: OpenAIService = None

# Crawl4AI scraper instance
scraper: Crawl4AIScraper = None

# NewsItem service instance
news_item_service: NewsItemService = None

# calling dev config
config = Config().dev_config


def create_app():
    app = Flask(__name__)
    app.env = config.ENV
    # app.secret_key = os.environ.get("SECRET_KEY")

    # Initialize Supabase service
    global database_service
    database_service = SupabaseDBService(
        os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
    )

    # Initialize Supabase auth service
    global auth_service
    auth_service = SupabaseAuthService(
        os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
    )

    # Initialize Crawl4AI scraper
    global scraper
    scraper = Crawl4AIScraper()

    # Initialize OpenAI service
    global openai_service
    openai_service = OpenAIService()

    # Initialize NewsItem service
    global news_item_service
    news_item_service = NewsItemService(database_service, scraper, openai_service)

    # Register blueprints
    from .routes import client_routes, api_routes

    app.register_blueprint(client_routes)
    app.register_blueprint(api_routes)

    return app
