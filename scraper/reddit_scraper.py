# import os
# import mysql.connector

# db_host = os.getenv('DB_HOST')
# db_user = os.getenv('DB_USER')
# db_password = os.getenv('DB_PASSWORD')
# db_name = os.getenv('DB_NAME')

# print(f"DB_HOST: {db_host}")
# print(f"DB_USER: {db_user}")
# print(f"DB_PASSWORD: {db_password}")
# print(f"DB_NAME: {db_name}")

# try:
#     cnx = mysql.connector.connect(
#         host=db_host,
#         user=db_user,
#         password=db_password,
#         port=3306,
#         database=db_name
#     )
#     print("Successfully connected to MySQL server!")
#     cnx.close()
# except mysql.connector.Error as err:
#     print(f"Error connecting to MySQL: {err}")
#     raise
import os
import time
# from dotenv import load_dotenv
import praw
import re
import datetime
import pandas as pd
import spacy
from fuzzywuzzy import fuzz
import mysql.connector
from mysql.connector import errorcode

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
def load_valid_tickers():
    try:
        cnx = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=3306,
            database=db_name
        )
        cursor = cnx.cursor()

        query = "SELECT company_name, ticker FROM sp500_companies"
        cursor.execute(query)

        company_ticker_dict = {}
        ticker_set = set()

        for (company_name, ticker) in cursor:
            company_ticker_dict[company_name] = ticker
            short_name = company_name.split(' ')[0]
            company_ticker_dict[short_name] = ticker
            ticker_set.add(ticker)

        cursor.close()
        cnx.close()

        print("Successfully connected to MySQL server!")
        return company_ticker_dict, ticker_set
    
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(f"Error: {err}")
        return {}, set()

# Example usage
company_ticker_dict, ticker_set = load_valid_tickers()

# Now you can use company_ticker_dict and ticker_set in your application
print("Company-Ticker Dictionary:")
print(company_ticker_dict)
print("\nTicker Set:")
print(ticker_set)

# # Assume data is retrieved and stored in a list of tuples (company_name, ticker)
# data_to_insert = [
#     ('Company A', 'A_TICKER'),
#     ('Company B', 'B_TICKER'),
#     # Add more data as needed
# ]

# def insert_data_into_sp500_companies(data):
#     try:
#         cnx = mysql.connector.connect(
#             host=db_host,
#             user=db_user,
#             password=db_password,
#             port=3306,
#             database=db_name
#         )
#         cursor = cnx.cursor()

#         # Prepare SQL statement for insertion
#         sql = "INSERT INTO sp500_companies (company_name, ticker) VALUES (%s, %s)"

#         # Execute insertion for each data tuple
#         for company_name, ticker in data:
#             cursor.execute(sql, (company_name, ticker))
        
#         # Commit changes to the database
#         cnx.commit()
#         print(f"{cursor.rowcount} rows inserted into sp500_companies")

#         cursor.close()
#         cnx.close()

#     except mysql.connector.Error as err:
#         print(f"Error: {err}")
#         cnx.rollback()  # Rollback changes if any error occurs

# # Call function to insert data
# insert_data_into_sp500_companies(data_to_insert)

# print("here")

# # Load environment variables from .env file
# # load_dotenv()
# db_host = os.getenv('DB_HOST')
# db_user = os.getenv('DB_USER')
# db_password = os.getenv('DB_PASSWORD')
# db_name = os.getenv('DB_NAME')


# # Connect to Reddit
# reddit = praw.Reddit(
#     client_id=os.getenv('REDDIT_CLIENT_ID'),
#     client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
#     user_agent=os.getenv('REDDIT_USER_AGENT')
# )

# # Load the list of valid stock tickers and company names from MySQL database
# valid_tickers, ticker_set = load_valid_tickers()

# # Define the regex pattern to find potential stock tickers (2-4 uppercase letters)
# ticker_pattern = re.compile(r'\b[A-Z]{2,4}\b')

# # Load spaCy for NLP processing
# nlp = spacy.load('en_core_web_sm')

# # Dictionary to track processed tickers for each comment ID
# processed_comments = {}

# def fuzzy_match_company_name(text):
#     matches = []
#     for company_name, ticker in valid_tickers.items():
#         ratio = fuzz.partial_ratio(company_name.lower(), text.lower())
#         if ratio > 80:
#             matches.append((company_name, ticker))
#     return matches

# def save_to_db(entity_id, text, tickers):
#     try:
#         cnx = mysql.connector.connect(
#             user=os.getenv('MYSQL_USER'),
#             password=os.getenv('MYSQL_PASSWORD'),
#             host=os.getenv('MYSQL_HOST'),
#             database='trading_bot'
#         )
#         cursor = cnx.cursor()

#         add_post = ("INSERT INTO reddit_posts "
#                     "(entity_id, text, tickers) "
#                     "VALUES (%s, %s, %s)")
#         data_post = (entity_id, text, ','.join(tickers))

#         cursor.execute(add_post, data_post)
#         cnx.commit()

#         cursor.close()
#         cnx.close()
#     except mysql.connector.Error as err:
#         print(f"Error: {err}")
#         return

