FROM python:3.12.7-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=120
WORKDIR /app
COPY requirements.txt pyproject.toml alembic.ini ./
RUN pip install --no-cache-dir --retries=8 --timeout=120 --index-url https://pypi.org/simple -r requirements.txt \
    && useradd --create-home --uid 10001 appuser
COPY fleetguard_db ./fleetguard_db
COPY migrations ./migrations
COPY main.py .
RUN pip install --no-cache-dir --no-deps .
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]