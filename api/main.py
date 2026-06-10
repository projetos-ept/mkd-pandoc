"""
MKD-Project — CETEP-LNAB | API HTTP

Converte markdown estruturado (tema livro didático CETEP-LNAB) em PDF/HTML.

    uvicorn api.main:app --host 0.0.0.0 --port 8000

Rotas:
    GET  /saude                  verificação de dependências (sem auth)
    POST /converter              JSON {"markdown": "...", "formato": "pdf"|"html"}
    POST /converter/com-imagens  multipart: markdown/arquivo + imagem1..N

Autenticação: header X-API-Key comparado com a variável de ambiente API_KEY.
"""

import secrets
import subprocess
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from api import config, imagens
from api.armazenamento import ErroArmazenamento
from api.conversor import ErroChromium, ErroPandoc, converter, extrair_titulo


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    if not config.API_KEY:
        raise RuntimeError(
            "Variável de ambiente API_KEY não definida. "
            "Defina-a antes de iniciar a API (ex: API_KEY=minha-chave uvicorn ...)."
        )
    yield


app = FastAPI(
    title="MKD-Pandoc API",
    description="Converte .md estruturado (tema CETEP-LNAB) em PDF/HTML.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)


def verificar_chave(x_api_key: str = Header(default="")):
    if not secrets.compare_digest(x_api_key, config.API_KEY):
        raise HTTPException(status_code=401, detail="Chave de API inválida")


@app.exception_handler(ErroPandoc)
async def _erro_pandoc(request: Request, exc: ErroPandoc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Erro no Pandoc ao converter o markdown",
                 "stderr": str(exc)},
    )


@app.exception_handler(ErroChromium)
async def _erro_chromium(request: Request, exc: ErroChromium):
    return JSONResponse(
        status_code=500,
        content={"detail": "Falha ao gerar o PDF no Chromium", "erro": str(exc)},
    )


@app.exception_handler(ErroArmazenamento)
async def _erro_armazenamento(request: Request, exc: ErroArmazenamento):
    return JSONResponse(
        status_code=502,
        content={"detail": "Falha no upload para o SML Storage", "erro": str(exc)},
    )


@app.exception_handler(imagens.ErroImagens)
async def _erro_imagens(request: Request, exc: imagens.ErroImagens):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


class RequisicaoConversao(BaseModel):
    markdown: str = Field(min_length=1, description="Conteúdo do arquivo .md")
    formato: Literal["pdf", "html"] = "pdf"


def _resposta(conteudo: bytes, markdown: str, formato: str) -> Response:
    nome = f"{extrair_titulo(markdown)}.{formato}"
    media_type = "application/pdf" if formato == "pdf" else "text/html; charset=utf-8"
    return Response(
        content=conteudo,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@app.get("/saude")
def saude():
    """Verifica Pandoc, template e Chromium do Playwright."""
    problemas = []

    try:
        pandoc = subprocess.run(
            ["pandoc", "--version"], capture_output=True, text=True, timeout=15
        )
        versao_pandoc = pandoc.stdout.splitlines()[0] if pandoc.returncode == 0 else None
        if not versao_pandoc:
            problemas.append("pandoc retornou erro")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        versao_pandoc = None
        problemas.append("pandoc não encontrado")

    if not config.TEMPLATE.exists():
        problemas.append(f"template não encontrado: {config.TEMPLATE}")

    chromium = False
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            chromium = bool(p.chromium.executable_path)
    except Exception:
        problemas.append("chromium do Playwright não instalado")

    corpo = {
        "status": "ok" if not problemas else "erro",
        "pandoc": versao_pandoc,
        "chromium": chromium,
        "problemas": problemas,
    }
    if problemas:
        return JSONResponse(status_code=503, content=corpo)
    return corpo


@app.post(
    "/converter",
    dependencies=[Depends(verificar_chave)],
    responses={200: {"content": {"application/pdf": {}}}},
)
def converter_markdown(req: RequisicaoConversao):
    """Converte markdown (imagens só por URL remota) e retorna PDF/HTML."""
    conteudo = converter(req.markdown, req.formato)
    return _resposta(conteudo, req.markdown, req.formato)


@app.post(
    "/converter/com-imagens",
    dependencies=[Depends(verificar_chave)],
    responses={200: {"content": {"application/pdf": {}}}},
)
async def converter_com_imagens(request: Request):
    """
    Converte markdown com imagens locais (multipart/form-data):

    - campo `markdown` (texto) OU `arquivo` (upload do .md)
    - campos `imagem1`, `imagem2`, ... referenciados no markdown
      como {{imagem1}}, {{imagem2}}, ...
    - campo opcional `formato`: "pdf" (padrão) ou "html"
    """
    form = await request.form()

    markdown = form.get("markdown")
    arquivo = form.get("arquivo")
    if not markdown and arquivo is not None and hasattr(arquivo, "read"):
        markdown = (await arquivo.read()).decode("utf-8")
    if not markdown or not isinstance(markdown, str):
        raise HTTPException(
            status_code=422,
            detail="Envie o campo 'markdown' (texto) ou 'arquivo' (upload do .md)",
        )

    formato = form.get("formato") or "pdf"
    if formato not in ("pdf", "html"):
        raise HTTPException(status_code=422, detail="formato deve ser 'pdf' ou 'html'")

    if not config.SML_STORAGE_API_KEY and any(
        chave.startswith("imagem") for chave in form
    ):
        raise HTTPException(
            status_code=503,
            detail="SML_STORAGE_API_KEY não configurada no servidor",
        )

    arquivos: dict[str, tuple[str, bytes]] = {}
    for chave, valor in form.multi_items():
        if imagens.PADRAO_PLACEHOLDER.fullmatch("{{" + chave + "}}") and hasattr(valor, "read"):
            arquivos[chave] = (valor.filename or chave, await valor.read())

    imagens.validar(markdown, arquivos)

    # Uploads + Pandoc + Chromium são bloqueantes → threadpool
    def _processar() -> tuple[bytes, str]:
        md_final = imagens.substituir(markdown, arquivos)
        return converter(md_final, formato), md_final

    conteudo, md_final = await run_in_threadpool(_processar)
    return _resposta(conteudo, md_final, formato)
