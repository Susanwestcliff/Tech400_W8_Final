from flask import Flask, render_template, request
import os
import re
from collections import defaultdict

app = Flask(__name__)

# Preprocessing function
def clean_text(text):
    return re.findall(r'\b\w+\b', text.lower())

# Load text files into a dictionary
def fetch_documents(directory_path):
    documents = {}
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory {directory_path} does not exist.")
    
    for doc_file in os.listdir(directory_path):
        if doc_file.endswith('.txt'):
            file_path = os.path.join(directory_path, doc_file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    documents[doc_file] = clean_text(f.read())
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    return documents

# Calculate term frequencies and document frequencies
def calculate_frequencies(docs):
    total_docs = len(docs)
    term_in_docs = defaultdict(int)
    term_frequency = defaultdict(lambda: defaultdict(int))

    for document, terms in docs.items():
        unique_terms = set(terms)
        for term in terms:
            term_frequency[document][term] += 1
        for term in unique_terms:
            term_in_docs[term] += 1

    return term_frequency, term_in_docs, total_docs

# Compute BIM-based relevance scores
def get_relevance_score(query_terms, term_frequency, term_in_docs, total_docs):
    relevance_scores = {}
    for doc_name in term_frequency:
        probability_score = 0.5
        for term in query_terms:
            term_freq = term_frequency[doc_name].get(term, 0)
            doc_freq = term_in_docs.get(term, 0)

            # Adjust calculations to avoid divide by zero errors
            if doc_freq == total_docs:
                prob_non_relevant = 1e-10  # Small value to avoid division by zero
            else:
                prob_relevant = (term_freq + 1) / (sum(term_frequency[doc_name].values()) + len(term_in_docs))
                prob_non_relevant = (doc_freq + 1) / (total_docs - doc_freq + len(term_in_docs))

            probability_score *= (prob_relevant / prob_non_relevant)
        relevance_scores[doc_name] = probability_score
    return relevance_scores

# Core function to retrieve documents based on user input query
def search_documents(directory_path, user_query):
    # Load documents
    documents = fetch_documents(directory_path)

    # Calculate frequencies
    term_frequency, term_in_docs, total_docs = calculate_frequencies(documents)

    # Process user query
    query_words = clean_text(user_query)

    # Handle the case where the query is empty
    if not query_words:
        return []

    # Get relevance scores for the user query
    scores = get_relevance_score(query_words, term_frequency, term_in_docs, total_docs)

    # Sort documents by relevance score
    sorted_docs = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return sorted_docs

# Flask route for the homepage
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get the user query from the form
        user_query = request.form['query']
        
        # Handle empty queries
        if not user_query.strip():
            return render_template('index.html', query=user_query, results=[])
        
        # Perform search
        doc_directory = './final_data'  # Ensure this path is correct
        try:
            results = search_documents(doc_directory, user_query)
        except FileNotFoundError as e:
            return render_template('index.html', query=user_query, error=str(e), results=None)
        
        # Pass results to the HTML template
        return render_template('index.html', query=user_query, results=results)
    
    return render_template('index.html', query=None, results=None)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
