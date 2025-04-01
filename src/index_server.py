import os
import pickle

from multiprocessing import Lock
from multiprocessing.managers import BaseManager

# llm
from llama_index.llms import OpenAI, Ollama

# embedding model
from llama_index.embeddings import OpenAIEmbedding, OllamaEmbedding

from llama_index import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)

from llama_index.core.node_parser import SentenceSplitter

# index: VectorStoreIndex = None
index = None
stored_docs = {}
lock = Lock()

index_name = "./saved_index"
pkl_name = "./stored_documents.pkl"


def init_index(use_openai: bool = False):
    """Create a new global index, or load one from the pre-set path."""
    global index, stored_docs

    storage_context = StorageContext.from_defaults(persist_dir=index_name)
    # transformations = SentenceSplitter(chunk_size=512, chunk_overlap=0)
    embed_model = (
        OpenAIEmbedding(model="text-embedding-3-large")
        if use_openai
        else OllamaEmbedding(model_name="nomic-embed-text:latest")
    )

    with lock:
        if os.path.exists(index_name):
            index = load_index_from_storage(
                storage_context,
                embed_model=embed_model,
            )
        else:
            index = VectorStoreIndex(
                nodes=[],
                embed_model=embed_model,
            )
            index.storage_context.persist(persist_dir=index_name)
        if os.path.exists(pkl_name):
            with open(pkl_name, "rb") as f:
                stored_docs = pickle.load(f)


def query_index(query_text, use_openai: bool = False):
    """Query the global index with the provided text."""
    global index
    llm = (
        OpenAI(model="gpt-3.5-turbo", temperature=0)
        if use_openai
        else Ollama(model="llama3.2:latest", request_timeout=120.0)
    )
    response = index.as_query_engine(llm=llm).query(query_text)
    return response
