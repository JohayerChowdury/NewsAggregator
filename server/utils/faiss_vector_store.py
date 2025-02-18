import pickle
import numpy as np
import faiss


def load_faiss_index(pickle_file):
    with open(pickle_file, "rb") as f:
        items = pickle.load(f)
    d = len(items[0]["vector"]) if items else 0
    index = faiss.IndexFlatL2(d)
    vectors = np.array([item["vector"] for item in items]).astype("float32")
    index.add(vectors)
    return index, items


def write_faiss_index(index, index_file="large.index"):
    try:
        faiss.write_index(index, index_file)
    except Exception as e:
        print(f"Error writing Faiss index: {e}")
        pass
