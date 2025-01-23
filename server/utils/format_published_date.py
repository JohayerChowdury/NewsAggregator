from datetime import datetime


def format_published_date(date_string):
    """
    Format the date string into a datetime object
    """
    if not date_string or date_string is None:
        return None

    try:
        if isinstance(date_string, tuple):
            return datetime(*date_string[:6])
        # return datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %Z")
    except Exception as e:
        print(f"Error formatting date: {e}")
        return None
