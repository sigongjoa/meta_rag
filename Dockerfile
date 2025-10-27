# 1. Base Image
FROM python:3.10-slim

# 2. Set working directory
WORKDIR /app

# 3. Install dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install uvicorn to run the server
RUN pip install --no-cache-dir uvicorn

# 4. Copy application code
COPY . .

# 5. Expose the port the app runs on
EXPOSE 8000

# 6. Run the application
# The --host 0.0.0.0 is important to make the server accessible from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
