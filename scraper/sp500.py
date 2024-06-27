import csv
import pandas as pd
import os
import mysql.connector
from mysql.connector import errorcode

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Fetch data from Wikipedia page
data = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')

# Assuming the first table [0] contains the S&P 500 companies data
sp500_companies_df = data[0]

# Extract company names and ticker symbols
company_names = sp500_companies_df['Security']
tickers = sp500_companies_df['Symbol']

# Create a DataFrame with company names and tickers
sp500_data = pd.DataFrame({
    'company_name': company_names,
    'ticker': tickers
})

# Function to read S&P 500 companies from DataFrame
def read_sp500_companies_from_dataframe(df):
    companies = []
    for _, row in df.iterrows():
        companies.append((row['company_name'], row['ticker']))
    return companies

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

# Execution
if __name__ == "__main__":
    db_host = "database"  # Docker service name for the database
    db_user = "root"
    db_password = "rootpassword"
    db_name = "db"
    
    # Read data from DataFrame
    companies = read_sp500_companies_from_dataframe(sp500_data)
    print("Fetched S&P 500 companies:", companies)  # Debugging output
    
    # Insert data into database
    insert_sp500_companies(companies)