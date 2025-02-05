# from flask import Blueprint, request, jsonify
# import os
# import pickle
# import numpy as np
# import faiss
# from openai import OpenAI
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Initialize OpenAI client
# openai_api_key = os.getenv("OPENAI_API_KEY")
# client = OpenAI(api_key=openai_api_key)

# search_bp = Blueprint("search", __name__, url_prefix="/api")


# def vectorize(chunk):
#     return (
#         client.embeddings.create(input=chunk, model="text-embedding-3-small")
#         .data[0]
#         .embedding
#     )


# def load_faiss_index(pickle_file):
#     with open(pickle_file, "rb") as f:
#         items = pickle.load(f)
#     d = len(items[0]["vector"]) if items else 0
#     index = faiss.IndexFlatL2(d)
#     vectors = np.array([item["vector"] for item in items]).astype("float32")
#     index.add(vectors)
#     return index, items


# @search_bp.route("/search-articles", methods=["POST"])
# def search_articles():
#     data = request.json
#     query_text = data.get("query")
#     pickle_file = data.get("picklePath")

#     if not query_text:
#         return jsonify({"error": "No query provided"}), 400

#     query_vector = vectorize(query_text)
#     faiss_index, items = load_faiss_index(pickle_file)

#     query_vector = np.array([query_vector]).astype("float32")
#     _, I = faiss_index.search(query_vector, 10)  # Search for the top 10 nearest vectors

#     results = []
#     for idx in I[0]:
#         item = items[idx]
#         results.append(
#             {
#                 "text": item["text"],
#                 "page_number": item["page_number"],
#                 "position": item["position"],
#             }
#         )

#     return jsonify(results), 200
