# # Name: Johayer Rahman Chowdury
# # HW4, Due: Friday Nov 25, 2022
# # Program: IndexEngine, modified from HW3 for optimization

# import sys
# import argparse
# import gzip as gz
# from pathlib import Path
# import xml.etree.ElementTree as ET
# from datetime import date
# from collections import defaultdict
# import time
# import pickle
# from utils import PorterStemmer

# lexicon_token_to_id = {}  # mapping from key:token to value:token_id
# inverted_index = defaultdict(
#     list
# )  # postings list of every token_id to document and number of occurences in document (ignoring 0 occurences)
# doc_lengths = (
#     {}
# )  # dictionary of document and its length, len of which is number of documents
# mapping = {}  # mapping from key:docid to value:docno


# def add_to_postings(word_counts, doc_id):
#     for id in word_counts:
#         inverted_index[id].append([doc_id, word_counts[id]])


# def count_words(token_ids):
#     word_counts = {}
#     for id in token_ids:
#         if id in word_counts:
#             word_counts[id] += 1
#         else:
#             word_counts[id] = 1
#     return word_counts


# def convert_to_ids(tokens):
#     token_ids = []
#     for token in tokens:
#         if token not in lexicon_token_to_id:
#             lexicon_token_to_id[token] = len(lexicon_token_to_id)
#         token_ids.append(lexicon_token_to_id[token])
#     return token_ids


# # method for tokenization, inspired from pseduocode given in MSCI 541 lecture
# def tokenize(text: str, toStem=False):
#     tokens = []
#     text = text.lower()
#     start = 0
#     for current_index in range(len(text)):
#         if not text[current_index].isalnum():
#             if current_index != start:
#                 tokens.append(text[start:current_index])
#             start = current_index + 1
#         if text[current_index].isalnum() and current_index == (len(text) - 1):
#             tokens.append(text[start:current_index])
#     if toStem:
#         p = PorterStemmer()
#         stemmed_tokens = []
#         for stem_token in tokens:
#             stem_token = p.stem(stem_token, 0, len(stem_token) - 1)
#             stemmed_tokens.append(stem_token)
#         return stemmed_tokens
#     return tokens


# # method that returns month, day, year from DOCNO tag
# def process_doc_date(date_text: str):
#     month = date_text[:2]
#     day = date_text[2:4]
#     year = date_text[4:6]
#     year_updated = "19" + year
#     full_date_string = year_updated + "-" + month + "-" + day
#     full_date = date.fromisoformat(full_date_string)
#     return month, day, year, full_date


# # process the document retrieved to store document and metadata
# def process_doc(doc: bytes, document_stored_directory: Path, toStem: int):
#     # use XML reader to fetch tags easily
#     root = ET.fromstring(doc)

#     # find docno tag in root
#     docno = root.findtext("DOCNO")

#     # remove whitespace and extra characters to process date
#     docno = docno.replace(" ", "")
#     docno_text = docno.replace("LA", "")
#     month, day, year, full_date = process_doc_date(docno_text)

#     # documents subdirectory and document files
#     doc_file = docno + ".txt.gz"
#     doc_metadata_file = docno + "_metadata.txt.gz"

#     # paths to directories and files
#     year_path = document_stored_directory / year
#     month_path = year_path / month
#     day_path = month_path / day
#     doc_file_path = day_path / doc_file
#     doc_metadata_file_path = day_path / doc_metadata_file

#     # if path to directory doesn't exist, make a directory
#     if not year_path.exists():
#         year_path.mkdir(parents=True)
#     if not month_path.exists():
#         month_path.mkdir(parents=True)
#     if not day_path.exists():
#         day_path.mkdir(parents=True)

#     # retrieve text for inverted index, <TEXT>, <HEADLINE>, <GRAPHIC> and append tokenized text to list of tokens
#     tokens = []
#     willStem = False
#     if toStem == 1:
#         willStem = True

#     if root.find("HEADLINE"):
#         headline = root.findtext("HEADLINE/P").replace("\n", "")
#         tokens += tokenize(headline, willStem)
#     else:
#         headline = "headline does not exist"

#     for text_tag in root.findall("TEXT"):
#         for p_tag in text_tag.findall("P"):
#             tokens += tokenize(p_tag.text, willStem)

#     if root.find("GRAPHIC"):
#         tokens += tokenize(root.findtext("GRAPHIC/P"), willStem)

#     # other relevant metadata
#     docid = root.findtext("DOCID").replace(" ", "")
#     date = full_date.strftime("%B %d, %Y")

#     # inverted index
#     token_ids = convert_to_ids(tokens)
#     word_counts = count_words(token_ids)
#     add_to_postings(word_counts, docid)

#     # write to mapping dictionary
#     mapping[docid] = docno

