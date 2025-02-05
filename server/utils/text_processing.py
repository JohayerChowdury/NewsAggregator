import re


def clean_text(text):
    """Clean and normalize text"""
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    text = re.sub(r"http\S+", "", text)  # Remove URLs
    text = re.sub(r"\s+", " ", text).strip()  # Normalize whitespace
    return text


# # Expand clean_text() to handle more edge cases
# def clean_text(text):
#     if not text:
#         return "No summary available"

#     # Remove HTML/XML tags and URLs
#     text = re.sub(r"<[^>]+>|https?:\/\/\S+", "", text)

#     # Normalize whitespace and fix encoding
#     text = " ".join(text.split()).strip()
#     return text.encode("ascii", "ignore").decode("ascii")
