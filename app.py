import requests
import feedparser
import ssl
from bs4 import BeautifulSoup as bs4
import urllib.parse
from flask import Flask, render_template, request

from utils import format_published_date, summarize_article

app = Flask(__name__)

# Add the appropriate RSS feeds
RSS_FEEDS = {
    # "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",  # works
    # 'Wall Street Journal': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', # works
    # "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",  # works
    # "Canadian Mortgage Trends": "https://www.canadianmortgagetrends.com/feed/",  # works
    # "Google News: Canadian Accessory Dwelling Unit": "https://news.google.com/rss/search?q=canadian%20accessory%20dwelling%20unit&hl=en-CA&gl=CA&ceid=CA%3Aen",  # works
    # "Government of Ontario: All News": "https://news.ontario.ca/newsroom/en/rss/allnews.rss",  # works
    # "Government of Canada: Finance": "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentfinance&type=newsreleases&sort=publishedDate&orderBy=desc&publishedDate%3E=2020-08-09&pick=100&format=atom&atomtitle=Canada%20News%20Centre%20-%20Department%20of%20Finance%20Canada%20-%20News%20Releases" # doesnt work,
    # "CBC News": "https://rss.cbc.ca/lineup/topstories.xml" # unsure
}

WEBSITES = {
    "Accessorry Dwelling Finance News": "https://accessorydwellings.org/category/news/financing-news/",
}


def is_rss_feed(feed_url):
    try:
        response = requests.head(feed_url, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "").lower()
            if "rss" in content_type or "xml" in content_type:
                return True
    except requests.RequestException as e:
        print(f"Error checking feed URL {feed_url}: {e}")
    return False


def resolve_url(base_url, href):
    return urllib.parse.urljoin(base_url, href)


# Find RSS Links on Page
def find_rss_links(url):

    if not url.startswith("http"):
        url = "https://" + url

    try:
        raw = requests.get(url).text
        html = bs4(raw, "html.parser")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

    # Extract RSS feed links from <link> tags with rel="alternate"
    feed_urls = html.findAll("link", rel="alternate")
    result = set()

    for f in feed_urls:
        feed_type = f.get("type")
        if feed_type and ("rss" in feed_type or "xml" in feed_type):
            href = f.get("href")
            if href:
                result.add(resolve_url(url, href))

    # Extract RSS feed links from <a> tags
    base_url = (
        urllib.parse.urlparse(url).scheme + "://" + urllib.parse.urlparse(url).hostname
    )
    atags = html.findAll("a")

    for a in atags:
        href = a.get("href")
        if href and any(keyword in href for keyword in ["xml", "rss", "feed", "atom"]):
            if is_rss_feed(href):
                result.add(resolve_url(url, href))

    # Check common RSS feed routes if no feed links were found
    if not result:
        routes = [
            "atom.xml",
            "feed.xml",
            "rss.xml",
            "index.xml",
            "atom.json",
            "feed.json",
            "rss.json",
            "index.json",
            "feed/",
            "rss/",
            "feed/index.xml",
            "rss/index.xml",
            "feed/index.json",
            "rss/index.json",
            "feed/atom",
            "rss/atom",
            "feed/rss",
            "rss/rss",
            "feed/atom.xml",
            "rss/atom.xml",
            "feed/rss.xml",
            "rss/rss.xml",
            "feed/atom.json",
            "rss/atom.json",
            "feed/rss.json",
            "rss/rss.json",
        ]
        for route in routes:
            try:
                href = base_url + "/" + route
                if is_rss_feed(href):
                    result.add(href)
            except Exception as e:
                print(f"Error parsing {href}: {e}")
                continue

    # Parse the URLs in the result set
    for feed_url in list(result):
        f = feedparser.parse(feed_url)
        if f.entries:
            result.add(feed_url)

    return list(result)


def parse_feed(feed_url):
    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context
    parsed_feed = feedparser.parse(feed_url)
    articles = []
    if parsed_feed.bozo:
        print(f"Error parsing feed {feed_url}: {parsed_feed.bozo_exception}")
    else:
        for entry in parsed_feed.entries:
            date_published = format_published_date(
                entry.get("published_parsed") or entry.get("published")
            )
            articles.append((entry, date_published))
    print(f"Total number of articles from source  {feed_url}: {len(articles)}")
    return articles


@app.route("/")
def index():
    articles = []

    # for source, feed in RSS_FEEDS.items():
    #     print(f"Fetching {source} feed from {feed}")
    #     parsed_articles = parse_feed(feed)
    #     articles.extend(
    #         [
    #             (source, entry, date_published)
    #             for entry, date_published in parsed_articles
    #             if entry is not None
    #         ]
    #     )

    for source, feed in WEBSITES.items():
        print(f"Fetching {source} feed from {feed}")
        parsed_articles = find_rss_links(feed)
        articles.extend(
            [(source, entry) for entry in parsed_articles if entry is not None]
        )

    # articles = sorted(articles, key=lambda x: x[2], reverse=True) or []

    page = request.args.get("page", 1, type=int)
    per_page = 10
    total_articles = len(articles)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_articles = articles[start:end]
    return render_template(
        "index.html",
        articles=paginated_articles,
        page=page,
        total_pages=total_articles // per_page + 1,
    )


@app.route("/search")
def search():
    query = request.args.get("query")

    articles = []
    for source, feed in RSS_FEEDS.items():
        parsed_articles = parse_feed(feed)
        filtered_articles = [
            (source, entry)
            for entry in parsed_articles
            if query.lower() in entry.title.lower()
        ]
        articles.extend(filtered_articles)

    return render_template("search_results.html", articles=articles, query=query)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
