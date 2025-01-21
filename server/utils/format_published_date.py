from datetime import datetime


def format_published_date(date_string):
    if not date_string:
        return None
    try:
        if isinstance(date_string, str):
            date_string = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
        elif isinstance(date_string, tuple):
            date_string = datetime(*date_string[:6])
        return date_string.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Error formatting date: {e}")
        return date_string
