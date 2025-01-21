# Name: Johayer Rahman Chowdury
# HW5, Due: Tuesday Dec 6, 2022
# Program: Unpickle, to unpickle serealized data and create text files (for specific data)

import pickle
import sys
from pathlib import Path

type_of_document = str(Path(sys.argv[2]))
text_file_path = Path(sys.argv[1]) / Path(type_of_document + ".txt")
pickle_path = Path(sys.argv[1]) / Path(type_of_document + ".pkl")
unpickled = pickle.load(open(pickle_path, "rb"))
tesc_measures = ["AP", "ndcg_at_10", "ndcg_at_100", "ndcg_at_1000", "P@10", "TBG"]

with open(text_file_path, "w") as f:
    if type_of_document == "lexicon":
        print("Now writing lexicon text file")
        f.write("There are " + str(len(unpickled)) + " tokens\n")
        for id in unpickled:
            f.write(str(unpickled[id]) + "||" + str(id) + "\n")
    elif type_of_document == "inverted_index":
        print("Now writing inverted index text file")
        total_num_of_lexicon_tokens_in_inverted_index = 0
        for id in unpickled:
            postings = unpickled[id]
            total_num_of_lexicon_tokens_in_inverted_index += len(postings)
            f.write(
                str(id)
                + " has "
                + str(len(postings))
                + " postings\nPostings: "
                + str(postings)
                + "\n"
            )
        f.write(
            "Taking the sum of the length of postings list, Inverted Index uses "
            + str(total_num_of_lexicon_tokens_in_inverted_index * 4.0)
            + " bytes.\n"
        )
        f.write(
            "Using python's sys.getsizeof() method, Inverted Index uses "
            + str(sys.getsizeof(unpickled))
            + " bytes."
        )
    elif type_of_document == "doc_length":
        print("Now writing doc length text file")
        f.write("There are " + str(len(unpickled)) + " documents\n")
        for id in unpickled:
            f.write(str(id) + " || " + str(unpickled[id]) + "\n")
    elif type_of_document in tesc_measures:
        print("Now writing " + type_of_document + " text file")
        for query_id in unpickled.keys():
            value = "{:.3f}".format(round(unpickled[query_id], 3))
            f.write(type_of_document + " " + str(query_id) + " " + value + "\n")
