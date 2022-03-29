# CS 221 / SWE 225 - Assignment 3
This project consists of creating a search engine using a given corpus. The user is able to interact with the search
engine where they can look up any terms of their liking through a defined set of web pages. From there, the top 50 results
will be shown to the user for them to review.

## Technologies
The programs in this project were run using the following:
* Python 3.6
* X11

## Setup
After downloading the project, you will want to ensure that the minimum requirements are met to run the search engine. If this
is not done, you may not be able to perform your searches as desired. To make sure you have the minimum requirments in place,
please download the indicated required packages. This can be done using `pip` through the following command in terminal:
`pip install -r requirements.txt`

Once the minimum requirements have been met, you will then want to build the indexer used for the search engine. This will create
files in your project that the search engine uses to run the search engine. If this is not done, you will not be able to perform
searches in the next steps. You can build the indexer in the following manner:
1. You will want to `cd` into the project
2. Run the Python file tied to creating the indexes needed
   - Enter `python3 indexer.py` in terminal
   - The program may take some time to fully build the indexer

After the indexes have been built, you can now run the search engine and perform your searches through the given corpus.
This is done in the following manner:
1. You will want to `cd` into the project
2. Run the search engine
    - Enter `streamlit run launcher.py` in terminal
        * This will open your browser which is the web interface tied to the search engine
