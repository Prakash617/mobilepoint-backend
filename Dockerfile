############################
# STAGE 1: Builder
############################
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt


############################
# STAGE 2: Runtime
############################
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Create non-root user
RUN addgroup --system app && adduser --system --group app

WORKDIR /app

# Runtime dependencies only
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        netcat-openbsd \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps from wheels
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir /wheels/* \
    && pip install gunicorn

# Copy project
COPY . .

# Static files directory & permissions
RUN mkdir -p /app/public/static \
    && chown -R app:app /app \
    && chmod 755 /app/public/static

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER app

EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "mobilepoint.wsgi:application", "-w", "2", "--threads", "2", "--timeout", "60", "-b", "0.0.0.0:8001"]
