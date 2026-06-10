"""
Núcleo de conversão md → html → pdf da API.

Espelha o pipeline do scripts/gerar-pdf.py v1.1, mas sem sys.exit/print,
levantando exceções para a camada HTTP traduzir em respostas.

  Etapa 1: Pandoc + templates/cetep.html  →  HTML
  Etapa 2: Playwright/Chromium headless   →  PDF
"""

import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

from api.config import TEMPLATE, MERMAID_TIMEOUT

PANDOC_TIMEOUT = 60  # segundos


class ErroPandoc(Exception):
    """Pandoc retornou erro ao converter o markdown (stderr na mensagem)."""


class ErroChromium(Exception):
    """Falha ao gerar o PDF no Chromium headless."""


def converter(markdown: str, formato: str = "pdf") -> bytes:
    """
    Converte o markdown estruturado (tema CETEP-LNAB) e retorna os bytes
    do resultado. formato: "pdf" ou "html".
    """
    if not TEMPLATE.exists():
        raise ErroPandoc(f"Template não encontrado: {TEMPLATE}")

    with tempfile.TemporaryDirectory(prefix="mkd-pandoc-") as tmp:
        tmpdir = Path(tmp)
        md = tmpdir / "documento.md"
        html = tmpdir / "documento.html"
        pdf = tmpdir / "documento.pdf"

        md.write_text(markdown, encoding="utf-8")

        resultado = subprocess.run(
            [
                "pandoc",
                str(md),
                f"--template={TEMPLATE}",
                "--standalone",
                "-f", "markdown+fenced_divs+link_attributes",
                "-o", str(html),
            ],
            capture_output=True,
            text=True,
            timeout=PANDOC_TIMEOUT,
        )
        if resultado.returncode != 0:
            raise ErroPandoc(resultado.stderr.strip())

        if formato == "html":
            return html.read_bytes()

        _gerar_pdf(html, pdf)
        return pdf.read_bytes()


def _gerar_pdf(html: Path, pdf: Path):
    """Abre o HTML no Chromium headless e imprime em A4 (margens no CSS)."""
    from playwright.sync_api import sync_playwright, Error as ErroPlaywright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            try:
                page = browser.new_page()
                page.goto(html.as_uri())

                # Aguarda o Mermaid.js terminar de renderizar os diagramas
                if MERMAID_TIMEOUT > 0:
                    page.wait_for_timeout(MERMAID_TIMEOUT)

                page.pdf(
                    path=str(pdf),
                    format="A4",
                    print_background=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                )
            finally:
                browser.close()
    except ErroPlaywright as exc:
        raise ErroChromium(str(exc)) from exc


def extrair_titulo(markdown: str) -> str:
    """
    Extrai o campo `titulo` do front matter YAML para nomear o arquivo
    de saída. Retorna um slug ASCII seguro; fallback "documento".
    """
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---", markdown, re.DOTALL)
    if frontmatter:
        campo = re.search(
            r'^titulo:\s*["\']?(.+?)["\']?\s*$',
            frontmatter.group(1),
            re.MULTILINE,
        )
        if campo:
            slug = _slug(campo.group(1))
            if slug:
                return slug
    return "documento"


def _slug(texto: str) -> str:
    sem_acentos = (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    slug = re.sub(r"[^A-Za-z0-9]+", "-", sem_acentos).strip("-")
    return slug[:80]
