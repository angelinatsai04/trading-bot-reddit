import os
import time
from dotenv import load_dotenv
import praw
import re
import datetime
import pandas as pd
import spacy
from fuzzywuzzy import fuzz
import mysql.connector
from mysql.connector import errorcode

# Load environment variables from .env file
load_dotenv()

def load_valid_tickers():
    try:
        cnx = mysql.connector.connect(
            user='your_username',
            password='your_password',
            host='your_host',
            database='stock_data'
        )
        cursor = cnx.cursor()

        query = "SELECT company_name, ticker FROM sp500_companies"
        cursor.execute(query)

        company_ticker_dict = {}
        for (company_name, ticker) in cursor:
            company_ticker_dict[company_name] = ticker
            short_name = company_name.split(' ')[0]
            company_ticker_dict[short_name] = ticker

        cursor.close()
        cnx.close()

        ticker_set = set(company_ticker_dict.values())
        return company_ticker_dict, ticker_set

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        return {}, set()

# Connect to reddit
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

# Load the list of valid stock tickers and company names from MySQL database
valid_tickers, ticker_set = load_valid_tickers()

# Define the regex pattern to find potential stock tickers (2-4 uppercase letters)
ticker_pattern = re.compile(r'\b[A-Z]{2,4}\b')

# Load spaCy for NLP processing
nlp = spacy.load('en_core_web_sm')

# Dictionary to track processed tickers for each comment ID
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

def scrape_posts(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    current_time_utc = datetime.datetime.utcnow()
    seven_days_ago_utc = current_time_utc - datetime.timedelta(days=7)

    top_posts = []
    for submission in subreddit.new(limit=None):
        submission_created_utc = datetime.datetime.utcfromtimestamp(submission.created_utc)
        if submission_created_utc >= seven_days_ago_utc:
            top_posts.append(submission)

    top_posts_sorted = sorted(top_posts, key=lambda x: x.score, reverse=True)[:50]

    for submission in top_posts_sorted:
        print(f'Scraping post: {submission.title}')
        extract_and_print_tickers(submission)

def scrape_comments(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    current_time_utc = datetime.datetime.utcnow()
    seven_days_ago_utc = current_time_utc - datetime.timedelta(days=7)

    top_posts = []
    for submission in subreddit.new(limit=None):
        submission_created_utc = datetime.datetime.utcfromtimestamp(submission.created_utc)
        if submission_created_utc >= seven_days_ago_utc:
            top_posts.append(submission)

    top_posts_sorted = sorted(top_posts, key=lambda x: x.score, reverse=True)[:50]

    for submission in top_posts_sorted:
        print(f'Scraping comments for post: {submission.title}')
        submission.comments.replace_more(limit=None)
        comments_sorted = sorted(submission.comments, key=lambda comment: comment.score, reverse=True)
        top_comments = comments_sorted[:10]
        for comment in top_comments:
            extract_and_print_tickers(comment)

subreddits = ['stocks', 'wallstreetbets', 'investing']

while True:
    for subreddit in subreddits:
        print(f'Starting to scrape subreddit: {subreddit} at {datetime.datetime.now()}')
        scrape_posts(subreddit)
        scrape_comments(subreddit)
        print(f'Finished scraping subreddit: {subreddit} at {datetime.datetime.now()}')
    time.sleep(60)  # Sleep for 60 seconds before the next scrape