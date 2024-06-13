import os
import time
from dotenv import load_dotenv
import praw
import re
import datetime
import pandas as pd
import spacy
from fuzzywuzzy import fuzz


# Load environment variables from .env file
load_dotenv()

# connect to reddit 
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

# Load the list of valid stock tickers and company names from Wikipedia
def load_valid_tickers():
    # Fetch data from Wikipedia page
    data = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')

    # Assuming the first table [0] contains the S&P 500 companies data
    sp500_companies_df = data[0]

    # Extract company names and ticker symbols
    company_names = sp500_companies_df['Security'].values.tolist()
    tickers = sp500_companies_df['Symbol'].values.tolist()

    # Create a dictionary with company names and ticker symbols
    company_ticker_dict = {}
    for name, ticker in zip(company_names, tickers):
        company_ticker_dict[name] = ticker
        # Add common abbreviations or variations
        # Example: Apple Inc. -> Apple (for recognizing "Apple")
        if ' ' in name:
            short_name = name.split(' ')[0]
            company_ticker_dict[short_name] = ticker
        # Add more mappings as needed for other companies

    return company_ticker_dict, set(tickers)

valid_tickers, ticker_set = load_valid_tickers()

# Define the regex pattern to find potential stock tickers (2-4 uppercase letters)
ticker_pattern = re.compile(r'\b[A-Z]{2,4}\b')

# Load spaCy for NLP processing
nlp = spacy.load('en_core_web_sm')

# Dictionary to track processed tickers for each comment ID
processed_comments = {}

def fuzzy_match_company_name(text):
    """ Fuzzy match company names to find potential ticker symbols. """
    matches = []
    for company_name, ticker in valid_tickers.items():
        # Compute fuzzy ratio between the company name and text
        ratio = fuzz.partial_ratio(company_name.lower(), text.lower())
        if ratio > 80:  # Adjust threshold as needed based on your data
            matches.append((company_name, ticker))
    return matches

def extract_and_print_tickers(comment_or_post):
    """ Extract and print potential stock tickers from a comment or post. """
    if isinstance(comment_or_post, praw.models.Comment):
        entity_id = comment_or_post.id
        body = comment_or_post.body
    elif isinstance(comment_or_post, praw.models.Submission):
        entity_id = comment_or_post.id
        body = comment_or_post.title + " " + comment_or_post.selftext
    else:
        return
    
    if entity_id not in processed_comments:
        processed_comments[entity_id] = set()  # Initialize set for this entity ID

    # Check for ticker symbols directly
    unique_tickers = set()
    tickers = re.findall(ticker_pattern, body)
    for ticker in tickers:
        if ticker in ticker_set and ticker not in processed_comments[entity_id]:
            processed_comments[entity_id].add(ticker)
            unique_tickers.add(ticker)
    
    # Use spaCy for entity recognition and fuzzy matching for company names
    doc = nlp(body)
    for ent in doc.ents:
        if ent.label_ == 'ORG':  # Assuming company names are recognized as organizations
            matches = fuzzy_match_company_name(ent.text)
            for _, ticker in matches:
                if ticker not in processed_comments[entity_id]:
                    processed_comments[entity_id].add(ticker)
                    unique_tickers.add(ticker)

    if unique_tickers:
        # Print the entire entity again with unique tickers
        print(f"Original Entity: {body}")
        print(f"Unique Tickers: {unique_tickers}")
        print("-" * 80)

def scrape_posts(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    current_time_utc = datetime.datetime.utcnow()
    seven_days_ago_utc = current_time_utc - datetime.timedelta(days=7)
    
    for submission in subreddit.hot(limit=None):  # Scraping all hot posts
        submission_created_utc = datetime.datetime.utcfromtimestamp(submission.created_utc)
        
        if submission_created_utc >= seven_days_ago_utc:
            print(f'Scraping post: {submission.title}')
            extract_and_print_tickers(submission)
        else:
            break  # Assuming posts are ordered by hotness, stop when we reach older posts

def scrape_comments(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    current_time_utc = datetime.datetime.utcnow()
    seven_days_ago_utc = current_time_utc - datetime.timedelta(days=7)
    for submission in subreddit.hot(limit=None):  # Scraping all hot posts
        submission_created_utc = datetime.datetime.utcfromtimestamp(submission.created_utc)
        
        if submission_created_utc >= seven_days_ago_utc:
            print(f'Scraping comments for post: {submission.title}')
            submission.comments.replace_more(limit=None)  # Retrieve all comments
            comments_sorted = sorted(submission.comments, key=lambda comment: comment.score, reverse=True)
            top_comments = comments_sorted[:10]  # Limit to top 10 comments
            
            for comment in top_comments:
                extract_and_print_tickers(comment)
        else:
            break  # Stop processing older posts

# Define the list of subreddits to scrape
subreddits = ['stocks', 'wallstreetbets', 'investing']  # Add more subreddits as needed

# Main loop to continuously scrape posts and comments
while True:
    for subreddit in subreddits:
        print(f'Starting to scrape subreddit: {subreddit} at {datetime.datetime.now()}')
        scrape_posts(subreddit)
        scrape_comments(subreddit)  # Optional: Uncomment if you want to scrape comments as well
        print(f'Finished scraping subreddit: {subreddit} at {datetime.datetime.now()}')
    
    # Sleep to avoid hitting Reddit's rate limits
    time.sleep(60)  # Sleep for 60 seconds before the next scrape