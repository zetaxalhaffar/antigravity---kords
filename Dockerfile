# Use the official Playwright Python image which includes browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements first to cache dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium only (since we only use Chromium/Chrome)
RUN playwright install chromium

# Copy the rest of the application code
COPY . .

# Create output directory for processed files
RUN mkdir -p output_files

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
