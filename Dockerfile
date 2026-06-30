FROM python:3.12-slim

# All app files will live under /app inside the container.
WORKDIR /app

# Python runtime flags for cleaner container behavior.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy dependency list first to maximize Docker layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project source into the image.
COPY . .

# Flask/Gunicorn listens on port 5000.
EXPOSE 5000

# Run the app with Gunicorn in production mode.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
