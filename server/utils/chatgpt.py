# from dotenv import load_dotenv
# import os
# import pprint
# import pickle

# import faiss
# import numpy as np
# from werkzeug.utils import secure_filename
# from typing_extensions import Concatenate
# import openai

# from langchain.text_splitter import CharacterTextSplitter
# from langchain.embeddings import HuggingFaceEmbeddings
# from langchain.chains.question_answering import load_qa_chain
# from sentence_transformers import SentenceTransformer

# from flask import Flask, Blueprint, request, jsonify, send_file


# load_dotenv()


# pp = pprint.PrettyPrinter(indent=4)


# main = Blueprint("main", __name__, url_prefix="/api")

# # Set the API key
# api_key = os.getenv("OPENAI_API_KEY")

# if api_key is None:
#     api_key = ""
# # Create an instance of the OpenAI class
# client = OpenAI(api_key=api_key)
# OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
# openai.api_key = OPENAI_API_KEY

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


# @main.route("/get-uploads", methods=["GET"])
# def get_uploads():
#     uploads_dir = UPLOADS_DIRECTORY
#     uploads = []

#     # Iterate through the directory
#     for subdir, dirs, files in os.walk(uploads_dir):
#         for file in files:
#             # Create an entry for each PDF and its corresponding PKL file
#             if file.endswith(".pdf"):
#                 file_name = os.path.splitext(file)[0]
#                 file_path = os.path.join(subdir, file)
#                 pickle_path = os.path.join(subdir, file_name + ".pkl")

#                 # Only add to the list if both PDF and pickle file exist
#                 if os.path.exists(pickle_path):
#                     uploads.append(
#                         {
#                             "file_name": file_name + ".pdf",
#                             "file_path": file_path,
#                             "pickle_file": pickle_path,
#                         }
#                     )

#     return jsonify(uploads), 200


# @main.route("/get-pdf", methods=["POST"])
# def get_pdf():
#     data = request.get_json()
#     file_path = data.get("file_path")

#     if not file_path:
#         return jsonify({"error": "File path is required."}), 400

#     if not os.path.isfile(file_path):
#         return jsonify({"error": "File not found."}), 404

#     # Return the file for download
#     return send_file(file_path, as_attachment=False)


# @main.route("/upload-pdf", methods=["POST"])
# def upload_file():
#     req_form = request.form.to_dict()
#     user_info = eval(
#         req_form["user"]
#     )  # Note: Using eval is dangerous and not recommended
#     print(user_info)
#     print("user info:", type(user_info))
#     if not user_info:
#         return "No User", 400

#     if "file" not in request.files:
#         return "No file part", 400

#     file = request.files["file"]
#     if file.filename == "":
#         return "No selected file", 400

#     if file:
#         # Secure filename
#         filename = secure_filename(file.filename)
#         # Create directories if they do not exist
#         user_dir = os.path.join("files", user_info["username"])
#         document_dir = os.path.join(user_dir, os.path.splitext(filename)[0])
#         os.makedirs(document_dir, exist_ok=True)
#         # Complete filepath
#         filepath = os.path.join(document_dir, filename)
#         print("filepath:", filepath)
#         # Save file
#         file.save(filepath)

#         # Process PDF to extract text
#         extract_text_from_pdf(filepath)

#         # Further processing or storing the extracted text
#         # ...
#         print("Api Request Complete")
#         return "File uploaded and processed", 200


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


# # def extract_text_from_pdf(filepath):
# #     pdf_reader = PdfReader(filepath)

# #     text_splitter = CharacterTextSplitter(
# #         separator=" ",
# #         chunk_size=100,
# #         chunk_overlap=10,
# #         length_function=len,
# #     )

# #     # You may want to define your batch size based on your system's memory constraints
# #     batch_size = 2  # Example batch size, adjust based on your requirements
# #     current_batch = []
# #     items = []

# #     for page_number, page in enumerate(pdf_reader.pages):
# #         for position, chunk in enumerate(text_splitter.split_text(page.extract_text().__str__())):
# #             text_object = {
# #                 "text": chunk,
# #                 "page_number": page_number,
# #                 "position": position,
# #             }
# #             # items.append(text_object)

# #             # When the batch reaches the batch size, process it
# #             # vector = vectorize(chunk)
# #             # text_object["vector"] = vector
# #             items.append(text_object)


# #     print(items)

# #     pickle_file = filepath
# #     picklefile = pickle_file.replace(".pdf", ".pkl")
# #     print("trying to store pickle @:", picklefile)
# #     with open(picklefile, 'wb') as f:
# #         pickle.dump(items, f)


