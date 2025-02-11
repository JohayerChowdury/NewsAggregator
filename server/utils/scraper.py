import feedparser

import requests
from bs4 import BeautifulSoup as bs4
import urllib.parse


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

    # TODO: unsure if needed
    # Parse the URLs in the result set
    for feed_url in list(result):
        f = feedparser.parse(feed_url)
        if f.entries:
            result.add(feed_url)

    return list(result)


# feedretriever.py: https://github.com/fvargaspiedra/RSSummarizer
import re
import datetime


# Read, download, and store a list of RSS feed URLs
def read_rss_file(rss_file_location, output_directory):
    # Read file with list of RSS feeds URLs
    rss_file = open(rss_file_location, "r")

    # Prepare suffix with date to save files
    now = datetime.datetime.now()
    suffix = now.strftime("_%Y%m%d%H%M%S.xml")

    # Iterate over all the RSS Feed URLs
    for rss in rss_file:
        rss = rss.strip()

        # Simple verification for malformed lines
        if len(rss) <= 1:
            continue

        # Filename will include parts of the URL plus the date suffix
        filename = re.compile("http://|https://").split(rss)[1]
        last_dot_index = filename.rfind(".")
        filename = filename[:last_dot_index]
        filename = re.sub("\.|\/", "_", filename)
        filename = filename + suffix

        # Download XML file from RSS feed URL and save it
        download_rss(rss, filename, output_directory)


# Download, and store a list of RSS feed URLs
def download_rss(url, filename, output_directory):
    print("Downloading content from " + url)
    print("Creating local file " + output_directory + filename)

    # Fetch XML from RSS feed URL and save it
    response = requests.get(url)

    # Use right encoding to avoid issues
    response.encoding = "utf-8-sig"

    # Only write output if response is a 200
    if response.status_code is 200:
        with open(output_directory + filename, "w") as f:
            f.write(response.text)