#     # write to doc_lengths dictionary
#     doc_length = len(tokens)
#     doc_lengths[docid] = doc_length

#     # writing doc and metadata to associated files in specific directories
#     doc_file_path.write_bytes(ET.tostring(root))
#     metadata = bytes(
#         "docno: "
#         + docno
#         + "\n"
#         + "internal id: "
#         + docid
#         + "\n"
#         + "date: "
#         + date
#         + "\n"
#         + "headline: "
#         + headline
#         + "\n"
#         + "document length: "
#         + str(doc_length),
#         "utf-8",
#     )
#     doc_metadata_file_path.write_bytes(metadata)


# def main():
#     # Author: Nimesh Ghelani based on code by Mark D. Smucker
#     parser = argparse.ArgumentParser(
#         description="Using a document collection, stores each document and its associated metadata seperately in folders."
#     )
#     parser.add_argument(
#         "--directory",
#         required=True,
#         help="Path to the directory where the documents and metadata will be stored.",
#     )
#     parser.add_argument(
#         "--toStem",
#         type=int,
#         help="Optional argument: 0 for basic tokenization, 1 for stemming in tokenization (default is 0)",
#     )
#     cli = parser.parse_args()

#     startTimeTotal = time.time()
#     startTime = time.strftime("%H:%M", time.localtime())
#     print("Time started running IndexEngine: " + startTime)

#     # try, except block for path to directory for metadata and documents
#     try:
#         # read second argument for documents directory
#         document_stored_directory = Path(cli.directory)
#         document_stored_directory.mkdir(parents=True)
#         print("Created directory: ", document_stored_directory)

#     except FileExistsError:
#         sys.exit("Directory already exists :(")

#     # comment out for testing
#     except gz.BadGzipFile:
#         sys.exit("invalid gzipped file :( , input file must be compressed with gzip")

#     startTimeProcessDocs = time.time()
#     print("Documents are now being processed by the IndexEngine")
#     # doc = b''
#     # for line in f1:
#     #     if line.startswith(b'<DOC>'):
#     #         doc = b''
#     #     if line.startswith(b'</DOC>'):
#     #         doc += line
#     #         process_doc(doc, document_stored_directory, cli.toStem)
#     #     elif not line.startswith(b' '):
#     #         doc += line
#     endTimeProcessDocs = time.time()
#     endTimeProcessDocsPrint = time.strftime("%H:%M", time.localtime())
#     print(
#         "Processing and tokenizing documents and creating directories time taken: ",
#         (endTimeProcessDocs - startTimeProcessDocs),
#     )
#     print(
#         "Time finished processing documents: "
#         + endTimeProcessDocsPrint
#         + "\nNow creating relevant files"
#     )

#     # writing to lexicon file
#     lexicon_file = "lexicon.pkl"
#     lexicon_path = document_stored_directory / lexicon_file
#     startTimeLexiconWriting = time.time()
#     pickle.dump(lexicon_token_to_id, open(lexicon_path, "wb"))
#     endTimeLexiconWriting = time.time()
#     print(
#         "Lexicon writing time taken: ",
#         (endTimeLexiconWriting - startTimeLexiconWriting),
#     )

#     # writing to doc lengths file
#     doc_length_file = "doc_length.pkl"
#     doc_length_path = document_stored_directory / doc_length_file
#     startTimeDocLengthWriting = time.time()
#     pickle.dump(doc_lengths, open(doc_length_path, "wb"))
#     endTimeDocLengthWriting = time.time()
#     print(
#         "Doc Length writing time taken: ",
#         (endTimeDocLengthWriting - startTimeDocLengthWriting),
#     )

#     # writing to mapping file
#     mapping_file = "mapping_between_id_and_docno.pkl"
#     mapping_path = document_stored_directory / mapping_file
#     startTimeMappingWriting = time.time()
#     pickle.dump(mapping, open(mapping_path, "wb"))
#     endTimeMappingWriting = time.time()
#     print(
#         "Mapping writing time taken: ",
#         (endTimeMappingWriting - startTimeMappingWriting),
#     )

#     # writing to inverted index file
#     inverted_index_file = "inverted_index.pkl"
#     inverted_index_path = document_stored_directory / inverted_index_file
#     startTimeInvertedIndexWriting = time.time()
#     pickle.dump(inverted_index, open(inverted_index_path, "wb"))
#     endTimeInvertedIndexWriting = time.time()
#     print(
#         "Inverted Index writing time taken: ",
#         (endTimeInvertedIndexWriting - startTimeInvertedIndexWriting),
#     )

#     endTimeTotal = time.time()

#     print("Total Time taken: ", (endTimeTotal - startTimeTotal))
#     sys.exit(
#         "Documents and their metadata are now found in their respective folders organized by YY/MM/DD in "
#         + str(document_stored_directory)
#     )


# if __name__ == "__main__":
#     main()
