# from dotenv import load_dotenv
# import os
# import pprint
# import pickle

# import faiss
# import numpy as np
# from werkzeug.utils import secure_filename
# from typing_extensions import Concatenate
# from openai import OpenAI

# from langchain.text_splitter import CharacterTextSplitter
# from langchain.embeddings import HuggingFaceEmbeddings

# from flask import Blueprint, request, jsonify, send_file


# load_dotenv()


# pp = pprint.PrettyPrinter(indent=4)


# main = Blueprint("main", __name__, url_prefix="/api")

# # Set the API key
# openai_api_key = os.getenv("OPENAI_API_KEY")

# if openai_api_key is None:
#     openai_api_key = ""
# # Create an instance of the OpenAI class
# client = OpenAI(api_key=openai_api_key)


# def summarize_article(article_text):
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a helpful assistant that summarizes articles.",
#             },
#             {
#                 "role": "user",
#                 "content": f"Summarize the following article: {article_text}",
#             },
#         ],
#         max_tokens=150,
#     )
#     return response.choices[0].message["content"]


# UPLOADS_DIRECTORY = os.environ.get("FILES_DIRECTORY")


# def extract_text_from_pdf(filepath):
#     PdfReader = HuggingFaceEmbeddings.get_pdf_reader()
#     pdf_reader = PdfReader(filepath)
#     items = []

#     for page_number, page in enumerate(pdf_reader.pages):
#         print(f"on page {page_number}/{pdf_reader.pages}")
#         # Extract text from page and replace newlines with spaces
#         page_text = (
#             page.extract_text().replace("\n", " ") if page.extract_text() else ""
#         )

#         # Initialize your splitter with updated page_text
#         text_splitter = CharacterTextSplitter(
#             separator=" ",
#             chunk_size=3000,  # Adjust the size as needed
#             chunk_overlap=100,  # Adjust the overlap as needed
#             length_function=len,
#         )

#         # Use the splitter to split the cleaned page_text
#         for position, chunk in enumerate(text_splitter.split_text(page_text)):
#             text_object = {
#                 "text": chunk,
#                 "page_number": page_number,
#                 "position": position,
#             }
#             vector = vectorize(chunk)
#             text_object["vector"] = vector
#             items.append(text_object)

#     print(items)
#     # Your logic for storing or processing the chunks
#     # ...
#     pickle_file = filepath
#     picklefile = pickle_file.replace(".pdf", ".pkl")
#     print("trying to store pickle @:", picklefile)
#     with open(picklefile, "wb") as f:
#         pickle.dump(items, f)


# def vectorize(chunk):
#     # model_name = 'sentence-transformers/all-MiniLM-L6-v2'
#     # return model.encode(chunk).tolist()
#     return (
#         openai.embeddings.create(input=chunk, model="text-embedding-3-small")
#         .data[0]
#         .embedding
#     )


# @main.route("/get_embeddings", methods=["GET"])
# def get_stored_embeddings():
#     # Get the file path from the query parameters
#     filepath = request.args.get("filepath")

#     # Check if the file exists
#     if not os.path.exists(filepath):
#         return jsonify({"error": "File not found"}), 404
#     print("path to pdf found")
#     # The pickle file is assumed to be in the same directory as the PDF, with a .pkl extension
#     pickle_file = filepath.replace(".pdf", ".pkl")
#     print("path to pkl = ", pickle_file)
#     # Check if the pickle file exists
#     if not os.path.exists(pickle_file):
#         return jsonify({"error": "Embeddings not found"}), 404

#     # Load the embeddings from the pickle file
#     with open(pickle_file, "rb") as f:
#         embeddings = pickle.load(f)

#     # Return the embeddings as JSON
#     return jsonify(embeddings)


# def load_faiss_index(pickle_file):
#     with open(pickle_file, "rb") as f:
#         items = pickle.load(f)
#     # Assuming all vectors are of the same size
#     d = len(items[0]["vector"]) if items else 0
#     index = faiss.IndexFlatL2(d)  # Create a flat (brute force) index
#     vectors = np.array([item["vector"] for item in items]).astype("float32")
#     index.add(vectors)  # Add vectors to the index
#     return index, items


# # API endpoint for search
# @main.route("/search", methods=["POST"])
# def search_embeddings():
#     data = request.json
#     query_text = data.get("query")
#     filepath = data.get("picklePath")
#     if not query_text:
#         return jsonify({"error": "No query provided"}), 400

#     # Convert the query text to a vector using the same method as for the documents
#     query_vector = vectorize(query_text)

#     # Load the index and items from the pickle file
#     # Make sure to pass the correct path to your pickle file
#     pickle_file = filepath
#     faiss_index, items = load_faiss_index(pickle_file)

#     # Convert the query vector to the right type and run the search
#     query_vector = np.array([query_vector]).astype("float32")
#     _, I = faiss_index.search(query_vector, 1)  # Search for the top 1 nearest vector

#     # Find the closest text object and return it
#     closest_item_index = I[0][0]
#     closest_item = items[closest_item_index]

#     # print(context)

#     response = {
#         "text": closest_item["text"],
#         "page_number": closest_item["page_number"],
#         "position": closest_item["position"],
#     }
#     pp.pprint(response)
#     return jsonify(response)
