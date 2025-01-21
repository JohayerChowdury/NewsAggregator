# # Name: Johayer Rahman Chowdury
# # HW5, Due: Tuesday Dec 6, 2022
# # Program: BM25

# import sys
# import argparse
# import time
# from pathlib import Path
# import pickle
# from collections import defaultdict
# from math import log

# import IndexEngine

# baseline_retrieval = "hw4-bm25-baseline-jchowdur.txt"
# stem_retrieval = "hw4-bm25-stem-jchowdur.txt"
# latimes_file = "../../../TREC_LATimes_Data/latimes.gz"


# def ranking(bm25_accumulator, topic_number, resultsFilePath):
#     # https://www.tutorialsteacher.com/articles/sort-dict-by-value-in-python helps to DESC sort values in a dictionary
#     sorted_list_bm25_accumulator = sorted(
#         bm25_accumulator.items(), key=lambda x: x[1], reverse=True
#     )
#     sorted_dict_bm25_accumulator = dict(sorted_list_bm25_accumulator)
#     with open(resultsFilePath, "a") as f:
#         runTag = "jchowdurAND"
#         rank = 1
#         for index in list(sorted_dict_bm25_accumulator)[:1000]:
#             f.write(
#                 str(topic_number)
#                 + " Q0 "
#                 + str(index)
#                 + " "
#                 + str(rank)
#                 + " "
#                 + str(sorted_dict_bm25_accumulator[index])
#                 + " "
#                 + str(runTag)
#                 + "\n"
#             )
#             rank += 1
#         f.close()


# # modified IndexEngine method to find token ids from given lexicon
# def convert_to_ids(tokens, lexicon):
#     token_ids = defaultdict(int)
#     for token in tokens:
#         lexicon_token = lexicon[token]
#         if lexicon_token in token_ids:
#             token_ids[lexicon_token] += 1
#         else:
#             token_ids[lexicon_token] = 1
#     return token_ids


# def bm25(
#     num_occurences_term_in_query,
#     postings,
#     doc_id: str,
#     freq_of_i_in_doc,
#     doc_lengths: dict,
#     average_doc_length,
# ):
#     # tuning parameters
#     k1 = 1.2
#     k2 = 7
#     b = 0.75

#     doc_length = float(doc_lengths[doc_id])
#     k = k1 * (b * doc_length / average_doc_length + (1 - b))
#     tf_in_doc = ((k1 + 1) * freq_of_i_in_doc) / (k + freq_of_i_in_doc)
#     tf_in_query = ((k2 + 1) * num_occurences_term_in_query) / (
#         k2 + num_occurences_term_in_query
#     )
#     idf_numerator = len(doc_lengths) - len(postings) + 0.5
#     idf_denominator = len(postings) + 0.5
#     idf = log(idf_numerator / idf_denominator)
#     return tf_in_doc * tf_in_query * idf


# def main():
#     # Author: Nimesh Ghelani based on code by Mark D. Smucker
#     parser = argparse.ArgumentParser(
#         description="After using IndexEngine, retrieves top 1000 ranked results for queries given using BM25 algorithm."
#     )
#     parser.add_argument(
#         "--index-path",
#         required=True,
#         help="Path to the directory location of your index",
#     )
#     parser.add_argument(
#         "--queries-path", required=True, help="Path to the queries file"
#     )
#     parser.add_argument(
#         "--output-path", required=True, help="Path to store output in a new file"
#     )
#     parser.add_argument(
#         "--toStem",
#         type=int,
#         help="Optional argument: 0 for basic tokenization, 1 for stemming in tokenization (default is 0)",
#     )
#     cli = parser.parse_args()

#     startTimeTotal = time.time()

#     # try, except block for path to directory for index
#     try:
#         document_stored_directory = Path(cli.index_path)
#     except FileNotFoundError:
#         msg = (
#             "Directory "
#             + str(document_stored_directory)
#             + " does not exist. Please provide correct directory path."
#         )
#         sys.exit(msg)

