"""
Configuração da API via variáveis de ambiente.

Variáveis:
  API_KEY               chave exigida no header X-API-Key (obrigatória)
  SML_STORAGE_ENDPOINT  base da SML Storage API
  SML_STORAGE_API_KEY   chave x-api-key da SML Storage (só p/ rotas com imagens)
  SML_PROJETO           nome do projeto no SML Storage
  MERMAID_TIMEOUT       espera (ms) para o Mermaid.js renderizar antes do PDF
"""

import os
from pathlib import Path

# Raiz do repositório (api/ está um nível abaixo)
BASE = Path(__file__).parent.parent.resolve()

# Template Pandoc do tema CETEP-LNAB
TEMPLATE = BASE / "templates" / "cetep.html"

API_KEY = os.environ.get("API_KEY", "")

SML_STORAGE_ENDPOINT = os.environ.get(
    "SML_STORAGE_ENDPOINT",
    "https://us-east1-sml-storage.cloudfunctions.net",
).rstrip("/")
SML_STORAGE_API_KEY = os.environ.get("SML_STORAGE_API_KEY", "")
SML_PROJETO = os.environ.get("SML_PROJETO", "mkd-pandoc")

MERMAID_TIMEOUT = int(os.environ.get("MERMAID_TIMEOUT", "2500"))
