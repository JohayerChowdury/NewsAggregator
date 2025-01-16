import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup

from flask import Flask, render_template, request

app = Flask(__name__)

RSS_FEEDS = {
    'Yahoo Finance': 'https://finance.yahoo.com/news/rssindex',
    'Hacker News': 'https://news.ycombinator.com/rss',
    'Wall Street Journal': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
    'CNBC': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069'
}

@app.route('/')
def index():
    articles = []
    for source, feed in RSS_FEEDS.items():
        parsed_feed = feedparser.parse(feed)
        entries = [(source, entry) for entry in parsed_feed.entries]
        articles.extend(entries)

    articles = sorted(articles, key=lambda x: x[1].published_parsed, reverse=True)

    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_articles = len(articles)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_articles = articles[start:end]
    return render_template('index.html', articles=paginated_articles, page=page, total_pages = total_articles // per_page + 1)

@app.route("/search")
def search():
    query = request.args.get('query')

    articles = []
    for source, feed in RSS_FEEDS.items():
        parsed_feed = feedparser.parse(feed)
        entries = [(source, entry) for entry in parsed_feed.entries if query.lower() in entry.title.lower()]
        articles.extend(entries)
    
    results = [article for article in articles if query.lower() in article[1].title.lower()]


    return render_template('search_results.html', articles=results, query=query)

# # Set up Selenium WebDriver
# chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode
# driver = webdriver.Chrome(options=chrome_options)



# # Function to scrape news
# def scrape_news():
#     url = "https://news.google.com/topstories?hl=en-GB&gl=GB&ceid=GB:en" # Replace with the actual URL
#     driver.get(url)
   
#     # use session to get the page
#     session = HTMLSession()
#     r = session.get(url)

#     time.sleep(3)  # Wait for the page to load

#     # Parse the page content with BeautifulSoup
#     soup = BeautifulSoup(driver.page_source, 'html.parser')
#     articles = soup.find_all('article')  # Adjust the tag and class as needed

#     news_list = []
#     for article in articles:
#         title = article.find('h2').text  # Adjust the tag and class as needed
#         link = article.find('a')['href']  # Adjust the tag and class as needed
#         summary = article.find('p').text  # Adjust the tag and class as needed
#         news_list.append({'title': title, 'link': link, 'summary': summary})

#     return news_list

# # Example usage
# if __name__ == "__main__":
#     news = scrape_news()
#     for item in news:
#         print(f"Title: {item['title']}")
#         print(f"Link: {item['link']}")
#         print(f"Summary: {item['summary']}")
#         print("-" * 80)

#     driver.quit()

if __name__ == '__main__':
    app.run(port=5000, debug=True)