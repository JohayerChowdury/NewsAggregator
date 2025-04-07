import os
from dotenv import load_dotenv

from flask import Flask

from .config.config import Config

from .services.openai_service import OpenAIService
from .services.database_service import SupabaseDBService
from .services.scrapers.crawl4ai_scraper import Crawl4AIScraper

load_dotenv()  # Load environment variables from .env file

# OpenAI service
openai_service: OpenAIService = None

# Supabase service instance
database_service: SupabaseDBService = None

# Crawl4AI scraper instance
scraper: Crawl4AIScraper = None

# calling dev config
config = Config().dev_config


def create_app():
    app = Flask(__name__)
    app.env = config.ENV
    app.secret_key = os.environ.get("SECRET_KEY")

    # Initialize Supabase service
    global database_service
    database_service = SupabaseDBService(
        os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
    )

    # Initialize Crawl4AI scraper
    global scraper
    scraper = Crawl4AIScraper()

    # Initialize OpenAI service
    global openai_service
    openai_service = OpenAIService()

    # Register blueprints
    from .routes import client_routes, api_routes

    app.register_blueprint(client_routes)
    app.register_blueprint(api_routes)

    return app
