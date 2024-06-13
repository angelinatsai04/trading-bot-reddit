import os
from dotenv import load_dotenv
import praw
import re
import random
import datetime
import pandas as pd


# Load environment variables from .env file
load_dotenv()

# connect to reddit 
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

# Load the list of valid stock tickers from a file
def load_valid_tickers(file_path):
    with open(file_path, 'r') as file:
        tickers = file.read().splitlines()
    return set(tickers)

# valid_tickers = load_valid_tickers('output.txt')

tickers = pd.read_html(
    'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]

valid_tickers = set(tickers['Symbol'])

# Define the regex pattern to find potential stock tickers (2-4 uppercase letters)
ticker_pattern = re.compile(r'\b[A-Z]{2,4}\b')

# Dictionary to track processed tickers for each comment ID
processed_comments = {}

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
    
    tickers = re.findall(ticker_pattern, body)
    unique_tickers = set()
    for ticker in tickers:
        if ticker in valid_tickers and ticker not in processed_comments[entity_id]:
            # print(f"Entity ID: {entity_id}, Ticker: {ticker}")
            processed_comments[entity_id].add(ticker)
            unique_tickers.add(ticker)

    if unique_tickers:
        # Print the entire entity again with unique tickers
        print(f"Original Entity: {body}")
        print(f"Unique Ticklers: {unique_tickers}")
        print("-" * 80)

def scrape_posts(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.hot(limit=10):  # Limiting to top 10 hot posts
        print(f'Scraping post: {submission.title}')
        extract_and_print_tickers(submission)

def scrape_comments(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.hot(limit=10):  # Limiting to top 10 hot posts
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            extract_and_print_tickers(comment)

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