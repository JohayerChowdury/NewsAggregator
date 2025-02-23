import os
import swifter

from .embedding_model import get_embeddings_from_chunked_text
from .openai_client import client
from .faiss_vector_store import load_faiss_index, write_faiss_index

from .scraper import required_columns

# source: https://www.perplexity.ai/search/we-want-to-track-all-news-rela-fkvIqwT2Tum_rBEBC8b4zg#8

gpt_model = os.environ.get("GPT_MODEL")

"""Analyze themes using sentence embeddings and Faiss K-means clustering"""


def analyze_themes(df, num_themes=5):
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")
    # TODO: finish


def generate_theme_label(cluster_texts):
    prompt = f"'''{' '.join(cluster_texts[:3])}''' Question: What is the connecting theme among these articles in 5 words or less?"
    try:
        response = client.chat.completions.create(
            stream=False,
            model=gpt_model,
            messages=[
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "text",
                            "text": """ 
                                You are an AI expert journalist in the housing and finance sector, especially in Canada. 
                                You strictly answer questions without unnecessary introductions or conclusions.
                                You are provided with a document that represent several news articles, delimited by triple quotes and a question. 
                                Your task is to answer the question using only the provided document.
                                """,
                        }
                    ],
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=10,
        )
        response_text = response.choices[0].message.content
        # response_text = response.message.content
        print(f"Generated theme label: {response_text}")
        return response_text
    except Exception as e:
        print(f"Error generating theme label:")
        print(e)
        return "Unlabeled Theme"


def label_themes(df):
    try:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise KeyError(f"Missing required columns: {missing}")

        theme_labels = {}
        for cluster_id in df["theme"].unique():
            cluster_texts = df[df["theme"] == cluster_id]["content"].tolist()
            theme_labels[cluster_id] = generate_theme_label(cluster_texts)
        df["theme_name"] = df["theme"].map(theme_labels)
    except Exception as e:
        print("Error labeling themes:")
        print(e)
        df["theme_name"] = "Unlabeled Theme"

    return df


def generate_summary(theme_name, articles):
    prompt = f" '''{' '.join(articles[:3])}''' Question: What is the summary of these articles with the following theme {theme_name}? Answer in 100 words or less."
    try:
        response = client.chat.completions.create(
            stream=False,
            model=gpt_model,
            messages=[
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "text",
                            "text": """
                                You are an AI expert journalist in the housing and finance sector, especially in Canada. 
                                You strictly answer questions without unnecessary introductions or conclusions.
                                You are provided with several documents that represent several news articles, delimited by triple quotes and a question. 
                                Your task is to answer the question using only the provided document.
                                """,
                        }
                    ],
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content
        # return response.message.content
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return "Summary unavailable due to an error."


def generate_jot_notes(df):
    """Create structured summaries with proper field access"""
    summaries = []
    for theme_name, group in df.groupby("theme_name"):
        articles_list = []
        for _, row in group.iterrows():
            # Access fields correctly from the DataFrame structure
            title = row["entry"].get("title", "No Title")  # Get title from entry object
            date = row["date_published"].strftime(
                "%Y-%m-%d"
            )  # Use date_published column
            link = row["entry"].get("link", "#")  # Get link from entry object

            articles_list.append(f"- **{title}** ({date}): [Read more]({link})")

        summaries.append(
            {
                "theme": theme_name,
                "articles": articles_list,
                "summary": generate_summary(theme_name, group["content"].tolist()),
            }
        )

    return sorted(summaries, key=lambda x: len(x["articles"]), reverse=True)
