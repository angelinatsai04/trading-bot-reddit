# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for mysqlclient
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libmariadb-dev-compat \
    libmariadb-dev \
    pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . . 

# Command to run the scraper script
CMD ["python", "reddit_scraper.py"]
