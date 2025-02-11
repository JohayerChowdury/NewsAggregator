# import re


# # Expand clean_text() to handle more edge cases
# def clean_text(text):
#     """Clean and normalize text"""
#     text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
#     text = re.sub(r"http\S+", "", text)  # Remove URLs
#     text = re.sub(r"\s+", " ", text).strip()  # Normalize whitespace

#     # Remove HTML/XML tags and URLs
#     text = re.sub(r"<[^>]+>|https?:\/\/\S+", "", text)

#     # Normalize whitespace and fix encoding
#     text = " ".join(text.split()).strip()
#     return text.encode("ascii", "ignore").decode("ascii")

import re
from bs4 import BeautifulSoup


def remove_social_media_urls(text):
    social_media_domains = [
        r"twitter\.com",
        r"facebook\.com",
        r"instagram\.com",
        r"linkedin\.com",
        r"tiktok\.com",
        r"youtube\.com",
        r"github\.com",
        r"medium\.com",
        r"reddit\.com",
    ]
    pattern = rf'\bhttps?://(?:www\.)?(?:{"|".join(social_media_domains)})/[^\s]+'

    cleaned_text = re.sub(pattern, "", text)
    return cleaned_text.strip()


def clean_text(text):
    """Clean and normalize text from HTML content"""

    # Parse HTML and extract text
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")  # Preserve some spacing between elements

    # Remove excessive whitespace and normalize encoding
    text = re.sub(r"\s+", " ", text).strip()
    text = text.encode("ascii", "ignore").decode("ascii")  # Remove non-ASCII characters

    # Replace escaped Unicode whitespace characters
    text = text.replace("\\xa0", "\n\n")  # Preserve paragraph breaks

    # Manual cleaning steps
    text = remove_social_media_urls(text)

    return text
