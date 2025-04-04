import os
from dotenv import load_dotenv

from flask import Flask

from .config.config import Config
from .services.database_service import SupabaseDBService
from .scrapers.crawl4ai_scraper import Crawl4AIScraper

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

    from .routes import register_routes

    register_routes(app)

    return app
