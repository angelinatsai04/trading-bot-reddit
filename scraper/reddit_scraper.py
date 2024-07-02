import os
import time
import praw
import datetime
import re
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
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

def get_db_connection():
    try:
        cnx = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=3306,
            database=db_name
        )
        return cnx
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None

def close_db_connection(cnx):
    try:
        if cnx:
            cnx.close()
    except mysql.connector.Error as err:
        print(f"Error closing connection: {err}")

def initialize_db():
    cnx = get_db_connection()
    if not cnx:
        return
    try:
        cursor = cnx.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reddit_posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                entity_id VARCHAR(20) NOT NULL,
                body TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                INDEX idx_entity_id (entity_id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickers_sentiment (
                id INT AUTO_INCREMENT PRIMARY KEY,
                entity_id VARCHAR(20) NOT NULL,
                ticker VARCHAR(10) NOT NULL,
                sentiment_score FLOAT DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_entity_id (entity_id),
                INDEX idx_ticker (ticker)
            );
        """)
        cnx.commit()
        print("Database tables initialized.")
    except mysql.connector.Error as err:
        print(f"Database Initialization Error: {err}")
    finally:
        cursor.close()
        close_db_connection(cnx)

def clear_tables():
    cnx = get_db_connection()
    if not cnx:
        return
    try:
        cursor = cnx.cursor()
        # Clear the tables before insertion
        cursor.execute("DELETE FROM reddit_posts")
        cursor.execute("DELETE FROM tickers_sentiment")
        cnx.commit()
        print("Database tables 'reddit_posts' and 'tickers_sentiment' cleared.")
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        cursor.close()
        close_db_connection(cnx)

def load_valid_tickers():
    cnx = get_db_connection()
    if not cnx:
        return {}, set()
    try:
        cursor = cnx.cursor()
        query = "SELECT company_name, ticker FROM sp500_companies"
        cursor.execute(query)
        
        company_ticker_dict = {}
        ticker_set = set()
        # Fetch all rows from the executed query
        rows = cursor.fetchall()

        if rows:
            for row in rows:
                company_name, ticker = row
                company_ticker_dict[company_name.upper()] = ticker
                short_name = company_name.split(' ')[0].upper()
                company_ticker_dict[short_name] = ticker
                ticker_set.add(ticker)
        else:
            print("No rows fetched from the database.")
        return company_ticker_dict, ticker_set
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(f"Error: {err}")
        return {}, set()
    finally:
        cursor.close()
        close_db_connection(cnx)

def save_to_db(entity_id, text, created_at):
    cnx = get_db_connection()
    if not cnx:
        return
    try:
        cursor = cnx.cursor()
        # Escape the text to avoid SQL issues
        text = text.replace('\n', ' ').replace('\r', '').strip()
        
        add_post = ("INSERT INTO reddit_posts "
                    "(entity_id, body, created_at) "
                    "VALUES (%s, %s, %s)")
        data_post = (entity_id, text, created_at)

        cursor.execute(add_post, data_post)
        cnx.commit()
        
        print(f"Saved to DB: {entity_id}")

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return
    finally:
        cursor.close()
        close_db_connection(cnx)

# Initialize VADER SentimentIntensityAnalyzer
sia = SIA()

def save_tickers_to_db(entity_id, tickers, sentiment_score):
    cnx = get_db_connection()
    if not cnx:
        return
    try:
        cursor = cnx.cursor()
        
        add_ticker = ("INSERT INTO tickers_sentiment "
                      "(entity_id, ticker, sentiment_score) "
                      "VALUES (%s, %s, %s)")
        
        for ticker in tickers:
            data_ticker = (entity_id, ticker, sentiment_score)
            cursor.execute(add_ticker, data_ticker)
        
        cnx.commit()
        print(f"Saved tickers and sentiment for entity: {entity_id}")

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return
    finally:
        cursor.close()
        close_db_connection(cnx)

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

def extract_and_print_tickers(comment_or_post):
    # Load valid tickers and company names
    company_ticker_dict, ticker_set = load_valid_tickers()
    
    # Extract text from comment or post
    if isinstance(comment_or_post, praw.models.Comment):
        text = comment_or_post.body
    elif isinstance(comment_or_post, praw.models.Submission):
        text = comment_or_post.title + " " + comment_or_post.selftext
    else:
        return set()

    # Normalize text to uppercase for uniformity
    text = text.upper()

    # Regular expression to find potential ticker symbols (usually uppercase letters, max 5 characters)
    potential_tickers = set(re.findall(r'\b[A-Z]{1,5}\b', text))

    # Validate potential tickers against the valid ticker set
    valid_tickers = {ticker for ticker in potential_tickers if ticker in ticker_set}

    # Check for company names and map them to tickers
    words = text.split()
    for word in words:
        if word in company_ticker_dict:
            valid_tickers.add(company_ticker_dict[word])

    # Additional check for variations of company names (like short names)
    for company_name in company_ticker_dict.keys():
        if company_name in text:
            valid_tickers.add(company_ticker_dict[company_name])
    
    return valid_tickers

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
    tickers = extract_and_print_tickers(comment_or_post)
    
    if tickers:
        sentiment_score = sia.polarity_scores(body)['compound']
        save_tickers_to_db(entity_id, tickers, sentiment_score)

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
        processed_count += 1
        extract_and_save(submission)
        submission.comments.replace_more(limit=15)
        comments_sorted = sorted(submission.comments, key=lambda comment: comment.score, reverse=True)
        top_comments = comments_sorted[:10]
        for comment in top_comments:
            processed_count += 1
            extract_and_save(comment)
    return processed_count

# Initialize the database tables
initialize_db()

# Clear the database table 'reddit_posts' before starting scraping
clear_tables()

subreddits = ['stocks', 'wallstreetbets', 'investing']
processed_count = 0

while processed_count < 165:
    for subreddit in subreddits:
        print(processed_count)
        try:
            processed_count = scrape_posts(subreddit, processed_count)
        except Exception as e:
            print(f'Error scraping {subreddit}: {e}')
    
    time.sleep(60)  # Sleep for 60 seconds before the next scrape

print("Finished scraping")
exit(0)