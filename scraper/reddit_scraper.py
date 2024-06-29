import os
import time
import praw
import datetime
import mysql.connector
from mysql.connector import errorcode

# Database credentials from environment variables
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Connect to Reddit
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

def clear_table():
    try:
        cnx = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=3306,
            database=db_name
        )
        cursor = cnx.cursor()

        # Clear the table before insertion
        cursor.execute("DELETE FROM reddit_posts")

        cursor.close()
        cnx.close()
        print("Database table 'reddit_posts' truncated.")

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")

def save_to_db(entity_id, text, created_at):
    try:
        cnx = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=3306,
            database=db_name
        )
        cursor = cnx.cursor()

        # Escape the text to avoid SQL issues
        text = text.replace('\n', ' ').replace('\r', '').strip()
        
        add_post = ("INSERT INTO reddit_posts "
                    "(entity_id, body, created_at) "
                    "VALUES (%s, %s, %s)")
        data_post = (entity_id, text, created_at)

        cursor.execute(add_post, data_post)
        cnx.commit()
        cursor.close()
        cnx.close()
        print(f"Saved to DB: {entity_id}, {text[:50]}")

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return

def is_relevant_content(body):
    irrelevant_patterns = [
        "User Report",
        "[**Join WSB Discord**](http://discord.gg/wsbverse)",
        "[deleted]"
        # Add more patterns as needed
    ]
    for pattern in irrelevant_patterns:
        if pattern in body:
            return False
    return True

def extract_and_save(comment_or_post):
    if isinstance(comment_or_post, praw.models.Comment):
        entity_id = comment_or_post.id
        body = comment_or_post.body
        created_at = datetime.datetime.utcfromtimestamp(comment_or_post.created_utc)
    elif isinstance(comment_or_post, praw.models.Submission):
        entity_id = comment_or_post.id
        body = comment_or_post.title + " " + comment_or_post.selftext
        created_at = datetime.datetime.utcfromtimestamp(comment_or_post.created_utc)
    else:
        return

    if not is_relevant_content(body):
        print(f"Irrelevant content filtered out: {body[:10]}...")
        return

    save_to_db(entity_id, body, created_at)

def scrape_posts(subreddit_name, processed_count):
    subreddit = reddit.subreddit(subreddit_name)
    current_time_utc = datetime.datetime.utcnow()
    seven_days_ago_utc = current_time_utc - datetime.timedelta(days=7)

    recent_posts = []
    for submission in subreddit.new(limit=100):  # Adjust the limit as needed to find the top 5 from the last 7 days
        submission_created_utc = datetime.datetime.utcfromtimestamp(submission.created_utc)
        if submission_created_utc >= seven_days_ago_utc:
            recent_posts.append(submission)

    # Sort recent posts by score and take the top 5
    top_posts = sorted(recent_posts, key=lambda post: post.score, reverse=True)[:5]

    for submission in top_posts:
        extract_and_save(submission)
        processed_count += 1
        submission.comments.replace_more(limit=15)
        comments_sorted = sorted(submission.comments, key=lambda comment: comment.score, reverse=True)
        top_comments = comments_sorted[:10]
        for comment in top_comments:
            extract_and_save(comment)
            processed_count += 1

# Clear the database table 'reddit_posts' before starting scraping
clear_table()

subreddits = ['stocks', 'wallstreetbets', 'investing']
processed_count = 0

while processed_count < 165:
    for subreddit in subreddits:
        try:
            scrape_posts(subreddit, processed_count)
        except Exception as e:
            print(f'Error scraping {subreddit}: {e}')
    
    time.sleep(60)  # Sleep for 60 seconds before the next scrape

print("Finished scraping")

# import os
# import time
# import praw
# import re
# import datetime
# import spacy
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from fuzzywuzzy import fuzz
# import mysql.connector
# from mysql.connector import errorcode

# # Database credentials from environment variables
# db_host = os.getenv('DB_HOST')
# db_user = os.getenv('DB_USER')
# db_password = os.getenv('DB_PASSWORD')
# db_name = os.getenv('DB_NAME')

# def load_valid_tickers():
#     try:
#         cnx = mysql.connector.connect(
#             host=db_host,
#             user=db_user,
#             password=db_password,
#             port=3306,
#             database=db_name
#         )
#         cursor = cnx.cursor()

#         query = "SELECT company_name, ticker FROM sp500_companies"
#         cursor.execute(query)
        
#         company_ticker_dict = {}
#         ticker_set = set()

#         # Fetch all rows from the executed query
#         rows = cursor.fetchall()

