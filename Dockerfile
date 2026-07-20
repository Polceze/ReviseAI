FROM python:3.11-slim

WORKDIR /app

# Install Python deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

ENV PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=5000

EXPOSE 5000

RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
# Runs app.py directly (not gunicorn) because table creation in this codebase
# lives under `if __name__ == "__main__"` in app.py — running it directly is
# what triggers the automatic schema setup on first boot.
CMD ["python", "app.py"]