#     try:
#         queries = Path(cli.queries_path)
#     except FileNotFoundError:
#         msg = (
#             "File "
#             + str(queries)
#             + " does not exist. Please provide correct queries file."
#         )
#         sys.exit(msg)

#     lexiconPath = document_stored_directory / "lexicon.pkl"
#     startTimeUnpickleLexicon = time.time()
#     lexicon = pickle.load(open(lexiconPath, "rb"))
#     endTimeUnpickleLexicon = time.time()
#     print(
#         "Lexicon unpickling time taken: ",
#         (endTimeUnpickleLexicon - startTimeUnpickleLexicon),
#     )

#     doc_lengths_path = document_stored_directory / "doc_length.pkl"
#     startTimeUnpickleDocLengths = time.time()
#     doc_lengths = pickle.load(open(doc_lengths_path, "rb"))
#     endTimeUnpickleDocLengths = time.time()
#     print(
#         "Doc lengths unpickling time taken: ",
#         (endTimeUnpickleDocLengths - startTimeUnpickleDocLengths),
#     )

#     mapping_path = document_stored_directory / "mapping_between_id_and_docno.pkl"
#     startTimeUnpickleMapping = time.time()
#     mapping = pickle.load(open(mapping_path, "rb"))
#     endTimeUnpickleMapping = time.time()
#     print(
#         "Mapping unpickling time taken: ",
#         (endTimeUnpickleMapping - startTimeUnpickleMapping),
#     )

#     invertedIndexPath = document_stored_directory / "inverted_index.pkl"
#     startTimeUnpickleInvertedIndex = time.time()
#     invertedIndex = pickle.load(open(invertedIndexPath, "rb"))
#     endTimeUnpickleInvertedIndex = time.time()
#     print(
#         "Inverted Index unpickling time taken: ",
#         (endTimeUnpickleInvertedIndex - startTimeUnpickleInvertedIndex),
#     )

#     startTimeAfterUnpickled = time.time()

#     average_doc_length = sum(doc_lengths.values()) / len(doc_lengths)
#     print("Average doc length is: " + str(average_doc_length))

#     with open(queries, "r") as f1:
#         # for every topic
#         for topic_line in f1:
#             topic_number = int(topic_line[0:3])
#             print("Now running BM25 for topic number: " + str(topic_number))
#             query = topic_line[5:]

#             # tokenizing query
#             query_tokens = IndexEngine.tokenize(query, cli.toStem)
#             query_tokens_ids = convert_to_ids(query_tokens, lexicon)

#             # create accumulator to store partial scores of query terms
#             bm25_accumulator = {}

#             # for every term in query
#             for query_term in query_tokens_ids:
#                 num_occurences_term_in_query = query_tokens_ids[query_term]
#                 postings = invertedIndex[query_term]
#                 for posting in postings:
#                     doc_id = str(posting[0])
#                     freq_of_i_in_doc = int(posting[1])
#                     bm25_query_term = bm25(
#                         num_occurences_term_in_query,
#                         postings,
#                         doc_id,
#                         freq_of_i_in_doc,
#                         doc_lengths,
#                         average_doc_length,
#                     )
#                     docno = mapping[doc_id]
#                     if docno in bm25_accumulator:
#                         bm25_accumulator[docno] += bm25_query_term
#                     else:
#                         bm25_accumulator[docno] = bm25_query_term
#             ranking(
#                 bm25_accumulator,
#                 topic_number,
#                 Path(document_stored_directory / cli.output_path),
#             )

#     endTimeTotal = time.time()
#     print(
#         "Time after unpickling and running bm25 algorithim for document collection: ",
#         (endTimeTotal - startTimeAfterUnpickled),
#     )
#     print("Total Time taken: ", (endTimeTotal - startTimeTotal))


# if __name__ == "__main__":
#     main()
