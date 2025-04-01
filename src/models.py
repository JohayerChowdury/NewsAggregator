from sqlalchemy import String, DateTime, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
import json

from .app import db
from .utils import standardize_date


class NewsItem(db.Model):
    __tablename__ = "news_items"
    __table_args__ = (UniqueConstraint("article_link", name="uq_article_link"),)

    ## required fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data_source: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Source of the article (e.g., RSS feed, Google News)
    data_json: Mapped[str] = mapped_column(
        String, nullable=False
    )  # JSON data from crawled article
    article_link: Mapped[str] = mapped_column(
        String, nullable=False, unique=True
    )  # URL of the article
    category: Mapped[str | None] = mapped_column(String, nullable=False)
    llm_generated_summary: Mapped[str | None] = mapped_column(Text, nullable=False)

    ## extracted fields
    article_date_published: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    article_title: Mapped[str] = mapped_column(String, nullable=False)
    article_news_source: Mapped[str] = mapped_column(String, nullable=False)
    article_author: Mapped[str | None] = mapped_column(String, nullable=True)
    article_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    article_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    ## generated fields
    original_url: Mapped[str | None] = mapped_column(String, nullable=True)
    selected_for_display: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"<Article {self.article_title}>"

    def __init__(self, data_source, data, article_link, **kwargs):
        self.data_source = data_source
        self.data_json = json.dumps(data)
        self.article_link = article_link

        self.article_date_published = standardize_date(data["published"])
        self.article_title = data["title"]

        try:
            self.article_news_source = data["source"]["title"]
        except KeyError:
            self.article_news_source = data_source

        try:
            self.article_author = data["author"]
        except KeyError:
            self.article_author = None

        try:
            self.original_url = data["link"]
        except KeyError:
            self.original_url = None

        self.selected_for_display = kwargs.get("selected_for_display", False)

    @property
    def article_data(self):
        return json.loads(self.data_json)
