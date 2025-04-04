from enum import Enum
from pydantic import BaseModel, Field, Json as PydanticJson, ValidationError
from typing import Optional, Any

from googlenewsdecoder import GoogleDecoder

# from uuid import UUID
import json

from .utils import standardize_date_type_format, filter_text_content


class NewsItemCategory(str, Enum):
    """Enum for news item categories."""

    GOVERNMENT = "government"
    COMPANY = "company"
    COMMUNITY = "community"
    OTHER = "other"


class NewsItemSchema(BaseModel):
    __tablename__ = "news_items"

    ## required fields
    id: Optional[int] = Field(
        None, primary_key=True, description="Unique identifier for the news item"
    )
    data_source_type: str = Field(
        ..., description="Type of data source (e.g., RSS Feed)"
    )
    # CAN DELETE: data_json_old: PydanticJson[Any] = Field()
    data_json: dict = Field(
        ..., unique=True, description="JSON data from crawled article"
    )
    data_URL: str = Field(..., unique=True, description="URL of the article")
    selected_for_display: bool = Field(
        default=False, description="Selected for display"
    )
    generated_category: Optional[str] = Field(None, description="Generated category")
    generated_summary: Optional[str] = Field(None, description="Generated summary")

    # extracted/derived fields
    extracted_date_published: Optional[str] = Field(None, description="Date published")
    extracted_title: Optional[str] = Field(None, description="Title of the article")
    extracted_news_source: Optional[str] = Field(None, description="News source")
    extracted_author: Optional[str] = Field(None, description="Author of the article")
    extracted_text: Optional[str] = Field(None, description="Full text of the article")
    extracted_summary: Optional[str] = Field(None, description="Extracted summary")

    def get_online_url(self):
        """
        Retrieve the article URL. If data_URL is null/empty,
        fallback to data_json.link (if it exists).
        """

        # TODO: Decode Google News URL if necessary
        if self.data_URL:
            return self.data_URL

        # Attempt to retrieve link from data_json
        try:
            link = self.data_json.get("link")
            if link:
                return link
        except AttributeError:
            # Handle cases where data_json is not a dictionary or lacks the expected structure
            pass

        return None

    def get_news_source(self):
        """
        Retrieve the news source. If extracted_news_source is null/empty,
        fallback to data_json.source.title (if it exists).
        """
        if self.extracted_news_source:
            return self.extracted_news_source

        # Attempt to retrieve source title from data_json
        try:
            source_title = self.data_json.get("source", {}).get("title")
            if source_title:
                return source_title
        except AttributeError:
            # Handle cases where data_json is not a dictionary or lacks the expected structure
            pass

        return None

    def get_title(self):
        """
        Retrieve the title. If extracted_title is null/empty,
        fallback to data_json.title (if it exists).
        """
        if self.extracted_title:
            return self.extracted_title

        # Attempt to retrieve title from data_json
        try:
            title = self.data_json.get("title")
            if title:
                return title
        except AttributeError:
            # Handle cases where data_json is not a dictionary or lacks the expected structure
            pass

        return None

    def get_date_published(self):
        """
        Retrieve the date published. If extracted_date_published is null/empty,
        fallback to data_json.published (if it exists).
        """
        if self.extracted_date_published:
            return standardize_date_type_format(self.extracted_date_published)

        # Attempt to retrieve published date from data_json
        try:
            published_date = self.data_json.get("published")
            if published_date:
                return standardize_date_type_format(published_date)
        except AttributeError:
            # Handle cases where data_json is not a dictionary or lacks the expected structure
            pass

        return None

    def get_article_summary(self):
        """
        Retrieve the article summary. If extracted_summary is null/empty,
        fallback to data_json.summary (if it exists).
        """
        if self.extracted_summary:
            return self.extracted_summary

        # Attempt to retrieve summary from data_json
        try:
            summary = self.data_json.get("summary")
            if summary:
                return filter_text_content(summary)
        except AttributeError:
            # Handle cases where data_json is not a dictionary or lacks the expected structure
            pass

        return None
