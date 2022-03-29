"""
CS 221 / SWE 225 - Assignment 3

File Name:
    indexer.py
    
Description:
    This program takes a zip file containing various json files. Each file represents the contents of a
    web page. The contents are stored in an index to correlation the location and score of a particular
    word. Additional indexes are also created to assist with determining document information and word
    location in relatino to the index created.
"""
#!/usr/bin/env python3

import ast
import heapq
import json
import math
import os
import re
import sys

from bs4 import BeautifulSoup
from bs4 import Comment
from collections import Counter
from collections import defaultdict
from contextlib import ExitStack
from time import time
from zipfile import ZipFile

from nltk.stem import PorterStemmer

# Global variables to track various items during construction of inverted index
doc_id = 0
doc_index = {}
search_index = defaultdict(list)
helper_path = 'helper_indexes'
main_path = 'main_indexes'

def weighted_frequencies(element):
    """
    The weighted_frequencies function determines the term frequencies in their weighted
    form (prior to log operation) based on importance
    
    Args:
        element (object): A Tag object containing text
    
    Returns:
        A Counter object with the weighted frequencies of the terms in the element
    """
    # Finds list of words in tag
    pattern = re.compile("[a-zA-Z0-9@#*&']{2,}")
    word_list = pattern.findall(element.strip())
    
    # Produces stemmed list of words in page and counts their current frequencies
    ps = PorterStemmer()
    stem_word_list = [ps.stem(word.lower()) for word in word_list]
    freqs = Counter(stem_word_list)
    
    # Updates frequencies found based on tag name
    # titles: weight of 0.4, headings: weight of 0.3, strong: weight of 0.2, all other: weight of 0.1
    tag_name = element.parent.name
    if tag_name == 'title':
        weight = 0.4
    elif not re.match('h[1-6]', tag_name) is None:
        weight = 0.3
    elif tag_name in {'strong', 'b'}:
        weight = 0.2
    else:
        weight = 0.1
    for key in freqs.keys():
        freqs[key] *= weight
    
    return freqs

def extract_contents(page):
    """
    The extract_contents function pulls the contents of the page being reviewed
    
    Args:
        page (str): A string representing the details of the page
    """
    global search_index
    
    # Extracts contents of the page
    content = BeautifulSoup(page, 'lxml')
    all_text = content.find_all(text=True)
    
    freqs = Counter()
    for tag in all_text:
        
        # Ignores tags that are not visible on page
        # https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
        if tag.parent.name in {'style', 'script', 'head', 'meta', '[document]'} or isinstance(tag, Comment):
            continue
        
        # Collects weighted term frequencies and stores them into Counter
        temp = weighted_frequencies(tag)
        freqs += temp
    
    # Computes the log word frequencies and adds them to memory with document association
    for word in freqs:
        score = 2 + math.log10(freqs[word])
        search_index[word].append((doc_id, score))

def indexes_to_disk():
    """
    The indexes_to_disk function writes the indexes we have for words and documents to disk in
    order to clear up memory usage
    """
    global doc_index
    global search_index
    
    # Note files to be created
    current_time = time()
    doc_index_file = f'{helper_path}/{current_time}_doc_index.txt'
    search_index_file = f'{main_path}/{current_time}_search_index.txt'
    
    # Create directories for files if not present already
    os.makedirs(helper_path, exist_ok=True)
    os.makedirs(main_path, exist_ok=True)
    
    # Creates partial indexes and adds contents
    with open(doc_index_file, mode='w+') as doc_file:
        for (k, v) in doc_index.items():
            doc_file.write(f'{str([k, v])}\n')
    with open(search_index_file, mode='w+') as search_file:
        for (k, v) in sorted(search_index.items()):
            search_file.write(f'{str([k, v])}\n')
    
    # Resets global variables for later usage
    doc_index.clear()
    search_index.clear()

def traverse_zip_file(file_name):
    """
    The traverse_zip_file function reviews and extracts the files found within the zip file
    
    Args:
        file_name (str): A string representing the name of the zip file
    """
    global doc_id
    global doc_index
    
    # Opens zip file and traverses through files within it
    with ZipFile(file_name) as myzip:
        for file in myzip.namelist():
            
            # Checks that file being viewed is json file
            if not file.lower().endswith('.json'):
                continue
            
            # Reads the contents of the json file and converts it to dictionary
            page_string = myzip.read(file).decode('utf-8', errors='replace')
            page_dict = json.loads(page_string)
            
            # Indicate document ID for file and add it to index
            doc_id += 1
            doc_index[doc_id] = [file, page_dict['url']]
            
            # Extracts the page contents
            extract_contents(page_dict['content'])
            
            # Writes indexes to disk after certain number of documents
            if doc_id % 5000 == 0:
                indexes_to_disk()
    
    # Creates new partial index based on current indexes still in memory
    indexes_to_disk()

