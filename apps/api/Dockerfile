FROM python:3.11-slim

WORKDIR /workspace

# Copy the py2dataiku library first (enables layer caching)
COPY py2dataiku/ ./py2dataiku/
COPY pyproject.toml setup.cfg* ./

# Install the py2dataiku library in editable mode
RUN pip install --no-cache-dir -e "." || pip install --no-cache-dir .

# Copy and install the API package
COPY apps/api/pyproject.toml ./apps/api/pyproject.toml
COPY apps/api/app/ ./apps/api/app/

WORKDIR /workspace/apps/api
RUN pip install --no-cache-dir -e "." || pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