# def extract_and_print_tickers(comment_or_post):
#     if isinstance(comment_or_post, praw.models.Comment):
#         entity_id = comment_or_post.id
#         body = comment_or_post.body
#     elif isinstance(comment_or_post, praw.models.Submission):
#         entity_id = comment_or_post.id
#         body = comment_or_post.title + " " + comment_or_post.selftext
#     else:
#         return

#     if entity_id not in processed_comments:
#         processed_comments[entity_id] = set()

#     unique_tickers = set()
#     tickers = re.findall(ticker_pattern, body)
#     for ticker in tickers:
#         if ticker in ticker_set and ticker not in processed_comments[entity_id]:
#             processed_comments[entity_id].add(ticker)
#             unique_tickers.add(ticker)

#     doc = nlp(body)
#     for ent in doc.ents:
#         if ent.label_ == 'ORG':
#             matches = fuzzy_match_company_name(ent.text)
#             for _, ticker in matches:
#                 if ticker not in processed_comments[entity_id]:
#                     processed_comments[entity_id].add(ticker)
#                     unique_tickers.add(ticker)

#     if unique_tickers:
#         print(f"Original Entity: {body}")
#         print(f"Unique Tickers: {unique_tickers}")
#         print("-" * 80)
#         save_to_db(entity_id, body, unique_tickers)

# def scrape_posts(subreddit_name):
#     subreddit = reddit.subreddit(subreddit_name)
#     current_time_utc = datetime.datetime.utcnow()
#     seven_days_ago_utc = current_time_utc - datetime.timedelta(days=7)

#     top_posts = []
#     for submission in subreddit.new(limit=5):  # Limiting to 5 posts for testing
#         submission_created_utc = datetime.datetime.utcfromtimestamp(submission.created_utc)
#         if submission_created_utc >= seven_days_ago_utc:
#             top_posts.append(submission)

#     top_posts_sorted = sorted(top_posts, key=lambda x: x.score, reverse=True)[:5]  # Limiting to 5 posts

#     for submission in top_posts_sorted:
#         print(f'Scraping post: {submission.title}')
#         extract_and_print_tickers(submission)

# def scrape_comments(subreddit_name):
#     subreddit = reddit.subreddit(subreddit_name)
#     current_time_utc = datetime.datetime.utcnow()
#     seven_days_ago_utc = current_time_utc - datetime.timedelta(days=7)

#     top_posts = []
#     for submission in subreddit.new(limit=5):  # Limiting to 5 posts for testing
#         submission_created_utc = datetime.datetime.utcfromtimestamp(submission.created_utc)
#         if submission_created_utc >= seven_days_ago_utc:
#             top_posts.append(submission)

#     top_posts_sorted = sorted(top_posts, key=lambda x: x.score, reverse=True)[:5]  # Limiting to 5 posts

#     for submission in top_posts_sorted:
#         print(f'Scraping comments for post: {submission.title}')
#         submission.comments.replace_more(limit=None)
#         comments_sorted = sorted(submission.comments, key=lambda comment: comment.score, reverse=True)
#         top_comments = comments_sorted[:3]  # Limiting to 3 comments per post
#         for comment in top_comments:
#             extract_and_print_tickers(comment)
# # def scrape_posts(subreddit_name):
# #     subreddit = reddit.subreddit(subreddit_name)
# #     current_time_utc = datetime.datetime.utcnow()
# #     seven_days_ago_utc = current_time_utc - datetime.timedelta(days=7)

# #     top_posts = []
# #     for submission in subreddit.new(limit=None):
# #         submission_created_utc = datetime.datetime.utcfromtimestamp(submission.created_utc)
# #         if submission_created_utc >= seven_days_ago_utc:
# #             top_posts.append(submission)

# #     top_posts_sorted = sorted(top_posts, key=lambda x: x.score, reverse=True)[:50]

# #     for submission in top_posts_sorted:
# #         print(f'Scraping post: {submission.title}')
# #         extract_and_print_tickers(submission)

# # def scrape_comments(subreddit_name):
#     subreddit = reddit.subreddit(subreddit_name)
#     current_time_utc = datetime.datetime.utcnow()
#     seven_days_ago_utc = current_time_utc - datetime.timedelta(days=7)

#     top_posts = []
#     for submission in subreddit.new(limit=None):
#         submission_created_utc = datetime.datetime.utcfromtimestamp(submission.created_utc)
#         if submission_created_utc >= seven_days_ago_utc:
#             top_posts.append(submission)

#     top_posts_sorted = sorted(top_posts, key=lambda x: x.score, reverse=True)[:50]

#     for submission in top_posts_sorted:
#         print(f'Scraping comments for post: {submission.title}')
#         submission.comments.replace_more(limit=None)
#         comments_sorted = sorted(submission.comments, key=lambda comment: comment.score, reverse=True)
#         top_comments = comments_sorted[:10]
#         for comment in top_comments:
#             extract_and_print_tickers(comment)

# subreddits = ['stocks', 'wallstreetbets', 'investing']

# while True:
#     for subreddit in subreddits:
#         print(f'Starting to scrape subreddit: {subreddit} at {datetime.datetime.now()}')
#         scrape_posts(subreddit)
#         scrape_comments(subreddit)
#         print(f'Finished scraping subreddit: {subreddit} at {datetime.datetime.now()}')
#     time.sleep(60)  # Sleep for 60 seconds before the next scrape