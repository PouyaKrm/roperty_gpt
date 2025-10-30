# Use official Python image
FROM python:3.11-slim
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the Django project
COPY . .

# # Expose port 8000
# EXPOSE 8000

# # Default command (can be overridden by docker-compose)
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
