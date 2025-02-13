#  source: https://medium.com/@srelan1/building-a-personalized-news-aggregator-using-llama3-langchain-and-ollama-139617cf3891

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
import ollama
from openai import OpenAI

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from datetime import date
import json
import os
import numpy as np

import faiss


# # Load documents from a JSON file
# def load_documents(file_path):
#     """
#     Loads documents from a JSON file using a predefined schema.

#     Parameters:
#     file_path (str): The path to the JSON file containing the documents.

#     Returns:
#     list: A list of documents loaded from the file.
#     """
#     loader = JSONLoader(
#         file_path=file_path,
#         jq_schema=".[] | { description: .description, url: .url}",
#         text_content=False,
#     )
#     return loader.load()


# # Split documents into manageable chunks
# def split_documents(documents):
#     """
#     Splits documents into smaller chunks to manage processing load.

#     Parameters:
#     documents (list): A list of documents to be split.

#     Returns:
#     list: A list of split document chunks.
#     """
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#     return text_splitter.split_documents(documents)


# def create_vector_store(documents):
#     """
#     Creates a vector store from document embeddings.

#     Parameters:
#     documents (list): A list of documents or text chunks.

#     Returns:
#     VectorStore: A vector store containing the documents' embeddings.
#     """
#     embedding_model = OllamaEmbeddings(model="llama3")
#     vector_store = Chroma.from_documents(documents=documents, embedding=embedding_model)
#     return vector_store.as_retriever()


# def generate_news_update():
# documents = load_documents("articles.json")
# document_splits = split_documents(documents)
# retriever = create_vector_store(document_splits)

# # TODO: remove topic and add theme analysis
# topic = "Canadian Financial News Related to Housing"
# question = f"""
#     Welcome to your curated news update, bringing you the latest and most relevant headlines directly to your inbox.

#     ## Today's Top Story
#     ### [Title of the Main News Article](URL_to_article)
#     Provide a brief introduction to the top story of the day, emphasizing the main points succinctly.

#     ---

#     ## More News

#     ### [Second News Article Title](URL_to_second_article)
#     **Summary**: Offer a concise summary of the second most important news of the day.

#     ### [Third News Article Title](URL_to_third_article)
#     **Summary**: Summarize this article, highlighting key details that inform the reader effectively.

#     ### [Fourth News Article Title](URL_to_fourth_article)
#     **Summary**: Briefly cover the fourth article, focusing on crucial points.

#     ### [Fifth News Article Title](URL_to_fifth_article)
#     **Summary**: Sum up the fifth article, ensuring to pinpoint essential information.

#     ---

#     **Instructions**:
#     - Write a news summary for the topic: '{topic}'.
#     - Ensure the news summaries do not repeat information.
#     - Follow the structure provided above as a template for the news summary.
#     """
# formatted_context = "\n\n".join(doc.page_content for doc in retriever.invoke(topic))
# formatted_prompt = f"Question: {question}\n\nContext: {formatted_context}"
# llm_response = ollama.chat(
#     model="llama3",
#     messages=[
#         {
#             "role": "system",
#             "content": "You are an AI bot that helps display curated news based on articles provided. Please answer the user's question, following the instructions with the provided context.",
#         },
#         {"role": "user", "content": formatted_prompt},
#     ],
# )
# return llm_response["message"]["content"]
# source: https://www.perplexity.ai/search/we-want-to-track-all-news-rela-fkvIqwT2Tum_rBEBC8b4zg#8

open_ai_api_key = os.environ.get("OPENAI_API_KEY")
llm_endpoint = os.environ.get("LLM_ENDPOINT")
open_ai_organization = os.environ.get("OPENAI_ORGANIZATION_ID")
open_ai_project = os.environ.get("OPENAI_PROJECT_ID")
gpt_model = os.environ.get("GPT_MODEL")
print(open_ai_api_key, llm_endpoint, open_ai_organization, open_ai_project, gpt_model)

client = OpenAI(
    api_key=open_ai_api_key,
    base_url=llm_endpoint,
    organization=open_ai_organization,
    project=open_ai_project,
)


from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings(texts, use_openai=False):
    """Batch generate embeddings with error handling"""
    if use_openai:
        response = client.embeddings.create(input=texts, model="text-embedding-3-small")
        return [item.embedding for item in response.data]
    else:
        embeddings = model.encode(texts)
        return embeddings


"""Analyze themes using sentence embeddings and Faiss K-means clustering"""


def analyze_themes(df, num_themes=10):
    index = create_faiss_index(df)
    ncentroids = min(num_themes, len(df) // 2) if len(df) > 20 else 2

    kmeans = faiss.Kmeans(index.d, ncentroids, niter=100, verbose=False)
    kmeans.train(index.reconstruct_n(0, index.ntotal))

    _, I = kmeans.index.search(index.reconstruct_n(0, index.ntotal), 1)
    df["theme"] = I.flatten()

    return df, kmeans


def generate_theme_label(cluster_texts):
    prompt = f"Generate a concise theme name (maximum 5 words) for these articles: {' '.join(cluster_texts[:3])}"
    try:
        # response = client.chat.completions.create(
        #     model=gpt_model,
        #     messages=[{"role": "user", "content": prompt}],
        # )
        response = ollama.chat(
            model=gpt_model,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.message.content
        print(f"Generated theme label: {response_text}")
        return response_text
        # return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating theme label:")
        print(e)
        return "Unlabeled Theme"


def label_themes(df):
    """Label themes using GPT-3.5"""
    try:
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
    """Generate a summary for a theme using GPT-3.5"""
    prompt = f"Summarize these articles about {theme_name} in 2-3 sentences, focusing on housing and finance aspects: {' '.join(articles[:3])}"
    try:
        # response = client.chat.completions.create(
        response = ollama.chat(
            model=gpt_model,
            messages=[
                # {"role": "system", "content": ""},
                {"role": "user", "content": prompt},
            ],
        )
        return response.message.content
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


def create_faiss_index(df):
    if "embedding" not in df.columns:
        df["embedding"] = df["content"].apply(
            lambda x: model.encode(x, show_progress_bar=True)
        )

    embeddings = np.array([e for e in df["embedding"]]).astype("float32")
    d = embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)
    return index
