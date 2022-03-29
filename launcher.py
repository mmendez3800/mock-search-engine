"""
CS 221 / SWE 225 - Assignment 3

File Name:
    launcher.py
    
Description:
    This program renders a web interface that the user can interact with. It is from here
    that the query terms entered will output a list of docs that best match the search
    terms entered.
"""
import math
import search
import streamlit as st

from time import time

def init_page_details():
    """
    The init_page_details function sets up the behind-the-scenes details that are contained within
    the page such as the search engine display, URL, and pagination information
    """
    # Inintialize backend search program
    search.init()
    
    # Updates search engine display if a search is already present
    if 'search' in st.session_state:
        st.set_page_config(page_title=f'{st.session_state.search} - UCI Scholar Search', page_icon=':brain:', layout='wide')
        st.experimental_set_query_params(search=st.session_state.search)
    
    # Sets a default display if a search is not present
    else:
        st.set_page_config(page_title='UCI Scholar', page_icon=':brain:')
        st.experimental_set_query_params()
        st.session_state.page = 1

def reset_pagination():
    """
    The reset_pagination function restarts the state value for the 'page' the user is on related
    to a search performed
    """
    st.session_state.page = 1

def update_pagination():
    """
    The update_pagination function increates the state value for the 'page' the user is on related
    to a search performed
    """
    st.session_state.page += 1

def run_search():
    """
    The perform_search function completes the search performed by the user based on the query
    terms entered
    """
    # Pulls search results and information on time completion and search size
    start_time = time()
    results = search.perform_search(st.session_state.search)
    end_time = time()
    total_time = math.floor((end_time - start_time) * 1000)
    
    # Stores the information into a state for later reference
    st.session_state.results = results
    st.session_state.total = len(results)
    st.session_state.time = total_time

def search_details():
    """
    The search_details function displays information regarding the query performed by
    the user such as the number of results and time to pull them
    
    Returns:
        A string containing the search result information
    """
    return f"""
            <div style="color: grey">
                {st.session_state.total} results ({st.session_state.time} milliseconds)
            </div>
            <br>
            """

def search_nil():
    """
    The search_nil function displays that there were no resuls found for the query terms
    entered by the user in the search engine
    
    Returns:
        A string containing information of no search results
    """
    return """
            <div style="font-size: 125%">
                <p>No results found</p>
                <p>Please refine search terms used</p>
            </div>
           """

def search_result(doc_info, index):
    """
    The search_results function displays the results of the query performed by the
    user into the search engine
    
    Args:
        doc_info (list): A list containing document information
        index (int): An integeter containing the ranking
    
    Returns:
        A string containing one result from the search
    """
    return f"""
            <div style="font-size: 125%; display: inline-flex; flex-direction: row">
                <div>
                    {index + 1}. &emsp;
                </div>
                <div>
                    <div>
                        File Path: {doc_info[0]}
                    </div>
                    <div>
                        URL: <a href="{doc_info[1]}" target="_blank">{doc_info[1]}</a>
                    </div>
                </div>
            </div>
            <br>
            <br>
            """

def main():
    """
    The main function initializes our search engine and allows the user to perform searches through the corpus
    provided. From there, a list of search results is provided.
    """
    # Initializes search engine
    init_page_details()
    
    # Creates tile and text input
    st.title('UCI Scholar')
    st.subheader('Top 50 Results')
    input = st.text_input('Review Various UCI Resources',
                          key='search',
                          on_change=reset_pagination, placeholder='Search Here')
    
    # Checks if text has been entered
    if input:
        
        # Performs search and displays result details
        run_search()
        st.write(search_details(), unsafe_allow_html=True)
        
        # Displays results of search done
        if st.session_state.total < 1:
            st.write(search_nil(), unsafe_allow_html=True)
        else:
            start = (st.session_state.page - 1) * 10
            for i in range(0, (start + 10)):
                try:
                    result = st.session_state.results[i]
                except:
                    break
                else:
                    st.write(search_result(result, i), unsafe_allow_html=True)
        
        # Creates button to allow the user to view more results of search
        if (st.session_state.page * 10) < st.session_state.total:
            show_more = st.button('Show More Results', on_click=update_pagination)

if __name__ == '__main__':
    main()
