FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Create gunicorn run directory
RUN mkdir -p /app/run

# Run migrations and start gunicorn
CMD ["sh", "-c", "python manage.py migrate && gunicorn mobilepoint.wsgi:application --bind 0.0.0.0:8000 --workers 4 --worker-class sync"]
