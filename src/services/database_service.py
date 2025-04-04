from supabase import create_client, Client, PostgrestAPIResponse
from typing import List, Optional

# from googlenewsdecoder import GoogleDecoder

from ..models import NewsItemSchema


class SupabaseDBService:
    NEWS_ITEMS_TABLE = NewsItemSchema.__tablename__

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_client: Client = create_client(supabase_url, supabase_key)

    # def decode_gnews_url(self, url: str) -> str:
    #     data_URL = news_item.data_URL
    #     try:
    #         if GoogleDecoder.get_base64_str(data_URL)["status"] == True:
    #             decoded_url_response = GoogleDecoder.decode_google_news_url(data_URL)
    #             if decoded_url_response["status"]:
    #                 news_item.data_URL = decoded_url_response["decoded_url"]
    #             else:
    #                 print(
    #                     f"Error decoding URL {data_URL}: {decoded_url_response['message']}"
    #                 )

    #     except:
    #         print(f"Error inserting news item: {e}")
    #         return None

    # READ METHODS
    def fetch_news_items_from_db(
        self,
        startIndex: int = None,
        endIndex: int = None,
        filters: dict = None,
        sort: dict = None,
        checking_for_nulls: dict = None,
    ) -> PostgrestAPIResponse:
        query = self.supabase_client.table(self.NEWS_ITEMS_TABLE).select("*")

        # Apply filters
        if filters:
            for column, value in filters.items():
                query = query.eq(column, value)

        # Apply sorting
        if sort:
            for column, desc in sort.items():
                query = query.order(column, desc=desc)

        if checking_for_nulls:
            for column, value in checking_for_nulls.items():
                if value == "null":
                    query = query.is_(column, "null")
                else:
                    query = query.eq(column, value)

        # Apply pagination
        if startIndex is not None and endIndex is not None:
            query = query.range(startIndex, endIndex)
        elif startIndex is not None:
            query = query.range(startIndex, startIndex + 20)
        elif endIndex is not None:
            query = query.range(0, endIndex)
        else:
            query = query.range(0, 20)

        response = query.execute()

        return response

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

    def get_news_items(
        self,
        startIndex: int = None,
        endIndex: int = None,
        filters: dict = None,
        sort: dict = None,
        checking_for_nulls: dict = None,
    ) -> List[NewsItemSchema]:
        """
        Fetch all news items from the database and convert them to NewsItemSchema objects.
        """
        response = self.fetch_news_items_from_db(
            startIndex=startIndex,
            endIndex=endIndex,
            filters=filters,
            sort=sort,
            checking_for_nulls=checking_for_nulls,
        )
        return (
            [NewsItemSchema(**item) for item in response.data] if response.data else []
        )

    # def fetch_unique_sources(self) -> List[str]:
    #     response = self.news_items_table.select("extracted_news_source").execute()
    #     return list(set(item["extracted_news_source"] for item in response.data))

    # CREATE METHODS
    def insert_news_item(self, news_item: NewsItemSchema) -> Optional[dict]:
        """
        Insert a news item into the database.
        """
        try:
            # Ensure the news item is serialized to match the database schema
            serialized_item = news_item.model_dump()

            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .insert(serialized_item)
                .execute()
            )

            return response.data[0] if response.data else None

        except Exception as e:
            print(f"Error inserting news item: {e}")
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

    def update_extracted_date_published(
        self, id: int, date_published: str
    ) -> Optional[dict]:
        """
        Update the extracted_date_published field in the database.
        """
        try:
            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update({"extracted_date_published": date_published})
                .eq("id", id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating extracted_date_published: {e}")
            return None

    def update_extracted_title(self, id: int, title: str) -> Optional[dict]:
        """
        Update the extracted_title field in the database.
        """
        try:
            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update({"extracted_title": title})
                .eq("id", id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating extracted_title: {e}")
            return None

    def update_extracted_news_source(self, id: int, news_source: str) -> Optional[dict]:
        """
        Update the extracted_news_source field in the database.
        """
        try:
            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update({"extracted_news_source": news_source})
                .eq("id", id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating extracted_news_source: {e}")
            return None

    def update_extracted_author(self, id: int, author: str) -> Optional[dict]:
        """
        Update the extracted_author field in the database.
        """
        try:
            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update({"extracted_author": author})
                .eq("id", id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating extracted_author: {e}")
            return None

    def update_extracted_text(self, id: int, text: str) -> Optional[dict]:
        """
        Update the extracted_text field in the database.
        """
        try:
            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update({"extracted_text": text})
                .eq("id", id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating extracted_text: {e}")
            return None

    def update_extracted_summary(self, id: int, summary: str) -> Optional[dict]:
        """
        Update the extracted_summary field in the database.
        """
        try:
            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update({"extracted_summary": summary})
                .eq("id", id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating extracted_summary: {e}")
            return None

    # def update_embedding(self, id: int, embedding: list) -> Optional[dict]:
    #     """Update the embedding field in the database."""
    #     try:
    #         response: PostgrestAPIResponse = (
    #             self.supabase_client.table(self.NEWS_ITEMS_TABLE)
    #             .update({"embedding": embedding})
    #             .eq("id", id)
    #             .execute()
    #         )
    #         return response.data[0] if response.data else None
    #     except Exception as e:
    #         print(f"Error updating embedding: {e}")
    #         return None

    def update_generated_summary(self, id: int, summary: str) -> Optional[dict]:
        """Update the generated_summary field in the database."""
        try:
            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update({"generated_summary": summary})
                .eq("id", id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating generated_summary: {e}")
            return None

    def update_generated_category(self, id: int, category: str) -> Optional[dict]:
        """Update the generated_category field in the database."""
        try:
            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update({"generated_category": category})
                .eq("id", id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating generated_category: {e}")
            return None