# def vectorize(chunk):
#     # model_name = 'sentence-transformers/all-MiniLM-L6-v2'
#     # model = SentenceTransformer(model_name)
#     # return model.encode(chunk).tolist()
#     return (
#         openai.embeddings.create(input=chunk, model="text-embedding-3-small")
#         .data[0]
#         .embedding
#     )


# # while\nour\ndatabase\nmanager\nis\ndependent\nupon\nthe\nembedding\nmanager,\nthe\nlatter\nexists\nindependently.


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

#     print("I0:", I[0])
#     # Find the closest text object and return it
#     closest_item_index = I[0][0]
#     closest_item = items[closest_item_index]
#     context = get_rags_context(items, closest_item_index, num_positions=10)
#     rags = perform_query(query_text, closest_item["text"], context)

#     # print(context)

#     response = {
#         "text": closest_item["text"],
#         "page_number": closest_item["page_number"],
#         "position": closest_item["position"],
#         "rags_answer": rags["answer"],
#         "rags_context": rags["context"],
#     }
#     pp.pprint(response)
#     return jsonify(response)


# def get_rags_context(items, closest_item_index, num_positions=5):
#     """
#     Create a context for RAGS by taking text from a number of positions
#     above and below the closest item's position.

#     :param items: The list of all items.
#     :param closest_item_index: The index of the closest item.
#     :param num_positions: The number of positions to take above and below.
#     :return: A string that concatenates the context.
#     """
#     context = []
#     total_items = len(items)
#     above_count = below_count = num_positions

#     # Adjust the counts if we are at the boundaries
#     if closest_item_index < num_positions:
#         above_count = closest_item_index
#         below_count = num_positions * 2 - above_count
#     if closest_item_index + num_positions >= total_items:
#         below_count = total_items - closest_item_index - 1
#         above_count = num_positions * 2 - below_count

#     # Get the items above the closest item
#     for i in range(closest_item_index - above_count, closest_item_index):
#         context.append(items[i]["text"])

#     # Add the closest item itself
#     context.append(items[closest_item_index]["text"])

#     # Get the items below the closest item
#     for i in range(closest_item_index + 1, closest_item_index + 1 + below_count):
#         if i < total_items:  # Ensure we don't go out of bounds
#             context.append(items[i]["text"])

#     # Concatenate all the texts to form the context
#     full_context = " ".join(context)
#     return full_context


# def perform_query(user_question, closest_text, context):
#     """
#     Perform a query using the OpenAI API to retrieve information.

#     :param query: The query string to be sent to the API.
#     :param openai_api_key: Your OpenAI API key.
#     :return: The response from the API.
#     """
#     openai.api_key = OPENAI_API_KEY

#     prompt = f"I am trying to do rags to answer user questions against a pdf. Here is the user question: {user_question} here is the part of the text that most closely matches the embedding of the question and the document {closest_text}. here is the context from surrounding text {context}. please do your best to answer the question."

#     response = openai.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {
#                 "role": "system",
#                 "content": 'You will be provided with a document delimited by triple quotes and a question. Your task is to answer the question using only the provided document and to cite the passage(s) of the document used to answer the question. If the document does not contain the information needed to answer this question then simply write: "Insufficient information." If an answer to the question is provided, it must be annotated with a citation. Use the following format for to cite relevant passages ({"citation": …}).',
#             },
#             {"role": "user", "content": f"'''{context}''' Question: {user_question}"},
#         ],
#     )

#     data = {
#         "user_query": user_question,
#         "context": context,
#         "closest_text": closest_text,
#         "answer": response.choices[0].message.content,
#     }

#     return data


# # Example usage:
# # result = perform_query("Explain the concept of RAGS in AI.", "your-openai-api-key")
# # print(result)


# from transformers import pipeline

# # Load your question-answering model
# qa_model = pipeline("question-answering")


# @main.route("/search-hugging-face", methods=["POST"])
# def search_embeddings_hf():
#     data = request.json
#     query_text = data.get("query")
#     filepath = data.get("filepath")

#     if not query_text:
#         return jsonify({"error": "No query provided"}), 400

#     # Convert the query text to a vector using the same method as for the documents
#     query_vector = vectorize(query_text)

#     # Load the index and items from the pickle file
#     pickle_file = filepath
#     faiss_index, items = load_faiss_index(pickle_file)

#     # Convert the query vector to the right type and run the search
#     query_vector = np.array([query_vector]).astype("float32")
#     _, I = faiss_index.search(query_vector, 5)  # Adjust the number based on your needs

#     # Retrieve and concatenate texts from the closest items for context
#     context = " ".join([items[i]["text"] for i in I[0]])

#     # Use the QA model to find the answer
#     answer = qa_model(question=query_text, context=context)

#     return jsonify({"answer": answer["answer"], "confidence": answer["score"]})
