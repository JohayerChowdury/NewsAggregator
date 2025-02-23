from sentence_transformers import SentenceTransformer
import openai

from .openai_client import client

model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embeddings(texts):
    return model.encode(texts)


def get_openai_embeddings(texts, use_openai=False):
    try:
        """Batch generate embeddings with error handling"""
        if use_openai:
            response = client.embeddings.create(
                input=texts, model="text-embedding-3-small"
            )
            return [item.embedding for item in response.data]
        else:
            embeddings = model.encode(texts)
            return embeddings
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


def get_embeddings_from_chunked_text(text, chunk_size=256, overlap=50):
    """Split text into overlapping chunks to maintain context"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
    embeddings = model.encode(chunks)
    return embeddings
