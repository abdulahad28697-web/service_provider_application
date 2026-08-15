# ServiceHub AI backend image.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /backend

# Install dependencies first (leverages Docker layer caching).
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application source.
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
