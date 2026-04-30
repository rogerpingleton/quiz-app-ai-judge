# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Unbuffered stdout/stderr so prompts appear immediately in `docker run -it`.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    QUIZ_FILE=AI_Engineering_Questions.json \
    QUIZ_TOPIC="AI Engineering"

WORKDIR /app

# Install Python deps first so the layer is cached when only source changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the repo (.dockerignore keeps secrets and junk out).
COPY . .

# Make entrypoint executable and drop to a non-root user.
RUN chmod +x entrypoint.sh && \
    useradd --create-home --uid 1000 quiz && \
    chown -R quiz:quiz /app
USER quiz

ENTRYPOINT ["./entrypoint.sh"]
