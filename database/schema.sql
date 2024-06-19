-- Create the sp500_companies table first with a unique constraint on ticker
CREATE TABLE sp500_companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    ticker VARCHAR(10) NOT NULL UNIQUE
);

-- Create the reddit_posts table
CREATE TABLE reddit_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    sentiment_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the trades table with the foreign key constraint
CREATE TABLE trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    trade_action VARCHAR(10) NOT NULL,
    trade_volume INT NOT NULL,
    trade_price FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker) REFERENCES sp500_companies(ticker)
);
