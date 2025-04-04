# import os
# import numpy as np
# import json

# from .scrapers.beautifulsoup_scraper import check_for_required_columns

# # source: https://www.perplexity.ai/search/we-want-to-track-all-news-rela-fkvIqwT2Tum_rBEBC8b4zg#8

# gpt_model = os.environ.get("LLM_MODEL")
# print(f"Using GPT model: {gpt_model}")

# def generate_theme_label(cluster_texts):
#     prompt = f"'''{' '.join(cluster_texts[:3])}''' Question: What is the connecting theme among these articles in 5 words or less?"
#     try:
#         '''
#         response = openai_client.chat.completions.create(
#             stream=False,
#             model=gpt_model,
#             messages=[
#                 {
#                     "role": "developer",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": """
#                                 You are an AI expert journalist in the housing and finance sector, especially in Canada.
#                                 You strictly answer questions without unnecessary introductions or conclusions.
#                                 You are provided with a document that represent several news articles, delimited by triple quotes and a question.
#                                 Your task is to answer the question using only the provided document.
#                                 """,
#                         }
#                     ],
#                 },
#                 {"role": "user", "content": prompt},
#             ],
#             max_tokens=10,
#         )
#         response_text = response.choices[0].message.content
#         print(f"Generated theme label: {response_text}")
#         '''
#         return
#     except Exception as e:
#         print(f"Error generating theme label:")
#         print(e)
#         return "Unlabeled Theme"


# def generate_summary(theme_name, articles):
#     prompt = f" '''{' '.join(articles[:5])}''' Question: These articles are grouped with the following theme {theme_name}. What is the summary of these articles? Answer in 100 words or less."
#     try:
#         '''
#         response = openai_client.chat.completions.create(
#             stream=False,
#             model=gpt_model,
#             messages=[
#                 {
#                     "role": "developer",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": """
#                                 You are an AI expert journalist in the housing and finance sector, especially in Canada.
#                                 You strictly answer questions without unnecessary introductions or conclusions.
#                                 You are provided with several documents that represent several news articles, delimited by triple quotes and a question.
#                                 Your task is to answer the question using only the provided document.
#                                 """,
#                         }
#                     ],
#                 },
#                 {"role": "user", "content": prompt},
#             ],
#             max_tokens=100,
#         )
#         '''
#         return
#     except Exception as e:
#         print(f"Error generating summary: {str(e)}")
#         return "Summary unavailable due to an error."


# def generate_jot_notes(df):
#     results = []
#     check_for_required_columns(df, ["theme_cluster", "theme_name", "extracted_content"])
#     try:
#         unique_theme_groups = df.groupby("theme_cluster")
#         for theme_id, group in unique_theme_groups:
#             articles_json = json.loads(group.to_json(orient="records"))
#             theme_name = group["theme_name"].unique()[0]
#             article_corpuses = group["extracted_content"].tolist()
#             summary = generate_summary(theme_name, article_corpuses)
#             results.append(
#                 {
#                     "summary": summary,
#                     "theme_name": theme_name,
#                     "articles": articles_json,
#                 }
#             )

#         # summaries_collection_id = "67be1d69551e9bfbece97364"
#         # updated_webflow_collection_response = update_collection(
#         #     summaries_collection_id, results
#         # )
#     except Exception as e:
#         print("Error generating jot notes:")
#         print(e)
#     return results
