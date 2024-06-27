# Use a base image with build tools
FROM python:3.9

RUN pip install mysql-connector-python

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

# Copy the application code
COPY reddit_scraper.py .
COPY sp500.py .

CMD ["python", "./reddit_scraper.py"]
