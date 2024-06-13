import pandas as pd

# Fetch data from Wikipedia page
data = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')

# Assuming the first table [0] contains the S&P 500 companies data
sp500_companies_df = data[0]

# Extract company names and ticker symbols
company_names = sp500_companies_df['Security']
tickers = sp500_companies_df['Symbol']

# Create a dictionary with company names as keys and tickers as values
company_ticker_dict = dict(zip(company_names, tickers))

# Save the dictionary to a text file
output_file = 'company_tickers.txt'
with open(output_file, 'w') as f:
    for company, ticker in company_ticker_dict.items():
        f.write(f"{company}: {ticker}\n")

print(f"Company names and tickers saved to {output_file}")