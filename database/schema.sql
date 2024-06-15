CREATE TABLE reddit_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    sentiment_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_symbol VARCHAR(10) NOT NULL,
    trade_action VARCHAR(10) NOT NULL,
    trade_volume INT NOT NULL,
    trade_price FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
