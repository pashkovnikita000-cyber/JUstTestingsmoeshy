FROM python:3.12-slim

WORKDIR /app

# Install dependencies first — layer cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY bot/ ./bot/

# Create data directory for SQLite volume mount
# Create non-root user and transfer ownership
RUN mkdir -p /app/data \
    && useradd -m -u 1000 botuser \
    && chown -R botuser:botuser /app

USER botuser

# Long-polling bot — no inbound ports needed
CMD ["python", "-m", "bot.main"]
