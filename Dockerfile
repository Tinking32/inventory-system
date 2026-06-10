FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies (psycopg2-binary needs no system libs)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Render uses its own health check via the healthCheckPath in render.yaml
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
