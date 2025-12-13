FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY ./app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app/ .

# Create download directory
RUN mkdir -p /app/downloads

# Set environment variables from .env file (if exists)
ENV PYTHONPATH=/app

# Make port 80 available to the world outside this container
EXPOSE 80

# Run the application
CMD ["python", "bot.py"]