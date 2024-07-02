-- Create the sp500_companies table first with a unique constraint on ticker
CREATE TABLE sp500_companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    ticker VARCHAR(10) NOT NULL UNIQUE
);

-- Create table for storing Reddit posts and comments
CREATE TABLE reddit_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_id VARCHAR(20) NOT NULL,
    body TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_entity_id (entity_id)
);

-- Create table for storing aggregated ticker sentiment data
CREATE TABLE tickers_sentiment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_id VARCHAR(20) NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    sentiment_score FLOAT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity_id (entity_id),
    INDEX idx_ticker (ticker)
);