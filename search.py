"""
CS 221 / SWE 225 - Assignment 3

File Name:
    search.py
    
Description:
    This program takes a query provided by the user. The terms of the query are then stemmed so that
    the appropriate documents can be presented based on the terms given.
"""
import ast
import json
import math
import re
import sys

from collections import Counter
from numpy import dot
from os import path

from nltk.stem import PorterStemmer
from numpy.linalg import norm

# Global variables to store helper indexes and corpus size in memory
doc_index = {}
doc_size = 0
vocab_index = {}

def init():
    """
    The init function starts the search program and displays the resulting documents of the query
    provided by the user
    
    Raises:
        SystemExit: If index files are not present
    """
    global doc_index
    global doc_size
    global vocab_index
    
    # List of indexes needed to perform search
    index_files = [
        'helper_indexes/final_doc_index.txt',
        'helper_indexes/final_word_index.txt',
        'main_indexes/final_search_index.txt'
    ]
    
    # Checks if all indexes are present
    index_present = [path.isfile(file) for file in index_files]
    if not all(index_present):
        sys.exit("One or more indexes is missing\n"
                 "Please ensure that 'indexer.py' is run to create necessary indexes")
    
    # Load helper indexes into memory
    with open(index_files[0]) as doc_file, open(index_files[1]) as vocab_file:
        doc_index = json.load(doc_file)
        doc_size = len(doc_index)
        vocab_index = json.load(vocab_file)

def cosine_similarity(tf, idf):
    """
    The cosine_similarity function takes two lists and computes the cosine similarity values
    between them
    
    Note:
        Similarity is being calculated under the 'lnc.ltc' weighting scheme. The 'tf' list
        contains a collection of documents and their tf score for each query term while the
        'idf' list contains the idf score for each query term
    
    Args:
        tf (list): A list of dictionaries containing the document and tf score for a query term
        idf (list): A list containing the idf score for a query term
    
    Returns:
        A list of top 50 tuples referencing documents sorted by cosine similarity score computed
    """
    # Checks that lists of equal length are provided
    if len(tf) != len(idf):
        sys.exit("Lists provided to 'cosine_similarity' function are not of equal length\n"
                 "Please review lists provided")
    else:
        length = len(tf)
    
    scores = Counter()
    
    # Checks if more than two query terms have been provided
    if length == 0:
        pass
    elif length == 1:
        scores.update(tf[0])
    
    else:
        # Note the documents involved for computing similarity
        unique_docs = set()
        for i in range(length):
            unique_docs.update(tf[i].keys())

        # Compute cosine similarity values for each unique doc
        for doc in unique_docs:
            tf_values = [tf[i].get(doc, 0) for i in range(length)]
            result = dot(tf_values, idf) / (norm(tf_values) * norm(idf))
            scores.update({doc: result})
    
    return scores.most_common(50)

def pull_documents(key_words):
    """
    The pull_documents function seraches for documents in our indexes that best fit the key words
    provided by the user
    
    Args:
        key_words (list): A list of strings containing the words needing to be referenced
    
    Raises:
        SystemExit: If value pulled from inverted index does not match key word it relates to
    
    Returns:
        A list of document IDs matching the key words given
    """
    # Grab positions of words in relation to inverted index and length of key words given
    positions = [vocab_index[word] for word in key_words]
    num_words = len(key_words)
    
    # Creates list to store inverted index values and read through index
    curr_tf = []
    curr_idf = []
    with open('main_indexes/final_search_index.txt') as index_file:
        for i in range(num_words):
            index_file.seek(positions[i])
            result = ast.literal_eval(index_file.readline().strip())
            
            # Checks that key word matches inverted index value found
            if key_words[i] != result[0]:
                sys.exit("Incorrect match with query words in relation to index\n"
                         "Please rebuild index through 'indexer.py'")
            else:
                curr_tf.append(dict(result[1]))
                curr_idf.append(result[2])
    
    # Variable to note threshold of terms that appear in 90% of corpus
    threshold = math.log10(10 / 9)
    
    # Check if idf score is less than threshold
    new_tf = []
    new_idf = []
    for i in range(num_words):
        score = curr_idf[i]
        if score < threshold:
            new_tf.append(curr_tf[i])
            new_idf.append(score)
    
    # Checks if removed key words due to high idf resulted in having no words left to check
    if not new_idf:
        new_idf = curr_idf[:]
        new_tf = curr_tf[:]
    
    # Clear out contents of previous lists in case memory needed
    curr_tf.clear()
    curr_idf.clear()
    
    # Computes cosine similarity values for each document
    results = cosine_similarity(new_tf, new_idf)
    
    return [doc[0] for doc in results]

def perform_search(query):
    """
    The perform_serach function takes the query entered by a user and presents the list of documents
    that best match the search words entered sorted by their rank results
    
    Args:
        query (str): A string containing the query terms entered by the user
    
    Returs:
        A list containing document information based on search done
    """    
    # Finds list of words in input
    pattern = re.compile("[a-zA-Z0-9@#*&']{2,}")
    word_list = pattern.findall(query)

    # Produces stemmed list of words and removes duplicates
    ps = PorterStemmer()
    stem_word_list = [ps.stem(word.lower()) for word in word_list]
    stem_word_list = list(set(stem_word_list))

    # Pulls documents found from query and prints the results
    docs = pull_documents(stem_word_list)
    docs_info = [doc_index[str(id)] for id in docs]
    
    return docs_info
