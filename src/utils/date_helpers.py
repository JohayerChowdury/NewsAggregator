from datetime import datetime, date
from dateutil import parser
from dateutil.relativedelta import relativedelta
import pytz


def serialize_datetime(obj):
    """
    Serialize datetime object into a readable string format:
    'Day of Week, Month of Year, Year, HH:MM (in EST)'
    """
    if isinstance(obj, datetime):
        est = pytz.timezone("US/Eastern")
        obj_est = obj.astimezone(est)
        return obj_est.strftime("%A, %B %d, %Y, %I:%M %p (EST)")
    raise TypeError("Type not serializable")


def standardize_date_type_format(date_input):
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

        return serialize_datetime(d)
    except Exception as e:
        print(f"Error formatting date: {e}")
        return date_input


def get_news_search_dates():
    today = date.today() + relativedelta(
        days=1
    )  # Add 1 day to today's date to include today's articles
    six_months_ago = today - relativedelta(months=6)
    return today.strftime("%Y-%m-%d %H:%M:%S"), six_months_ago.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
