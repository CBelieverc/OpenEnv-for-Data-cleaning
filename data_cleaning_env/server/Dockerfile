FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY __init__.py .
COPY models.py .
COPY client.py .
COPY inference.py .
COPY openenv.yaml .
COPY server/ server/

# Install dependencies from pyproject.toml
RUN pip install --no-cache-dir .

# Set PYTHONPATH so imports work correctly
ENV PYTHONPATH="/app:$PYTHONPATH"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
