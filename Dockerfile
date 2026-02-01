FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY clawsearch/ ./clawsearch/

# Create non-root user
RUN useradd -m -u 1000 clawsearch && chown -R clawsearch:clawsearch /app
USER clawsearch

# Run
EXPOSE 8000
CMD ["uvicorn", "clawsearch.main:app", "--host", "0.0.0.0", "--port", "8000"]
