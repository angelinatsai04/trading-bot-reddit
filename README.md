# Trading Bot Reddit

This project is a trading bot that performs sentiment analysis on Reddit posts to then make stock trading decisions. By scraping posts and comments from selected 
subreddits, the bot on Alpaca paper trading based on the average sentiment of mentioned tickers. The logic behind the bot itself is simple: if sentiment is 
positive, the bot will buy one share; if sentiment is negative and shares are being held, the bot will sell a share.

## Table of Contents
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)

## Features
- Scrapes Reddit posts and comments from specified subreddits.
- Performs sentiment analysis using NLTK's VADER Sentiment Intensity Analyzer.
- Executes trades based on the sentiment of mentioned tickers using Alpaca API.
- Stores scraped data and sentiment analysis results in a MySQL database.
- Automated daily execution using cron jobs.

## Technologies Used
- **Python**: Core programming language
- **Docker**: Containerization
- **MySQL**: Database for storing Reddit data and sentiment analysis results
- **NLTK**: Sentiment analysis
- **PRAW**: Python Reddit API Wrapper
- **Alpaca API**: Trading API
- **Lumibot**: Algorithmic trading library

## Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/trading-bot-reddit.git
   cd trading-bot-reddit
   
2. **Create a .env file in the root directory and add the following environment variables:**
   ```env
   DB_HOST=your_db_host
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=your_db_name
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USER_AGENT=your_reddit_user_agent
   ALPACA_API_KEY=your_alpaca_api_key
   ALPACA_API_SECRET=your_alpaca_api_secret
3. **Build and run the Docker containers:**
   ```bash
   docker-compose up --build -d

## Usage
1. **Insert SP500 companies into the database (run once):**
   ```bash
   docker-compose up --build sp500
2. **Run the scraper (run daily):**
   ```bash
   docker-compose up --build scraper
3. **Run the trading bot (run daily after scraper):**
   ```bash
   docker-compose up --build trading_bot

For autonomous trading, set up the following cron jobs:
1. **Open the crontab editor:**
   ```bash
   crontab -e
2. **Add the following cron jobs (example cron job for Pacific Time):**
   ```cron
   # Run scraper every day at 6:00 AM PT
   0 6 * * * cd /path/to/your/project/trading-bot-reddit && docker-compose up --build scraper

   # Run trading bot at 6:35 AM PT (5 minutes after market opens at 9:30 AM EST)
   35 6 * * * cd /path/to/your/project/trading-bot-reddit && docker-compose up --build trading_bot
