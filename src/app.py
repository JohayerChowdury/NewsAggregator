import os
from dotenv import load_dotenv

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_migrate import Migrate

from .config.config import Config


class Base(DeclarativeBase):
    pass


# sql achemy instance
db = SQLAlchemy(model_class=Base)

# calling dev config
config = Config().dev_config

SQLALCHEMY_DATABASE_URI = (
    os.environ.get("DATABASE_URI") or "sqlite:///./news-aggregator-db.db"
)


def create_app():
    app = Flask(__name__)
    app.env = config.ENV
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLACHEMY_TRACK_MODIFICATIONS"] = os.environ.get(
        "SQLACHEMY_TRACK_MODIFICATIONS", False
    )
    app.secret_key = os.environ.get("SECRET_KEY")

    db.init_app(app)

    from .routes import register_routes

    register_routes(app, db)

    # Flask Migrate instance to handle migrations
    migrate = Migrate(app, db)

    return app
