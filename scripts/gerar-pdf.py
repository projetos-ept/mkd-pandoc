#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  MKD-Project — CETEP-LNAB                                       ║
║  gerar-pdf.py v1.1                                               ║
║                                                                  ║
║  Converte um arquivo .md no tema livro didático CETEP-LNAB.     ║
║  Etapa 1: Pandoc  →  .html  (com template cetep.html)           ║
║  Etapa 2: Playwright/Chromium  →  .pdf                          ║
║                                                                  ║
║  Uso:                                                            ║
║    python gerar-pdf.py documento.md                             ║
║    python gerar-pdf.py documento.md --so html                   ║
║    python gerar-pdf.py documento.md --saida D:\outra\pasta      ║
║    python gerar-pdf.py --ajuda                                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import subprocess
import argparse
import platform
from pathlib import Path

# ──────────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO — ajuste os caminhos se necessário
# ──────────────────────────────────────────────────────────────────

# Pasta raiz do projeto (onde este script está)
BASE = Path(__file__).parent.resolve()

# Template Pandoc
TEMPLATE = BASE / "cetep.html"

# Pasta de saída padrão (HTMLs e PDFs gerados)
SAIDA_PADRAO = BASE / "saida"

# Tempo de espera para o Mermaid.js renderizar os diagramas (ms)
# Aumente para 4000 se os diagramas aparecerem em branco
MERMAID_TIMEOUT = 2500

# Caminho customizado do Chromium (deixe None para usar o padrão do Playwright)
# Exemplo Windows: r"D:\playwright-browsers"
# Exemplo Linux:   "/opt/playwright-browsers"
PLAYWRIGHT_BROWSERS_PATH = None

# ──────────────────────────────────────────────────────────────────


def verificar_dependencias():
    """Verifica se Pandoc está instalado e acessível."""
    try:
        resultado = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True, text=True
        )
        if resultado.returncode != 0:
            raise FileNotFoundError
        versao = resultado.stdout.splitlines()[0]
        print(f"  Pandoc: {versao}")
    except FileNotFoundError:
        print("✗ Pandoc não encontrado.")
        print("  Windows: choco install pandoc")
        print("  Linux:   sudo apt install pandoc")
        sys.exit(1)

    try:
        from playwright.sync_api import sync_playwright  # noqa
        print("  Playwright: OK")
    except ImportError:
        print("✗ Playwright não encontrado.")
        print("  Instale com: python -m pip install playwright")
        print("  Depois:      python -m playwright install chromium")
        sys.exit(1)


def configurar_playwright_path():
    """
    Define a variável de ambiente PLAYWRIGHT_BROWSERS_PATH se configurada.
    Permite instalar o Chromium em disco diferente (ex: D: no Windows).
    """
    if PLAYWRIGHT_BROWSERS_PATH:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(PLAYWRIGHT_BROWSERS_PATH)
        print(f"  Browsers: {PLAYWRIGHT_BROWSERS_PATH}")


def etapa_pandoc(md: Path, html_out: Path):
    """
    Etapa 1: Pandoc converte o .md em HTML usando o template cetep.html.

    Flags usadas:
      --template     aplica o template visual cetep.html
      --standalone   gera HTML completo (com <head>, não fragmento)
      -f markdown+fenced_divs+link_attributes
                     habilita blocos ::: e atributos de imagem {width=Xpx}
    """
    if not TEMPLATE.exists():
        print(f"✗ Template não encontrado: {TEMPLATE}")
        print("  Coloque o cetep.html na mesma pasta que este script.")
        sys.exit(1)

    print(f"\n→ Etapa 1/2 — Pandoc: {md.name}")

    cmd = [
        "pandoc",
        str(md),
        f"--template={TEMPLATE}",
        "--standalone",
        "-f", "markdown+fenced_divs+link_attributes",
        "-o", str(html_out)
    ]

    resultado = subprocess.run(cmd, capture_output=True, text=True)

    if resultado.returncode != 0:
        print(f"✗ Erro no Pandoc:\n{resultado.stderr}")
        sys.exit(1)

    tamanho = html_out.stat().st_size / 1024
    print(f"✓ HTML gerado: {html_out}  ({tamanho:.1f} KB)")


def etapa_pdf(html_out: Path, pdf_out: Path):
    """
    Etapa 2: Playwright abre o HTML no Chromium headless e gera o PDF.

    - Aguarda MERMAID_TIMEOUT ms para o Mermaid.js renderizar os diagramas
    - Imprime em A4 sem margens (as margens estão no CSS via @page)
    - print_background=True garante cores e fundos no PDF
    """
    from playwright.sync_api import sync_playwright

    print(f"\n→ Etapa 2/2 — Playwright: gerando PDF...")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Carrega o HTML pelo protocolo file://
        page.goto(html_out.as_uri())

        # Aguarda o Mermaid.js terminar de renderizar os diagramas
        if MERMAID_TIMEOUT > 0:
            page.wait_for_timeout(MERMAID_TIMEOUT)

        page.pdf(
            path=str(pdf_out),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )

        browser.close()

    tamanho = pdf_out.stat().st_size / 1024
    print(f"✓ PDF gerado:  {pdf_out}  ({tamanho:.1f} KB)")


