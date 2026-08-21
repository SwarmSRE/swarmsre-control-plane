# Build the React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm install
COPY ui/ ./
RUN npm run build

# Build the Python FastAPI Backend (using uv)
FROM python:3.14-slim-bookworm AS backend-builder
WORKDIR /app

# Install uv
RUN pip install uv

# Install dependencies using uv
COPY pyproject.toml .
# We don't have a uv.lock but uv can install from pyproject.toml
RUN uv pip install --system .

# Final Production Image
FROM python:3.14-slim-bookworm
WORKDIR /app

# Install runtime dependencies (e.g., for psycopg if needed, though psycopg[binary] usually suffices)
# RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=backend-builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend code
COPY api/ api/
COPY agents/ agents/
COPY core/ core/
COPY policies/ policies/
COPY main.py .

# Copy compiled frontend from frontend-builder
COPY --from=frontend-builder /app/ui/dist ui/dist

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
