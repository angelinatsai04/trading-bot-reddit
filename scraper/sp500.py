import os
import mysql.connector
from mysql.connector import errorcode
import yfinance as yf

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Function to fetch S&P 500 companies
def fetch_sp500_companies():
    try:
        sp500 = yf.download('^GSPC', period='1d')
        sp500_tickers = sp500['^GSPC']['Constituents'].tolist()
        sp500_companies = [(ticker.info['longName'], ticker.ticker) for ticker in sp500_tickers]
        return sp500_companies
    except Exception as e:
        print(f"Error fetching S&P 500 companies: {e}")
        return []

# Function to insert S&P 500 companies into MySQL database
def insert_sp500_companies(companies):
    try:
        cnx = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=3306,
            database=db_name
        )
        cursor = cnx.cursor()

        # Truncate table if needed
        cursor.execute("DELETE FROM sp500_companies")

        # Insert each company into the table
        for company_name, ticker in companies:
            insert_query = "INSERT INTO sp500_companies (company_name, ticker) VALUES (%s, %s)"
            cursor.execute(insert_query, (company_name, ticker))
        
        cnx.commit()
        print(f"{len(companies)} rows inserted into sp500_companies")
        
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(f"Error: {err}")
    finally:
        cursor.close()
        cnx.close()

# Example usage
if __name__ == "__main__":
    db_host = "database"  # Docker service name for the database
    db_user = "root"
    db_password = "rootpassword"
    db_name = "db"
    
    companies = fetch_sp500_companies()
    print("Fetched S&P 500 companies:", companies)  # Debugging output
    insert_sp500_companies(companies)