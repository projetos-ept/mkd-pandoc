"""
Cliente da SML Storage API (upload de imagens).

Fluxo em 3 passos:
  1. POST {base}/getUploadUrl  →  {success, uploadUrl, docId, error}
  2. PUT  uploadUrl            com os bytes crus da imagem
  3. POST {base}/confirmUpload →  {success, url, error}
"""

import httpx

from api.config import SML_STORAGE_ENDPOINT, SML_STORAGE_API_KEY, SML_PROJETO

TIMEOUT = 30  # segundos por chamada


class ErroArmazenamento(Exception):
    """Falha de rede ou resposta de erro da SML Storage API."""


def enviar_imagem(nome_arquivo: str, conteudo: bytes, content_type: str) -> str:
    """Envia uma imagem para o SML Storage e retorna a URL pública."""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": SML_STORAGE_API_KEY,
    }

    try:
        with httpx.Client(timeout=TIMEOUT) as cliente:
            resposta = cliente.post(
                f"{SML_STORAGE_ENDPOINT}/getUploadUrl",
                headers=headers,
                json={
                    "projeto": SML_PROJETO,
                    "filename": nome_arquivo,
                    "tag1": "mkd-pandoc",
                    "tag2": "",
                    "tag3": "",
                },
            )
            dados = _json_ok(resposta, "getUploadUrl")

            envio = cliente.put(
                dados["uploadUrl"],
                content=conteudo,
                headers={"Content-Type": content_type},
            )
            if envio.status_code >= 400:
                raise ErroArmazenamento(
                    f"PUT na URL assinada falhou (HTTP {envio.status_code})"
                )

            confirmacao = cliente.post(
                f"{SML_STORAGE_ENDPOINT}/confirmUpload",
                headers=headers,
                json={"docId": dados["docId"]},
            )
            dados = _json_ok(confirmacao, "confirmUpload")
            return dados["url"]
    except httpx.HTTPError as exc:
        raise ErroArmazenamento(f"Erro de rede com o SML Storage: {exc}") from exc


def _json_ok(resposta: httpx.Response, etapa: str) -> dict:
    try:
        dados = resposta.json()
    except ValueError:
        raise ErroArmazenamento(
            f"{etapa}: resposta inválida (HTTP {resposta.status_code})"
        )
    if resposta.status_code >= 400 or not dados.get("success"):
        raise ErroArmazenamento(
            f"{etapa}: {dados.get('error') or f'HTTP {resposta.status_code}'}"
        )
    return dados
