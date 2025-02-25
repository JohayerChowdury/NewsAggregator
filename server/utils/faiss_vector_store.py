# import pickle
import faiss


def write_faiss_index(index, index_file="embeddings.index"):
    try:
        faiss.write_index(index, index_file)
    except Exception as e:
        print(f"Error writing Faiss index: {e}")
        pass


def read_faiss_index(index_file="embeddings.index"):
    try:
        index = faiss.read_index(index_file)
        return index
    except Exception as e:
        print(f"Error reading Faiss index: {e}")
        return None


def create_faiss_index(embeddings_array):
    try:
        d = 384  # dimension of the embeddings
        index = faiss.IndexFlatL2(d)
        index.add(embeddings_array)
        write_faiss_index(index)
        return index
    except Exception as e:
        print(f"Error creating Faiss index: {e}")
        return None


def search_faiss_index(index, query, k=5):
    try:
        distances, indices = index.search(query, k)
        return distances, indices
    except Exception as e:
        print(f"Error searching Faiss index: {e}")
        return None, None
