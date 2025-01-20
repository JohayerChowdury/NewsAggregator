from dotenv import load_dotenv
import os

from openai import OpenAI

# Load the environment variables
load_dotenv()

# Set the API key
api_key = os.getenv("OPENAI_API_KEY")

# Create an instance of the OpenAI class
client = OpenAI(api_key=api_key)


def summarize_article(article_text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes articles.",
            },
            {
                "role": "user",
                "content": f"Summarize the following article: {article_text}",
            },
        ],
        max_tokens=150,
    )
    return response.choices[0].message["content"]
