import feedparser

from flask import Flask, render_template, request

from datetime import datetime

app = Flask(__name__)

# Add the appropriate RSS feeds
RSS_FEEDS = {
    # 'Yahoo Finance': 'https://finance.yahoo.com/news/rssindex', # works
    # 'Hacker News': 'https://news.ycombinator.com/rss', # works
    # 'Wall Street Journal': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', # works
    # "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",  # works
    # "Canadian Mortgage Trends": "https://www.canadianmortgagetrends.com/feed/",
    "Google News: Canadian Accessory Dwelling Unit": "https://news.google.com/rss/search?q=canadian%20accessory%20dwelling%20unit&hl=en-CA&gl=CA&ceid=CA%3Aen",
}


def format_published_date(published):
    if published:
        if isinstance(published, str):
            try:
                published = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                try:
                    published = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
                except ValueError:
                    return None
        elif isinstance(published, tuple):
            published = datetime(*published[:6])
        return published.strftime("%Y-%m-%d %H:%M:%S")
    return None


def parse_feed(feed_url):
    parsed_feed = feedparser.parse(feed_url)
    articles = []
    for entry in parsed_feed.entries:
        published = entry.get("published_parsed") or entry.get("published")
        published = format_published_date(published)
        articles.append((entry, published))
    return articles


@app.route("/")
def index():
    articles = []
    for source, feed in RSS_FEEDS.items():
        parsed_articles = parse_feed(feed)
        articles.extend(
            [(source, entry, published) for entry, published in parsed_articles]
        )

    articles = sorted(articles, key=lambda x: x[2], reverse=True)

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
            (source, entry, published)
            for entry, published in parsed_articles
            if query.lower() in entry.title.lower()
        ]
        articles.extend(filtered_articles)

    return render_template("search_results.html", articles=articles, query=query)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
