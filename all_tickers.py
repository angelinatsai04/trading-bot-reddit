import pandas as pd

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

# Save DataFrame to CSV
sp500_data.to_csv('sp500_companies.csv', index=False)

print("sp500_companies.csv file created successfully.")
