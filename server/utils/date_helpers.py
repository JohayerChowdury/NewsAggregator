from datetime import datetime


def format_published_date(date_string):
    """
    Format the date string into a datetime object
    """
    if not date_string or date_string is None:
        return None

    try:
        """
        [
                2025,
                1,
                29,
                11,
                0,
                0,
                2,
                29,
                0
            ]
        """
        if isinstance(date_string, tuple):
            return datetime(*date_string[:6])

        # "Wed, 29 Jan 2025 11:00:00 +0000"
        elif isinstance(date_string, str):
            return datetime.strptime(date_string, "%Y-%m-%d")

        # return datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %Z")
    except Exception as e:
        print(f"Error formatting date: {e}")
        return None


def serialize_datetime(obj):
    """
    Serialize datetime object into string
    """
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d")
    raise TypeError("Type not serializable")
