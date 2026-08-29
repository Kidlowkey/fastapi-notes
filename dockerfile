# --- Base Image ---
FROM python:3.12-slim

# Don't buffer stdout/stderr (so logs show immediately), don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /fastapi-notes

# Install dependecies first, so this layer is cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt

# Now copy the rest of the source code
COPY . .

# Render (and most platforms) inject the port to bind to via $PORT
# Default to 8000 for local 'docker run'
ENV PORT=8000
EXPOSE 8000

# Run as non-root user for basic security hygiene
RUN useradd -m appuser
USER appuser

# Use sheel form so $PORT gets expanded at container start
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
