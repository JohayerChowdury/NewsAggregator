from supabase import create_client, Client, PostgrestAPIResponse
from postgrest import SyncSelectRequestBuilder
from typing import List, Optional
from enum import Enum

# from googlenewsdecoder import GoogleDecoder

from ..models import NewsItemSchema


class DatabaseResponseStatusType(Enum):
    """
    Enum for database operation status types.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


class DatabaseResponse:
    """
    Standardized response object for database operations.
    """

    def __init__(
        self,
        status: DatabaseResponseStatusType,
        data: Optional[dict] = None,
        message: Optional[str] = None,
    ):
        self.status = status
        self.data = data
        self.message = message

    def is_success(self) -> bool:
        return self.status == DatabaseResponseStatusType.SUCCESS


class SupabaseDBService:
    NEWS_ITEMS_TABLE = NewsItemSchema.__tablename__

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_client: Client = create_client(supabase_url, supabase_key)

    @staticmethod
    def paginate_query(
        query: SyncSelectRequestBuilder,
        page: int = 1,
        per_page: int = 20,
    ):
        """
        Paginate the query results.
        """
        startIndex = (page - 1) * per_page
        endIndex = startIndex + per_page - 1

        return query.range(startIndex, endIndex)

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
        sort: dict[str:str] = None,
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
            for column, value in sort.items():
                if value == "asc":
                    query = query.order(column, desc=False)
                elif value == "desc":
                    query = query.order(column, desc=True)
                else:
                    raise ValueError(
                        f"Invalid sort direction, needs to be 'asc' or 'desc': {value}"
                    )

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

    def fetch_news_items_by_data_URL(self, data_URL: str) -> PostgrestAPIResponse:
        """
        Fetch a news item by its data_URL from the database.
        """
        return (
            self.supabase_client.table(self.NEWS_ITEMS_TABLE)
            .select("*")
            .eq("data_URL", data_URL)
            .execute()
        )

    def fetch_unique_sources(self) -> List[str]:
        response = self.NEWS_ITEMS_TABLE.select("extracted_news_source").execute()
        return list(set(item["extracted_news_source"] for item in response.data))

    # CREATE METHODS
    def insert_news_item(self, news_item: NewsItemSchema) -> DatabaseResponse:
        """
        Insert a news item into the database.
        """
        try:
            # Serialize the news item, excluding unset fields (like id)
            serialized_item = news_item.get_json()

            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .insert(serialized_item)
                .execute()
            )

            if response.data:
                return DatabaseResponse(
                    status=DatabaseResponseStatusType.SUCCESS,
                    data=NewsItemSchema(**response.data[0]),
                )
            else:
                return DatabaseResponse(
                    status=DatabaseResponseStatusType.FAILURE,
                    message="No data inserted in the database.",
                )

        except Exception as e:
            return DatabaseResponse(
                status=DatabaseResponseStatusType.ERROR,
                message=f"Error inserting in database: {e}",
            )

    # UPDATE METHODS
    def update_news_item(self, id, news_item: NewsItemSchema) -> DatabaseResponse:
        """
        Update a news item in the database.
        """
        try:
            # Ensure the news item is serialized to match the database schema
            serialized_item = news_item.get_json()

            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update(serialized_item)
                .eq("id", id)
                .execute()
            )
            if response.data:
                return DatabaseResponse(
                    status=DatabaseResponseStatusType.SUCCESS,
                    data=NewsItemSchema(**response.data[0]),
                )
            else:
                return DatabaseResponse(
                    status=DatabaseResponseStatusType.FAILURE,
                    message="No data inserted in the database.",
                )

        except Exception as e:
            return DatabaseResponse(
                status=DatabaseResponseStatusType.ERROR,
                message=f"Error inserting in database: {e}",
            )

    def update_news_item_removed_from_display(
        self, id: int, is_removed_from_display: bool
    ) -> Optional[dict]:
        """
        Update the is_removed_from_display field in the database.
        """
        try:
            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .update({"is_removed_from_display": is_removed_from_display})
                .eq("id", id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating is_removed_from_display: {e}")
            return None

    # DELETE METHODS
    def delete_news_item(self, id: int) -> Optional[dict]:
        """
        Delete a news item from the database.
        """
        try:
            response: PostgrestAPIResponse = (
                self.supabase_client.table(self.NEWS_ITEMS_TABLE)
                .delete()
                .eq("id", id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error deleting news item: {e}")
            return None
