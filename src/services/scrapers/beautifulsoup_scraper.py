from requests_cache import CachedSession
from bs4 import BeautifulSoup

# Custom headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
session = CachedSession(cache_name="cache", backend="sqlite", expire_after=3000)


def fetch_article_soup(url):
    #     """Fetch and extract article text from a given URL."""
    try:
        response = session.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")

    try:
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching article content of {url}")
        print(e)
        return None


def extract_clean_article(
    article_link,
    excluded_classes=["ad", "sponsored", "promo", "sidebar", "footer"],
    excluded_keywords=["advertisement", "subscribe", "click here"],
    max_depth=3,
):
    soup = fetch_article_soup(article_link)
    if not soup:
        return ""
    p_tags = soup.find_all("p")

    clean_paragraphs = []

    for p in p_tags:
        parent = p
        depth = 0
        exclude = False

        # Traverse up to max_depth levels
        while parent and depth < max_depth:
            parent = parent.find_parent("div")
            if parent:
                # Check class-based exclusion
                if any(cls in parent.get("class", []) for cls in excluded_classes):
                    exclude = True
                    break

                # Check keyword-based exclusion
                if any(
                    keyword in parent.get_text(strip=True).lower()
                    for keyword in excluded_keywords
                ):
                    exclude = True
                    break

            depth += 1

        if not exclude:
            clean_paragraphs.append(p.get_text(strip=True))

    return str("\n".join(clean_paragraphs))
