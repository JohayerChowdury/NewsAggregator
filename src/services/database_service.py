from supabase import create_client, Client, PostgrestAPIResponse
from typing import List, Optional

# from googlenewsdecoder import GoogleDecoder

from ..models import NewsItemSchema


class SupabaseDBService:
    NEWS_ITEMS_TABLE = NewsItemSchema.__tablename__

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_client: Client = create_client(supabase_url, supabase_key)

    # READ METHODS
    def query_ALL_news_items_from_db(self):
        """
        Query all news items from the database.
        """
        return (
            self.supabase_client.table(self.NEWS_ITEMS_TABLE)
            .select("*")
            .order("extracted_date_published", desc=True)
        )

    def query_select_news_items_from_db(
        self,
        filters: dict = None,
        not_null_fields: List[str] = None,
        sort: dict = None,
    ):
        query = self.query_ALL_news_items_from_db()

        # Apply filters
        if filters:
            for column, value in filters.items():
                if value == "null":
                    query = query.is_(column, "null")
                else:
                    query = query.eq(column, value)

        # Apply not-null checks
        if not_null_fields:
            for field in not_null_fields:
                query = query.not_.is_(field, "null")

        # Apply sorting
        if sort:
            for column, desc in sort.items():
                query = query.order(column, desc=desc)

        return query

    def fetch_news_items_by_id(self, id: int) -> Optional[dict]:
        """
        Fetch a news item by its ID from the database.
        """
        response: PostgrestAPIResponse = (
            self.supabase_client.table(self.NEWS_ITEMS_TABLE)
            .select("*")
            .eq("id", id)
            .execute()
        )
        return response.data[0] if response.data else None

    def fetch_unique_sources(self) -> List[str]:
        response = self.NEWS_ITEMS_TABLE.select("extracted_news_source").execute()
        return list(set(item["extracted_news_source"] for item in response.data))

    # CREATE METHODS
    def insert_news_item(self, news_item: NewsItemSchema) -> Optional[dict]:
        """
        Insert a news item into the database.
        """
        try:
            # Serialize the news item, excluding unset fields (like id)
            serialized_item = news_item.model_dump(exclude_unset=True)

            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .insert(serialized_item)
                .execute()
            )

            return response.data[0] if response.data else None

        except Exception as e:
            print(f"Error inserting in database: {e}")
            return None

    # UPDATE METHODS
    def update_news_item(self, id, news_item: NewsItemSchema) -> Optional[dict]:
        """
        Update a news item in the database.
        """
        try:
            # Ensure the news item is serialized to match the database schema
            serialized_item = news_item.model_dump()

            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update(serialized_item)
                .eq("id", id)
                .execute()
            )

            return response.data[0] if response.data else None

        except Exception as e:
            print(f"Error updating news item: {e}")
            return None

    # def update_extracted_date_published(
    #     self, id: int, date_published: str
    # ) -> Optional[dict]:
    #     """
    #     Update the extracted_date_published field in the database.
    #     """
    #     try:
    #         response: PostgrestAPIResponse = (
    #             self.supabase_client.table(self.NEWS_ITEMS_TABLE)
    #             .update({"extracted_date_published": date_published})
    #             .eq("id", id)
    #             .execute()
    #         )
    #         return response.data[0] if response.data else None
    #     except Exception as e:
    #         print(f"Error updating extracted_date_published: {e}")
    #         return None

    # def update_extracted_title(self, id: int, title: str) -> Optional[dict]:
    #     """
    #     Update the extracted_title field in the database.
    #     """
    #     try:
    #         response: PostgrestAPIResponse = (
    #             self.supabase_client.table(self.NEWS_ITEMS_TABLE)
    #             .update({"extracted_title": title})
    #             .eq("id", id)
    #             .execute()
    #         )
    #         return response.data[0] if response.data else None
    #     except Exception as e:
    #         print(f"Error updating extracted_title: {e}")
    #         return None

    # def update_extracted_news_source(self, id: int, news_source: str) -> Optional[dict]:
    #     """
    #     Update the extracted_news_source field in the database.
    #     """
    #     try:
    #         response: PostgrestAPIResponse = (
    #             self.supabase_client.table(self.NEWS_ITEMS_TABLE)
    #             .update({"extracted_news_source": news_source})
    #             .eq("id", id)
    #             .execute()
    #         )
    #         return response.data[0] if response.data else None
    #     except Exception as e:
    #         print(f"Error updating extracted_news_source: {e}")
    #         return None

    # def update_extracted_author(self, id: int, author: str) -> Optional[dict]:
    #     """
    #     Update the extracted_author field in the database.
    #     """
    #     try:
    #         response: PostgrestAPIResponse = (
    #             self.supabase_client.table(self.NEWS_ITEMS_TABLE)
    #             .update({"extracted_author": author})
    #             .eq("id", id)
    #             .execute()
    #         )
    #         return response.data[0] if response.data else None
    #     except Exception as e:
    #         print(f"Error updating extracted_author: {e}")
    #         return None

    # def update_article_text(self, id: int, text: str) -> Optional[dict]:
    #     """
    #     Update the article_text field in the database.
    #     """
    #     try:
    #         response: PostgrestAPIResponse = (
    #             self.supabase_client.table(self.NEWS_ITEMS_TABLE)
    #             .update({"article_text": text})
    #             .eq("id", id)
    #             .execute()
    #         )
    #         return response.data[0] if response.data else None
    #     except Exception as e:
    #         print(f"Error updating article_text: {e}")
    #         return None

    # def update_extracted_summary(self, id: int, summary: str) -> Optional[dict]:
    #     """
    #     Update the extracted_summary field in the database.
    #     """
    #     try:
    #         response: PostgrestAPIResponse = (
    #             self.supabase_client.table(self.NEWS_ITEMS_TABLE)
    #             .update({"extracted_summary": summary})
    #             .eq("id", id)
    #             .execute()
    #         )
    #         return response.data[0] if response.data else None
    #     except Exception as e:
    #         print(f"Error updating extracted_summary: {e}")
    #         return None

    # def update_generated_summary(self, id: int, summary: str) -> Optional[dict]:
    #     """Update the generated_summary field in the database."""
    #     try:
    #         response: PostgrestAPIResponse = (
    #             self.supabase_client.table(self.NEWS_ITEMS_TABLE)
    #             .update({"generated_summary": summary})
    #             .eq("id", id)
    #             .execute()
    #         )
    #         return response.data[0] if response.data else None
    #     except Exception as e:
    #         print(f"Error updating generated_summary: {e}")
    #         return None

    # def update_generated_category(self, id: int, category: str) -> Optional[dict]:
    #     """Update the generated_category field in the database."""
    #     try:
    #         response: PostgrestAPIResponse = (
    #             self.supabase_client.table(self.NEWS_ITEMS_TABLE)
    #             .update({"generated_category": category})
    #             .eq("id", id)
    #             .execute()
    #         )
    #         return response.data[0] if response.data else None
    #     except Exception as e:
    #         print(f"Error updating generated_category: {e}")
    #         return None
