import os
import mysql.connector
import logging
from datetime import datetime, timedelta
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from alpaca_trade_api import REST
from alpaca_trade_api.rest import APIError

# Database credentials from environment variables
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Alpaca API credentials from environment variables
API_KEY = os.getenv('ALPACA_API_KEY')
API_SECRET = os.getenv('ALPACA_API_SECRET')
BASE_URL = "https://paper-api.alpaca.markets"

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
        self.sleeptime = "5S"
        self.last_trade = None
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)
        self.sentiment_threshold = 0.2  # Adjust this threshold as needed
        self.tickers_processed = set()  # To keep track of processed tickers
        self.stop_flag = False  # Stop flag
        logger.info("Trader initialized.")

    def get_cash(self):
        try:
            account = self.api.get_account()
            cash = float(account.cash)
            logger.info(f"Cash position: {cash}")
            return cash
        except Exception as e:
            logger.error(f"Error retrieving cash position: {e}")
            return 0.0  # Default to 0.0 if there's an error

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

    def get_position(self, ticker):
        try:
            position = self.api.get_position(ticker)
            logger.info(f"Position for {ticker}: {position}")
            return position
        except APIError as e:
            if e.status_code == 404:
                # logger.info(f"No existing position for {ticker}")
                return None
            else:
                raise

    def on_trading_iteration(self):
        if self.stop_flag:
            return
    
        logger.info("Starting trading iteration.")
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
            if ticker == "USD" or ticker in self.tickers_processed:
                continue  # Skip USD and already processed tickers

            avg_sentiment = self.get_avg_sentiment(ticker)
            cash, last_price, quantity = self.position_sizing(ticker)
            position = self.get_position(ticker)

            logger.info(f"Evaluating ticker {ticker} with avg_sentiment={avg_sentiment}, cash={cash}, last_price={last_price}, position={position}")

            if avg_sentiment > self.sentiment_threshold:
                if cash > last_price:
                    order = self.create_order(
                        ticker,
                        quantity,
                        "buy",
                        type="market"
                    )
                    self.submit_order(order)
                    logger.info(f"Placed buy order for {ticker}: {order}")
                    self.last_trade = "buy"
            elif avg_sentiment < -self.sentiment_threshold:
                if position and int(position.qty) > 0:
                    order = self.create_order(
                        ticker,
                        quantity,
                        "sell",
                        type="market"
                    )
                    self.submit_order(order)
                    logger.info(f"Placed sell order for {ticker}: {order}")
                    self.last_trade = "sell"

            self.tickers_processed.add(ticker)

        # Stop the trader after processing all tickers
        if len(self.tickers_processed) == len(tickers):
            logger.info("All tickers processed, stopping trader.")
            self.stop_trading()

    def stop_trading(self):
        self.stop_flag = True
        logger.info("Stopping trading...")
        os._exit(0)
        # exit(0)  # Exit the program


if __name__ == "__main__":
    broker = Alpaca(ALPACA_CREDS)
    strategy = RedditSentimentTrader(name='RedditSentimentTrader', broker=broker)
    trader = Trader()
    trader.add_strategy(strategy)
    trader.run_all()