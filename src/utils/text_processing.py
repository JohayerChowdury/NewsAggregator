import re
from bs4 import BeautifulSoup


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


def filter_text_for_llm(text):
    """Filter text to remove unneeded content for LLM/AI generation."""
    # Remove social media mentions and URLs
    text = remove_websites_and_social_media_mentions(text)

    # Remove common texts that are not relevant
    phrases_to_remove = [
        r"You can save this article by registering for freehere\.",
        r"Reviews and recommendations are unbiased and products are independently selected\.",
        r"Postmedia may earn an affiliate commission from purchases made through links on this page\.",
        r"Postmedia is committed to maintaining a lively but civil forum for discussion.",
        r"Written by.*?(?=\s)",  # removes 'Written by' and subsequent content until a space
        r"Last modified:.*?(?=\s)",
        r"Please keep comments relevant and respectful\.",
        r"This website uses cookies.*?(?=By continuing)",  # example pattern
        r"Having trouble logging in\?",
        r"Click here for more information\.",
        r"Click here to unsubscribe\.",
        r"Click here to view in browser\.",
        r"Click here to read more\.",
        r"Read more$",
        r"Comments may take up to an hour to appear on the site\.",
        r"You will receive an email if there is a reply to your comment, an update to a thread you follow or if a user you follow comments\.",
        r"For more information *?click here\.",
        r"By continuing to use our site, you agree to our Terms of Use and Privacy Policy.",
        r"Visit our Community Guidelines",
        # Add more patterns as needed
    ]

    # Remove each unwanted phrase/pattern from the text
    for pattern in phrases_to_remove:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Final cleanup: remove any extra spaces that may have resulted
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_and_normalize_text(text):
    """Clean and normalize text for human-readable display."""
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    text = re.sub(r"http\S+", "", text)  # Remove URLs
    text = re.sub(r"\s+", " ", text).strip()  # Normalize whitespace

    # Replace non-breaking spaces (&nbsp;) with regular spaces
    text = text.replace("&nbsp;", " ")

    # # Normalize whitespace and fix encoding
    # text = " ".join(text.split()).strip()

    return text


def normalize_html_content(raw_html):
    # Parse HTML and extract text
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ")  # Preserve some spacing between elements

    # Clean and normalize text for human-readable display
    text = clean_and_normalize_text(text)

    text = filter_text_for_llm(text)

    return text


from googlenewsdecoder import gnewsdecoder


def decode_gnews_url(url, interval=None, proxy=True):
    try:
        decoded = None
        if proxy:
            proxyString = "http://15.235.53.20:28003"  # Use different proxy if needed
            decoded = gnewsdecoder(source_url=url, interval=interval, proxy=proxyString)
        else:
            decoded = gnewsdecoder(source_url=url, interval=interval)
        if decoded.get("status"):
            return decoded["decoded_url"]
    except Exception as e:
        print(f"Error decoding URL {url}: {e}")
    return url
