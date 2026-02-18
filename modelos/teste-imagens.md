---
turma: 1TACM1-M2
disciplina: Teste de Imagens
professor: Lucas Batista
capitulo: "0"
titulo: "Teste de Imagens no Template"
unidade: Teste
ano: "2025"
---

# Teste de Imagens

Este documento testa o suporte a imagens: dentro de tabela, centralizadas,
em diferentes tamanhos e com legenda.

---

## Imagem simples com legenda

![Logo CETEP-LNAB — tamanho original](https://raw.githubusercontent.com/projetos-ept/images/main/marktext/logo-cetep-lnab.png)

---

## Imagens em diferentes tamanhos

Pandoc suporta atributos de tamanho diretamente na sintaxe Markdown:

![Logo pequeno (100px)](https://raw.githubusercontent.com/projetos-ept/images/main/marktext/logo-cetep-lnab.png){width=100px}

![Logo médio (250px)](https://raw.githubusercontent.com/projetos-ept/images/main/marktext/logo-cetep-lnab.png){width=250px}

![Logo grande (400px)](https://raw.githubusercontent.com/projetos-ept/images/main/marktext/logo-cetep-lnab.png){width=400px}

---

## Imagens dentro de tabela

| Tamanho | Imagem | Descrição |
|---------|--------|-----------|
| Pequeno | ![](https://raw.githubusercontent.com/projetos-ept/images/main/marktext/logo-cetep-lnab.png){width=80px} | Logo 80px |
| Médio   | ![](https://raw.githubusercontent.com/projetos-ept/images/main/marktext/logo-cetep-lnab.png){width=160px} | Logo 160px |
| Grande  | ![](https://raw.githubusercontent.com/projetos-ept/images/main/marktext/logo-cetep-lnab.png){width=240px} | Logo 240px |

---

## Imagem centralizada com legenda (figure/figcaption)

<figure>
  <img src="https://raw.githubusercontent.com/projetos-ept/images/main/marktext/logo-cetep-lnab.png" width="200" alt="Logo CETEP-LNAB">
  <figcaption>Figura 1 — Logo oficial do CETEP-LNAB. Utilizado em todos os materiais didáticos.</figcaption>
</figure>

---

::: conceito
O Pandoc aceita imagens de URL externa diretamente no Markdown.
Para uso offline, salve as imagens na mesma pasta do `.md` e use
caminhos relativos: `![legenda](imagens/foto.png)`
:::
