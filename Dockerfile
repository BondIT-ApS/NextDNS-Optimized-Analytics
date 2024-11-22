# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables to ensure Python runs in an unbuffered and consistent mode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the application source code to the working directory
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the API port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
