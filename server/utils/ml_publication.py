import os
import numpy as np
import faiss
import json

from .embedding_model import get_embeddings_from_chunked_text
from .openai_client import client
from .faiss_vector_store import create_faiss_index
from .scraper import check_for_required_columns

"""Analyze themes using sentence embeddings and Faiss K-means clustering"""

# source: https://www.perplexity.ai/search/we-want-to-track-all-news-rela-fkvIqwT2Tum_rBEBC8b4zg#8

gpt_model = os.environ.get("GPT_MODEL")


def prepare_embeddings_array(df, column="extracted_content", embedding_dim=384):
    """
    Generates embeddings for a dataframe column and returns a properly shaped NumPy array.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the text to be embedded.
    - column (str): The column name containing text to be embedded.
    - embedding_dim (int): The expected dimension of each embedding.

    Returns:
    - np.ndarray: A 2D array of shape (N, embedding_dim) suitable for FAISS indexing.
    """

    try:
        # Generate embeddings (ensure function `get_embeddings_from_chunked_text` exists)
        df["vectors"] = df[column].swifter.apply(get_embeddings_from_chunked_text)

        # Handle missing, empty, or malformed embeddings
        df = df.dropna(subset=["vectors"])

        # Convert to a NumPy array
        embeddings_array = np.array(df["vectors"].tolist(), dtype=np.float32)

        # Check shape to confirm it's valid for FAISS
        if embeddings_array.shape[1] != embedding_dim:
            raise ValueError(
                f"Embedding dimension mismatch. Expected {embedding_dim}, got {embeddings_array.shape[1]}."
            )

        return df, embeddings_array

    except Exception as e:
        print(f"Error preparing embeddings: {e}")
        return None


def analyze_themes(df, num_themes=5):

    df, embeddings_array = prepare_embeddings_array(df)
    index = create_faiss_index(embeddings_array)
    ncentroids = min(num_themes, len(df) // 2) if len(df) > 20 else 2

    try:
        kmeans = faiss.Kmeans(384, ncentroids, niter=100, verbose=False)
        kmeans.train(embeddings_array)
        _, I = kmeans.index.search(embeddings_array, 1)

        df["theme_cluster"] = I.flatten()
    except Exception as e:
        print(f"Error clustering themes: {str(e)}")
        raise e

    return df, index


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
        theme_labels = {}
        for cluster_id in df["theme_cluster"].unique():
            cluster_texts = df[df["theme_cluster"] == cluster_id][
                "extracted_content"
            ].tolist()
            theme_labels[cluster_id] = generate_theme_label(cluster_texts)
        df["theme_name"] = df["theme_cluster"].map(theme_labels)
    except Exception as e:
        print("Error labeling themes:")
        print(e)
        df["theme_name"] = "Unlabeled Theme"

    return df


def generate_summary(theme_name, articles):
    prompt = f" '''{' '.join(articles[:5])}''' Question: Summarize the main insights from these articles with the following theme {theme_name}? Answer in 100 words or less."
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
    results = []
    check_for_required_columns(df, ["theme_cluster", "theme_name", "extracted_content"])
    try:
        unique_themes = df["theme_cluster"].unique()
        for theme_id in unique_themes:
            theme_name = df[df["theme_cluster"] == theme_id]["theme_name"].iloc[0]
            articles = df[df["theme_cluster"] == theme_id]["extracted_content"].tolist()
            summary = generate_summary(theme_name, articles)
            results.append(
                {"summary": summary, "theme_name": theme_name, "theme_id": theme_id}
            )

    except Exception as e:
        print("Error generating jot notes:")
        print(e)

    # json_string = json.dumps(results)
    # with open("newsletter.json", "w") as f:
    #     json.dump(results, f)
    return results
