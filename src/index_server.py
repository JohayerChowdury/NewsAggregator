# import os

# from llama_index.core.storage import StorageContext
# from llama_index.vector_stores.supabase import SupabaseVectorStore
# from llama_index.indices.vector_store import VectorStoreIndex
# from llama_index.llms import OpenAI, Ollama  # llm
# from llama_index.embeddings import OpenAIEmbedding, OllamaEmbedding  # embedding model


# DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DATABASE_URL")

# vector_store = SupabaseVectorStore(
#     postgres_connection_string=DATABASE_URL,
#     collection_name="news_items",
# )

# storage_context = StorageContext.from_defaults(vector_store=vector_store)
# index = VectorStoreIndex.from_documents([], storage_context=storage_context)

# use_openai = False

# embed_model = (
#     OpenAIEmbedding(model="text-embedding-3-large")
#     if use_openai
#     else OllamaEmbedding(model_name="nomic-embed-text:latest")
# )
# llm = (
#     OpenAI(model="gpt-3.5-turbo", temperature=0)
#     if use_openai
#     else Ollama(model="llama3.2:latest", request_timeout=120.0)
# )


# def query_index(query_text, use_openai: bool = False):
#     """Query the global index with the provided text."""
#     global index
#     global llm
#     response = index.as_query_engine(llm=llm).query(query_text)
#     return response


# def create_embedding(text):
#     """Generate an embedding for the given text."""
#     global embed_model
#     return embed_model.embed(text)


# def generate_summary(text):
#     """Generate a summary for the given text."""
#     global llm
#     response = llm.complete(prompt=f"Summarize the following text:\n{text}")
#     return response["choices"][0]["text"].strip()


# def classify_text(text, categories):
#     """Classify the text into one of the given categories."""
#     global llm
#     prompt = (
#         f"Classify the following text into one of these categories: {', '.join(categories)}.\n"
#         f"Text: {text}\n"
#         f"Category:"
#     )
#     response = llm.complete(prompt=prompt)
#     return response["choices"][0]["text"].strip()