#         if rows:
#             for row in rows:
#                 company_name, ticker = row
#                 company_ticker_dict[company_name] = ticker
#                 short_name = company_name.split(' ')[0]
#                 company_ticker_dict[short_name] = ticker
#                 ticker_set.add(ticker)
#         else:
#             print("No rows fetched from the database.")

#         cursor.close()
#         cnx.close()

#         print("Successfully connected to MySQL server!")
#         return company_ticker_dict, ticker_set
    
#     except mysql.connector.Error as err:
#         if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
#             print("Something is wrong with your user name or password")
#         elif err.errno == errorcode.ER_BAD_DB_ERROR:
#             print("Database does not exist")
#         else:
#             print(f"Error: {err}")
#         return {}, set()

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

# processed_count = 0  # Counter for processed posts and comments
# max_processed_entries = 165  # Limit for processed entries (5 posts + 50 comments per subreddit * 3 subreddits)

# def fuzzy_match_company_name(text):
#     matches = []
#     for company_name, ticker in valid_tickers.items():
#         ratio = fuzz.partial_ratio(company_name.lower(), text.lower())
#         if ratio > 80:
#             matches.append((company_name, ticker))
#     return matches

# def save_to_db(entity_id, text, tickers):
#     global processed_count
#     try:
#         cnx = mysql.connector.connect(
#             host=db_host,
#             user=db_user,
#             password=db_password,
#             port=3306,
#             database=db_name
#         )
#         cursor = cnx.cursor()

#         # Escape the text to avoid SQL issues
#         text = text.replace('\n', ' ').replace('\r', '').strip()
        
#         add_post = ("INSERT INTO reddit_posts "
#                     "(entity_id, body, tickers, created_at) "
#                     "VALUES (%s, %s, %s, %s)")
#         data_post = (entity_id, text, ','.join(tickers), datetime.datetime.utcnow())

#         cursor.execute(add_post, data_post)
#         cnx.commit()
#         cursor.close()
#         cnx.close()
#         processed_count += 1  # Increment the counter
#         print(f"Saved to DB: {entity_id}, {text[:50]}, {tickers}")

#     except mysql.connector.Error as err:
#         print(f"Database Error: {err}")
#         return

# def is_relevant_content(body):
#     irrelevant_patterns = [
#         "User Report",
#         "[**Join WSB Discord**](http://discord.gg/wsbverse)",
#         "[deleted]"
#         # Add more patterns as needed
#     ]
#     for pattern in irrelevant_patterns:
#         if pattern in body:
#             return False
#     return True

# def extract_and_print_tickers(comment_or_post):
#     global processed_count
#     if isinstance(comment_or_post, praw.models.Comment):
#         entity_id = comment_or_post.id
#         body = comment_or_post.body
#     elif isinstance(comment_or_post, praw.models.Submission):
#         entity_id = comment_or_post.id
#         body = comment_or_post.title + " " + comment_or_post.selftext
#     else:
#         return

#     if not is_relevant_content(body):
#         print(f"Filtered out irrelevant content: {body[:100]}...")
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
#     global processed_count
#     subreddit = reddit.subreddit(subreddit_name)
#     current_time_utc = datetime.datetime.utcnow()
#     seven_days_ago_utc = current_time_utc - datetime.timedelta(days=7)

#     top_posts = []
#     for submission in subreddit.new(limit=5):
#         submission_created_utc = datetime.datetime.utcfromtimestamp(submission.created_utc)
#         if submission_created_utc >= seven_days_ago_utc:
#             top_posts.append(submission)

#     for submission in top_posts:
#         if processed_count >= max_processed_entries:
#             return
#         print(f'Scraping post: {submission.title}')
#         extract_and_print_tickers(submission)
#         print(f'Scraping comments for post: {submission.title}')
#         submission.comments.replace_more(limit=20)
#         comments_sorted = sorted(submission.comments, key=lambda comment: comment.score, reverse=True)
#         top_comments = comments_sorted[:10]
#         for comment in top_comments:
#             extract_and_print_tickers(comment)

# subreddits = ['stocks', 'wallstreetbets', 'investing']

# while True:
#     with ThreadPoolExecutor(max_workers=len(subreddits)) as executor:
#         futures = [executor.submit(scrape_posts, subreddit) for subreddit in subreddits]
#         for future in as_completed(futures):
#             try:
#                 future.result()
#             except Exception as e:
#                 print(f'Error: {e}')
    
#     if processed_count >= max_processed_entries:
#         print(f"Reached limit of {processed_count} processed entries. Exiting.")
#         break
    
#     time.sleep(60)  # Sleep for 60 seconds before the next scrape