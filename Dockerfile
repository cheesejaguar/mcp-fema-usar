FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install runtime dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py ./
COPY resources ./resources

# Expose the port used by the application
EXPOSE 8000

# Command to run the application
CMD ["python", "server.py"]
