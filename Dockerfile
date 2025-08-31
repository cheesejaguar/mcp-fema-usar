FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy pyproject.toml and README.md for package installation
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

# Copy application files
COPY fema_usar_mcp ./fema_usar_mcp
COPY app ./app

# Expose the port used by the application  
EXPOSE 8000

# Command to run the HTTP application
CMD ["python", "-m", "app.main"]
