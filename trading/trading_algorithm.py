import os
import mysql.connector
import logging
from datetime import datetime, timedelta
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from alpaca_trade_api import REST
from pathlib import Path

# Database credentials from environment variables
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Alpaca API credentials from environment variables
API_KEY = os.getenv('ALPACA_API_KEY')
API_SECRET = os.getenv('ALPACA_API_SECRET')
BASE_URL = "https://paper-api.alpaca.markets/v2"

ALPACA_CREDS = {
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
    "PAPER": True
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedditSentimentTrader(Strategy):
    def initialize(self):
        self.sleeptime = "24H"
        self.last_trade = None
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)
        self.sentiment_threshold = 0.2  # Adjust this threshold as needed
        logger.info("Trader initialized.")

    def position_sizing(self, symbol):
        cash = self.get_cash()
        last_price = self.get_last_price(symbol)
        quantity = 1  # Fixed quantity to 1 share
        logger.info(f"Position sizing for {symbol}: cash={cash}, last_price={last_price}, quantity={quantity}")
        return cash, last_price, quantity

    def get_avg_sentiment(self, ticker):
        cnx = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=3306,
            database=db_name
        )
        cursor = cnx.cursor()
        query = """
        SELECT AVG(sentiment_score)
        FROM tickers_sentiment
        WHERE ticker = %s
        """
        cursor.execute(query, (ticker,))
        result = cursor.fetchone()
        cursor.close()
        cnx.close()
        avg_sentiment = result[0] if result else 0
        logger.info(f"Avg sentiment for {ticker}: {avg_sentiment}")
        return avg_sentiment

    def on_trading_iteration(self):
        cnx = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=3306,
            database=db_name
        )
        cursor = cnx.cursor()
        cursor.execute("SELECT DISTINCT ticker FROM tickers_sentiment")
        tickers = [row[0] for row in cursor.fetchall()]
        cursor.close()
        cnx.close()

        for ticker in tickers:
            avg_sentiment = self.get_avg_sentiment(ticker)
            cash, last_price, quantity = self.position_sizing(ticker)

            if cash > last_price:
                if avg_sentiment > self.sentiment_threshold:
                    if self.last_trade == "sell":
                        self.sell_all()
                    order = self.create_order(
                        ticker,
                        quantity,
                        "buy",
                        type="bracket",
                        take_profit_price=last_price * 1.20,
                        stop_loss_price=last_price * 0.95
                    )
                    self.submit_order(order)
                    logger.info(f"Placed buy order for {ticker}: {order}")
                    self.last_trade = "buy"
                elif avg_sentiment < -self.sentiment_threshold:
                    if self.last_trade == "buy":
                        self.sell_all()
                    order = self.create_order(
                        ticker,
                        quantity,
                        "sell",
                        type="bracket",
                        take_profit_price=last_price * 0.8,
                        stop_loss_price=last_price * 1.05
                    )
                    self.submit_order(order)
                    logger.info(f"Placed sell order for {ticker}: {order}")
                    self.last_trade = "sell"

if __name__ == "__main__":
    broker = Alpaca(ALPACA_CREDS)
    strategy = RedditSentimentTrader(name='RedditSentimentTrader', broker=broker)
    trader = Trader()
    trader.add_strategy(strategy)
    trader.run_all()