def finalize_doc_index():
    """
    The finalize_doc_index function combines the partial indexes from disk to produce
    our final index for document IDs
    """
    global doc_index
    
    # Notes file to be created and list of partial indexes
    doc_index_file = f'{helper_path}/final_doc_index.txt'
    doc_partial_indexes = os.listdir(helper_path)
    
    # Reads through each '_doc_index.txt' partial file and adds it to dictionary in memory
    for partial_file in doc_partial_indexes:
        if not partial_file.endswith('_doc_index.txt'):
            continue
        with open(f'{helper_path}/{partial_file}') as file:
            for line in file:
                doc = ast.literal_eval(line.strip())
                doc_index[doc[0]] = doc[1]
    
    # Creates final document index
    with open(doc_index_file, mode='w+') as doc_file:
        json.dump(doc_index, doc_file, indent=4)
    
    # Clears out contents of global variable from memory
    doc_index.clear()

def next_word(indexes):
    """
    The next_word function reviews each partial index and returns the next alphabetical word
    between all of them
    
    Args:
        indexes (list): A list of file objects representing our partial indexes
    
    Returns:
        A generator for the alphabetical next word in the partial search indexes with accompanying
        document information
    """ 
    # Creates list to maintain lines read from partial indexes with their index reference
    word_info = [ast.literal_eval(file.readline().strip()) for file in indexes]
    for i in range(len(indexes)):
        word_info[i].append(i)
    
    # Converts list to a heap queue
    heapq.heapify(word_info)
    
    while True:       
        # Checks if there are no more words to record for any of the partial indexes
        if not word_info:
            break
        
        # Grabs information of lowest word in heap queue with location
        info = heapq.heappop(word_info)
        location = info.pop()
        
        # Grabs the next word from the file location
        new_word = indexes[location].readline().strip()
        
        # Checks if EOF was not reached for partial index read
        if new_word:
            
            # Adds new word with its index reference to heap queue
            new_info = ast.literal_eval(new_word)
            new_info.append(location)
            heapq.heappush(word_info, new_info)
        
        yield info

def finalize_search_index():
    """
    The finalize_search_index function combines the partial indexes from disk to produce
    our final index for search functionality and word location
    """    
    # Note files to be created and list of partial indexes
    word_index_file = f'{helper_path}/final_word_index.txt'
    search_index_file = f'{main_path}/final_search_index.txt'
    search_partial_indexes = os.listdir(main_path)
    
    # Create dictionary and tracker to house word locations within final index
    word_index = {}
    word_location = 0
    
    # Creates context managers for all files needing to be reviewed
    with open(search_index_file, mode='w+') as search_file:
        with ExitStack() as stack:
            files = [stack.enter_context(open(f'{main_path}/{partial_file}')) for partial_file
                     in search_partial_indexes if partial_file.endswith('_search_index.txt')]
            
            # Variable to keep track of results returned from next_word function
            prev_result = ['', []]
            
            # Iterates through each word found alphabetically
            for result in next_word(files):
                
                # Checks if new word returned matches previous word returned to add document references
                if prev_result[0] == result[0]:
                    prev_result[1].extend(result[1])
                    
                else:
                    # Adds the previous resulting word to dictionary with its location
                    word_index[prev_result[0]] = word_location
                    
                    # Compute tf score for term in relation to corpus
                    doc_freqs = len(prev_result[1])
                    if doc_freqs > 0:
                        prev_result.append(math.log10(doc_id / doc_freqs))

                    # Writes result to search index and updates location for next word
                    # Only the top docs with highests tf scores are used
                    prev_result[1] = Counter(dict(prev_result[1])).most_common(250)
                    entry = f'{str(prev_result)}\n'
                    search_file.write(entry)
                    word_location += len(entry)
                    
                    # Updates previous result with current result
                    prev_result = result
            
            # Updates indexes with last word received
            word_index[prev_result[0]] = word_location
            doc_freqs = len(prev_result[1])
            if doc_freqs > 0:
                prev_result.append(math.log10(doc_id / doc_freqs))
            prev_result[1] = Counter(dict(prev_result[1])).most_common(250)
            entry = f'{str(prev_result)}\n'
            search_file.write(entry)
            
    # Writes the resuting word dictionary with accompanying locations
    with open(word_index_file, mode='w+') as word_file:
        json.dump(word_index, word_file, indent=4)

def main():
    """
    The main function runs the indexer program and creates various indexes to store document, term,
    and score information based on zip file provided
    
    Raises:
        SystemExit: If indicated zip file is not within same directory as program
    """
    # Zip file to reference for program operation
    zip_file = 'developer.zip'
    
    # Checks if zip file is within same directory as program
    if not os.path.isfile(zip_file):
        sys.exit("Zip file containing web pages was not found\n"
                 "Please ensure that 'developer.zip' is placed within the same directory")
    
    # Traverses through zip file
    traverse_zip_file(zip_file)
    
    # Finalizes partial indexes created
    finalize_doc_index()
    finalize_search_index()

if __name__ == "__main__":
    main()
