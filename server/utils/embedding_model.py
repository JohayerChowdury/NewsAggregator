# from functools import cache
import numpy as np
from sentence_transformers import SentenceTransformer
import openai

from .openai_client import openai_client

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_embedding_model_instance = None

model = SentenceTransformer(EMBEDDING_MODEL)

# @cache
# def _embedding_model():
#     global _embedding_model_instance
#     if _embedding_model_instance is None:
#         model = SentenceTransformer(EMBEDDING_MODEL)
#         _embedding_model_instance = model
#         vector_dim = _embedding_model_instance.get_sentence_embedding_dimension()
#         print(
#             f"Loaded SentenceTransformer model: {EMBEDDING_MODEL} with {vector_dim} dimensions"
#         )
#     return _embedding_model_instance


def get_model_embeddings(text_corpus):
    return model.encode(text_corpus)


def get_embeddings_from_chunked_text(text, chunk_size=256, overlap=50, openai=False):
    """Split text into overlapping chunks to maintain context"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
    if openai:
        embeddings = get_openai_embeddings(chunks)
    else:
        embeddings = get_model_embeddings(chunks)
    if len(embeddings) == 0:  # Properly check if embeddings list is empty
        return [0.0] * 384  # Return zero vector

    return np.mean(np.array(embeddings), axis=0).tolist()  # Convert to single vector


def get_openai_embeddings(texts):
    try:
        """Batch generate embeddings with error handling"""
        response = openai_client.embeddings.create(
            input=texts, model="text-embedding-3-small"
        )
        return [item.embedding for item in response.data]

    except openai.APIError as e:
        # Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error:")
        print(e)
        pass
    except openai.APIConnectionError as e:
        # Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        pass
    except Exception as e:
        print(f"Error generating embeddings:")
        print(e)
        return None
