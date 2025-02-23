from datetime import datetime, date
from dateutil import parser
from dateutil.relativedelta import relativedelta


def standardize_date(date_input):
    if not date_input or date_input is None:
        return None
    try:
        # instead of just date parser.parse(value)
        if isinstance(date_input, str):
            d = parser.parse(date_input)
        elif isinstance(date_input, tuple):
            d = datetime(*date_input[:6])
        elif isinstance(date_input, date):
            d = date(date_input.year, date_input.month, date_input.day)
        else:
            raise ValueError("Unsupported date format.")

        return d.strftime("%Y-%m-%d %H:%M:%S")  # Standardized storage format
    except Exception as e:
        print(f"Error formatting date: {e}")
        return date_input


def serialize_datetime(obj):
    """
    Serialize datetime object into string
    """
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d")
    raise TypeError("Type not serializable")


def get_news_search_dates():
    today = date.today() + relativedelta(
        days=1
    )  # Add 1 day to today's date to include today's articles
    six_months_ago = today - relativedelta(months=6)
    return standardize_date(today), standardize_date(six_months_ago)
