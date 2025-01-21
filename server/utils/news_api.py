from dotenv import load_dotenv
import os

from newsapi import NewsApiClient

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variable
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if NEWS_API_KEY is None:
    NEWS_API_KEY = ""

# Initialize the NewsApiClient with the API key
newsapi = NewsApiClient(api_key=NEWS_API_KEY)


def search_news_articles(keywords=[""]):
    # Define the query parameters
    query = " OR ".join(keywords)

    # Fetch the news articles
    response = newsapi.get_everything(
        q="canadian AND accessory AND dwelling AND unit",
        language="en",
        sort_by="relevancy",
    )
    print(response)

    # Check if the request was successful
    if response["status"] == "ok":
        return response["articles"]
    else:
        raise Exception(f"Error fetching news articles: {response['message']}")


if __name__ == "__main__":
    keywords = [
        "canadian accessory dwelling unit",
        "canadian financing",
        "canadian housing",
    ]

    try:
        articles = search_news_articles(keywords)
        for article in articles:
            print(f"Title: {article['title']}")
            print(f"Description: {article['description']}")
            print(f"URL: {article['url']}\n")
    except Exception as e:
        print(e)
