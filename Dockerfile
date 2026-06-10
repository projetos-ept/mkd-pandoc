FROM python:3.12-slim-bookworm

# Pandoc (etapa 1 do pipeline)
RUN apt-get update \
    && apt-get install -y --no-install-recommends pandoc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependências Python + Chromium headless (etapa 2 do pipeline)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY templates/ templates/
COPY api/ api/

# API_KEY (obrigatória), SML_STORAGE_* e MERMAID_TIMEOUT via -e no docker run
ENV MERMAID_TIMEOUT=2500

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
