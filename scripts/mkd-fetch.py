#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mkd-fetch.py — Busca arquivos .md no GitHub e gera PDF via gerar-pdf.py

Uso:
  python3 mkd-fetch.py
  python3 mkd-fetch.py --repo projetos-ept/mkd-pandoc
  python3 mkd-fetch.py --pasta modelos
  python3 mkd-fetch.py --so html
"""

import sys
import os
import subprocess
import argparse
import urllib.request
import urllib.error
import json
from pathlib import Path

# ──────────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO
# ──────────────────────────────────────────────────────────────────

REPO_PADRAO  = "projetos-ept/mkd-pandoc"
PASTA_PADRAO = "modelos"
BRANCH       = "main"

BASE         = Path(__file__).parent.resolve()
DOCUMENTOS   = BASE / "documentos"
SCRIPT_PDF   = BASE / "gerar-pdf.py"

# ──────────────────────────────────────────────────────────────────

COR_AZUL    = "\033[94m"
COR_VERDE   = "\033[92m"
COR_LARANJA = "\033[93m"
COR_ERRO    = "\033[91m"
COR_RESET   = "\033[0m"
COR_NEGRITO = "\033[1m"

def azul(t):    return f"{COR_AZUL}{t}{COR_RESET}"
def verde(t):   return f"{COR_VERDE}{t}{COR_RESET}"
def laranja(t): return f"{COR_LARANJA}{t}{COR_RESET}"
def erro(t):    return f"{COR_ERRO}{t}{COR_RESET}"
def negrito(t): return f"{COR_NEGRITO}{t}{COR_RESET}"


def cabecalho():
    print()
    print(azul("╔══════════════════════════════════════════════╗"))
    print(azul("║  ") + negrito("MKD-Project — CETEP-LNAB") + azul("                  ║"))
    print(azul("║  ") + "Buscador de documentos no GitHub          " + azul("║"))
    print(azul("╚══════════════════════════════════════════════╝"))
    print()


def buscar_arquivos(repo, pasta, branch):
    """Consulta a API do GitHub e retorna lista de arquivos .md na pasta."""
    url = f"https://api.github.com/repos/{repo}/contents/{pasta}?ref={branch}"
    req = urllib.request.Request(url, headers={"User-Agent": "mkd-fetch/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            dados = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(erro(f"  Repositório ou pasta não encontrado: {repo}/{pasta}"))
        else:
            print(erro(f"  Erro HTTP {e.code} ao acessar o GitHub."))
        sys.exit(1)
    except urllib.error.URLError:
        print(erro("  Sem conexão com o GitHub. Verifique sua internet."))
        sys.exit(1)

    arquivos = [
        {"nome": item["name"], "url_raw": item["download_url"], "tamanho": item["size"]}
        for item in dados
        if item["type"] == "file" and item["name"].endswith(".md")
    ]
    return arquivos


def listar_arquivos(arquivos, repo, pasta):
    """Exibe o menu numerado de arquivos disponíveis."""
    print(negrito(f"  Repositório: ") + azul(f"github.com/{repo}"))
    print(negrito(f"  Pasta:       ") + azul(f"{pasta}/"))
    print()
    print(negrito(f"  {'#':<4} {'Arquivo':<45} {'Tamanho':>8}"))
    print(f"  {'─'*4} {'─'*45} {'─'*8}")

    for i, arq in enumerate(arquivos, 1):
        kb = arq["tamanho"] / 1024
        destaque = verde(f"{i:<4}") 
        print(f"  {destaque} {arq['nome']:<45} {kb:>6.1f} KB")

    print()


def escolher_arquivo(arquivos):
    """Solicita escolha do usuário e retorna o arquivo selecionado."""
    while True:
        try:
            entrada = input(azul("  Escolha o número do arquivo (0 para sair): ")).strip()
            if entrada == "0":
                print("\n  Saindo.\n")
                sys.exit(0)
            n = int(entrada)
            if 1 <= n <= len(arquivos):
                return arquivos[n - 1]
            print(laranja(f"  Digite um número entre 1 e {len(arquivos)}."))
        except (ValueError, KeyboardInterrupt):
            print("\n  Cancelado.\n")
            sys.exit(0)


def baixar_arquivo(arq, destino):
    """Baixa o arquivo .md para a pasta documentos/."""
    destino.parent.mkdir(parents=True, exist_ok=True)

    print()
    print(f"  Baixando {azul(arq['nome'])}...")

    req = urllib.request.Request(arq["url_raw"], headers={"User-Agent": "mkd-fetch/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            conteudo = r.read()
        destino.write_bytes(conteudo)
        kb = len(conteudo) / 1024
        print(verde(f"  OK  Salvo em: {destino}  ({kb:.1f} KB)"))
    except urllib.error.URLError:
        print(erro("  Falha ao baixar o arquivo."))
        sys.exit(1)


def confirmar_geracao(nome):
    """Pergunta se deve gerar o PDF imediatamente."""
    print()
    try:
        resp = input(azul(f"  Gerar PDF de '{nome}' agora? [S/n]: ")).strip().lower()
        return resp in ("", "s", "sim", "y", "yes")
    except KeyboardInterrupt:
        return False


def escolher_modo():
    """Pergunta o modo de geração."""
    print()
    print("  Modo de geração:")
    print(f"  {verde('1')} PDF + HTML  (padrão)")
    print(f"  {verde('2')} Só HTML     (rápido, sem Playwright)")
    print(f"  {verde('3')} Só PDF")
    print()
    try:
        resp = input(azul("  Escolha [1/2/3]: ")).strip()
        modos = {"1": "ambos", "2": "html", "3": "pdf", "": "ambos"}
        return modos.get(resp, "ambos")
    except KeyboardInterrupt:
        return "ambos"


def gerar_pdf(destino, modo, abrir):
    """Chama o gerar-pdf.py com os parâmetros escolhidos."""
    if not SCRIPT_PDF.exists():
        print(erro(f"  gerar-pdf.py não encontrado em: {SCRIPT_PDF}"))
        sys.exit(1)

    cmd = ["python3", str(SCRIPT_PDF), str(destino), "--so", modo]
    if not abrir:
        cmd.append("--nao-abrir")

    print()
    print(azul("  ─" * 24))
    subprocess.run(cmd)
    print(azul("  ─" * 24))


def main():
    parser = argparse.ArgumentParser(
        prog="mkd-fetch",
        description="Busca .md no GitHub e gera PDF via MKD-Project."
    )
    parser.add_argument("--repo",  default=REPO_PADRAO,  help=f"Repositório GitHub (padrão: {REPO_PADRAO})")
    parser.add_argument("--pasta", default=PASTA_PADRAO, help=f"Pasta no repositório (padrão: {PASTA_PADRAO})")
    parser.add_argument("--branch", default=BRANCH,     help=f"Branch (padrão: {BRANCH})")
    parser.add_argument("--so", choices=["html","pdf","ambos"], default=None,
                        help="Modo de geração (pula a pergunta interativa)")
    parser.add_argument("--nao-abrir", action="store_true", help="Não abrir o PDF ao final")
    args = parser.parse_args()

    cabecalho()

    # Busca arquivos
    print(f"  Buscando arquivos em {azul(f'github.com/{args.repo}/{args.pasta}')}...\n")
    arquivos = buscar_arquivos(args.repo, args.pasta, args.branch)

    if not arquivos:
        print(laranja(f"  Nenhum arquivo .md encontrado em '{args.pasta}'."))
        sys.exit(0)

    # Lista e escolha
    listar_arquivos(arquivos, args.repo, args.pasta)
    arq = escolher_arquivo(arquivos)

    # Destino local
    destino = DOCUMENTOS / arq["nome"]

    # Avisa se já existe
    if destino.exists():
        print()
        print(laranja(f"  Arquivo já existe localmente: {destino}"))
        try:
            resp = input(azul("  Sobrescrever? [s/N]: ")).strip().lower()
            if resp not in ("s", "sim", "y"):
                print("  Usando arquivo local existente.")
            else:
                baixar_arquivo(arq, destino)
        except KeyboardInterrupt:
            print("\n  Cancelado.")
            sys.exit(0)
    else:
        baixar_arquivo(arq, destino)

    # Geração
    if confirmar_geracao(arq["nome"]):
        modo = args.so if args.so else escolher_modo()
        gerar_pdf(destino, modo, abrir=not args.nao_abrir)
    else:
        print()
        print(f"  Arquivo salvo em: {verde(str(destino))}")
        print(f"  Para gerar depois: {azul(f'python3 gerar-pdf.py documentos/{arq[\"nome\"]}')}")
        print()


if __name__ == "__main__":
    main()