def abrir_pdf(pdf_out: Path):
    """Abre o PDF no visualizador padrão do sistema operacional."""
    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(str(pdf_out))
        elif sistema == "Darwin":  # macOS
            subprocess.Popen(["open", str(pdf_out)])
        else:  # Linux
            subprocess.Popen(["xdg-open", str(pdf_out)])
    except Exception:
        pass  # Se não conseguir abrir, não é erro crítico


def processar(md_path: str, saida: Path, modo: str, abrir: bool):
    """
    Fluxo principal: valida o arquivo, cria as pastas e executa as etapas.

    Parâmetros:
        md_path  caminho do arquivo .md (pode ser relativo)
        saida    pasta de destino para HTML e PDF
        modo     "ambos" | "html" | "pdf"
        abrir    True para abrir o PDF automaticamente ao final
    """
    md = Path(md_path).resolve()

    if not md.exists():
        print(f"✗ Arquivo não encontrado: {md}")
        sys.exit(1)

    if md.suffix.lower() != ".md":
        print(f"✗ O arquivo deve ser um .md: {md.name}")
        sys.exit(1)

    # Garante que a pasta de saída existe
    saida.mkdir(parents=True, exist_ok=True)

    html_out = saida / (md.stem + ".html")
    pdf_out  = saida / (md.stem + ".pdf")

    print(f"\n{'='*60}")
    print(f"  Arquivo:  {md.name}")
    print(f"  Saída:    {saida}")
    print(f"  Modo:     {modo}")
    print(f"{'='*60}")

    # Etapa 1 — sempre necessária (PDF também precisa do HTML)
    etapa_pandoc(md, html_out)

    # Etapa 2 — apenas se o modo incluir PDF
    if modo in ("ambos", "pdf"):
        etapa_pdf(html_out, pdf_out)

        print(f"\n{'='*60}")
        print(f"✓ Concluído!")
        print(f"  HTML → {html_out}")
        print(f"  PDF  → {pdf_out}")
        print(f"{'='*60}\n")

        if abrir:
            abrir_pdf(pdf_out)
    else:
        print(f"\n{'='*60}")
        print(f"✓ Concluído!")
        print(f"  HTML → {html_out}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="gerar-pdf",
        description="MKD-Project CETEP-LNAB — Converte .md em HTML e PDF estilizados.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python gerar-pdf.py Cap01-Parasitologia.md
  python gerar-pdf.py Cap01-Parasitologia.md --so html
  python gerar-pdf.py Cap01-Parasitologia.md --saida D:\\Documentos\\pdfs
  python gerar-pdf.py Cap01-Parasitologia.md --nao-abrir
        """
    )

    parser.add_argument(
        "arquivo",
        nargs="?",
        help="Caminho do arquivo .md a converter"
    )
    parser.add_argument(
        "--so",
        choices=["html", "pdf", "ambos"],
        default="ambos",
        metavar="FORMATO",
        help="Gerar apenas 'html', apenas 'pdf', ou 'ambos' (padrão: ambos)"
    )
    parser.add_argument(
        "--saida",
        default=str(SAIDA_PADRAO),
        metavar="PASTA",
        help=f"Pasta de saída (padrão: {SAIDA_PADRAO})"
    )
    parser.add_argument(
        "--nao-abrir",
        action="store_true",
        help="Não abrir o PDF automaticamente ao final"
    )
    parser.add_argument(
        "--verificar",
        action="store_true",
        help="Apenas verifica se as dependências estão instaladas"
    )
    parser.add_argument(
        "--ajuda",
        action="help",
        help="Exibe esta mensagem de ajuda"
    )

    args = parser.parse_args()

    print("\n  MKD-Project — CETEP-LNAB  |  gerar-pdf.py v1.1")
    print(f"  Sistema: {platform.system()} {platform.release()}")
    print(f"  Python:  {platform.python_version()}")

    # Configura path do Chromium antes de qualquer coisa
    configurar_playwright_path()

    # Modo de verificação de dependências
    if args.verificar:
        print("\n→ Verificando dependências...\n")
        verificar_dependencias()
        print("\n✓ Todas as dependências OK.\n")
        return

    if not args.arquivo:
        parser.print_help()
        sys.exit(0)

    # Verifica dependências antes de processar
    verificar_dependencias()

    processar(
        md_path=args.arquivo,
        saida=Path(args.saida),
        modo=args.so,
        abrir=not args.nao_abrir
    )


if __name__ == "__main__":
    main()
