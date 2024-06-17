import os
import time
from dotenv import load_dotenv
import praw
import re
import spacy
from fuzzywuzzy import fuzz
import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
load_dotenv()

# Connect to Reddit
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

# Load the list of valid stock tickers and company names from Wikipedia
def load_valid_tickers():
    data = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    sp500_companies_df = data[0]
    company_names = sp500_companies_df['Security'].values.tolist()
    tickers = sp500_companies_df['Symbol'].values.tolist()
    company_ticker_dict = {name: ticker for name, ticker in zip(company_names, tickers)}
    for name, ticker in zip(company_names, tickers):
        short_name = name.split(' ')[0]
        company_ticker_dict[short_name] = ticker
    return company_ticker_dict, set(tickers)

valid_tickers, ticker_set = load_valid_tickers()
ticker_pattern = re.compile(r'\b[A-Z]{2,4}\b')
nlp = spacy.load('en_core_web_sm')
processed_comments = {}

def fuzzy_match_company_name(text):
    matches = []
    for company_name, ticker in valid_tickers.items():
        ratio = fuzz.partial_ratio(company_name.lower(), text.lower())
        if ratio > 80:
            matches.append((company_name, ticker))
    return matches

def extract_and_print_tickers(comment_or_post):
    if isinstance(comment_or_post, praw.models.Comment):
        entity_id = comment_or_post.id
        body = comment_or_post.body
    elif isinstance(comment_or_post, praw.models.Submission):
        entity_id = comment_or_post.id
        body = comment_or_post.title + " " + comment_or_post.selftext
    else:
        return
    
    if entity_id not in processed_comments:
        processed_comments[entity_id] = set()

    unique_tickers = set()
    tickers = re.findall(ticker_pattern, body)
    for ticker in tickers:
        if ticker in ticker_set and ticker not in processed_comments[entity_id]:
            processed_comments[entity_id].add(ticker)
            unique_tickers.add(ticker)
    
    doc = nlp(body)
    for ent in doc.ents:
        if ent.label_ == 'ORG':
            matches = fuzzy_match_company_name(ent.text)
            for _, ticker in matches:
                if ticker not in processed_comments[entity_id]:
                    processed_comments[entity_id].add(ticker)
                    unique_tickers.add(ticker)

    if unique_tickers:
        print(f"Original Entity: {body}")
        print(f"Unique Tickers: {unique_tickers}")
        print("-" * 80)

def get_top_posts(subreddit_name, time_filter='week', limit=50):
    subreddit = reddit.subreddit(subreddit_name)
    return list(subreddit.top(time_filter=time_filter, limit=limit))

def get_top_comments(submission, limit=10):
    submission.comments.replace_more(limit=None)
    comments_sorted = sorted(submission.comments, key=lambda comment: comment.score, reverse=True)
    return comments_sorted[:limit]

def scrape_subreddit(subreddit_name):
    print(f'Starting to scrape subreddit: {subreddit_name} at {datetime.datetime.now()}')
    top_posts = get_top_posts(subreddit_name)
    
    for submission in top_posts:
        extract_and_print_tickers(submission)
        top_comments = get_top_comments(submission)
        for comment in top_comments:
            extract_and_print_tickers(comment)
    
    print(f'Finished scraping subreddit: {subreddit_name} at {datetime.datetime.now()}')

subreddits = ['stocks', 'wallstreetbets', 'investing']

while True:
    with ThreadPoolExecutor(max_workers=len(subreddits)) as executor:
        futures = [executor.submit(scrape_subreddit, subreddit) for subreddit in subreddits]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f'Error: {e}')
    time.sleep(60)  # Sleep for 60 seconds before the next scrape