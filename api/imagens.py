"""
Substituição de placeholders de imagem no markdown.

Convenção: o autor escreve {{imagem1}}, {{imagem2}}, ... onde iria a URL:

    ![Legenda da figura]({{imagem1}}){width=250px}

e envia os arquivos nos campos multipart imagem1, imagem2, ...
Cada imagem é enviada ao SML Storage e o placeholder vira a URL pública.
"""

import mimetypes
import re

from api.armazenamento import enviar_imagem

EXTENSOES_ACEITAS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
TAMANHO_MAXIMO = 10 * 1024 * 1024  # 10 MB (limite do SML Storage)

PADRAO_PLACEHOLDER = re.compile(r"\{\{(imagem\d+)\}\}")


class ErroImagens(Exception):
    """Inconsistência entre placeholders e arquivos enviados (HTTP 422)."""


def validar(markdown: str, imagens: dict[str, tuple[str, bytes]]):
    """
    Valida placeholders × arquivos antes de qualquer upload.
    imagens: {campo: (nome_do_arquivo, conteúdo)}.
    """
    placeholders = set(PADRAO_PLACEHOLDER.findall(markdown))

    sem_arquivo = sorted(placeholders - set(imagens))
    if sem_arquivo:
        raise ErroImagens(
            "Placeholder sem arquivo correspondente no formulário: "
            + ", ".join("{{" + p + "}}" for p in sem_arquivo)
        )

    sem_placeholder = sorted(set(imagens) - placeholders)
    if sem_placeholder:
        raise ErroImagens(
            "Arquivo enviado sem placeholder no markdown: "
            + ", ".join(sem_placeholder)
        )

    for campo, (nome, conteudo) in imagens.items():
        extensao = "." + nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
        if extensao not in EXTENSOES_ACEITAS:
            raise ErroImagens(
                f"{campo}: extensão não aceita ({nome}). "
                f"Use: {', '.join(sorted(EXTENSOES_ACEITAS))}"
            )
        if len(conteudo) > TAMANHO_MAXIMO:
            raise ErroImagens(f"{campo}: arquivo maior que 10 MB ({nome})")


def substituir(markdown: str, imagens: dict[str, tuple[str, bytes]]) -> str:
    """
    Faz upload de cada imagem para o SML Storage e substitui os
    placeholders pelas URLs públicas. Chame validar() antes.
    """
    for campo, (nome, conteudo) in sorted(imagens.items()):
        content_type = mimetypes.guess_type(nome)[0] or "application/octet-stream"
        url = enviar_imagem(nome, conteudo, content_type)
        markdown = markdown.replace("{{" + campo + "}}", url)
    return markdown
