import re
from bs4 import BeautifulSoup


def remove_accented_chars(text):
    text = text.encode("ascii", "ignore").decode("ascii")  # Remove non-ASCII characters
    return text


def normalize_html_content(raw_html):
    """Clean and normalize text from HTML content"""

    # Parse HTML and extract text
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ")  # Preserve some spacing between elements
    print("Text before cleaning:", text)

    # Remove excessive whitespace and normalize encoding
    text = re.sub(r"\s+", " ", text).strip()
    text = remove_accented_chars(text)
    # Replace escaped Unicode whitespace characters
    text = text.replace("\\xa0", "\n\n")  # Preserve paragraph breaks

    print("Text after cleaning:", text)
    return text


def remove_websites_and_social_media_mentions(text):
    # List of common social media & general website labels
    platform_keywords = [
        "Website",
        "Facebook",
        "LinkedIn",
        "Twitter",
        "YouTube",
        "Instagram",
        "TikTok",
        "Github",
        "Medium",
        "Reddit",
    ]

    # Regex pattern to match: "Platform: URL" OR "Platform:" (with no URL)
    platform_pattern = rf'\b(?:{"|".join(platform_keywords)})\s*:\s*(https?://\S+)?'

    # General URL pattern (removes all links)
    url_pattern = r"https?://\S+"

    # Remove social media mentions
    text = re.sub(platform_pattern, "", text)

    # Remove any remaining URLs
    text = re.sub(url_pattern, "", text)

    # Clean up extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


# # Expand clean_text() to handle more edge cases
def clean_text(text):
    """Clean and normalize text"""
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    text = re.sub(r"http\S+", "", text)  # Remove URLs
    text = re.sub(r"\s+", " ", text).strip()  # Normalize whitespace

    # Remove HTML/XML tags and URLs
    text = remove_websites_and_social_media_mentions(text)

    # Remove dates in this format Jan 22, 2025
    text = re.sub(
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}",
        "",
        text,
    )

    # Normalize whitespace and fix encoding
    text = " ".join(text.split()).strip()

    # Remove common texts that are not relevant
    text = re.sub(r"Written by *$", "", text)
    text = text.replace("Click here for more information.", "")
    text = text.replace("Having trouble logging in", "")
    text = text.replace("Click here to unsubscribe", "")
    text = text.replace("Click here to view in browser", "")
    text = text.replace("Click here to read more", "")
    text = re.sub(r"Read more$", "", text)

    return text.encode("ascii", "ignore").decode("ascii")
