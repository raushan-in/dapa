FROM python:3.12.3-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port
EXPOSE 8080

# Start the backend app
CMD ["python", "src/main.py"]