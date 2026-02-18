# MKD-Project — CETEP-LNAB
**Pipeline de publicação de materiais didáticos: Markdown → HTML → PDF**

Converte arquivos `.md` escritos no MarkText em documentos HTML estilizados
(tema livro didático) e PDF de alta qualidade, sem dependências de IA,
sem servidor e sem ferramentas pagas.

---

## Sumário

1. [Visão geral](#visão-geral)
2. [Requisitos e instalação — Windows](#requisitos-e-instalação--windows)
3. [Requisitos e instalação — Linux](#requisitos-e-instalação--linux)
4. [Estrutura do projeto](#estrutura-do-projeto)
5. [Fluxo de trabalho diário](#fluxo-de-trabalho-diário)
6. [Front matter YAML](#front-matter-yaml)
7. [Marcadores de estilo no Markdown](#marcadores-de-estilo-no-markdown)
8. [Imagens](#imagens)
9. [Diagramas Mermaid](#diagramas-mermaid)
10. [Solução de problemas](#solução-de-problemas)

---

## Visão geral

```
documento.md
    │
    ▼
[Pandoc + cetep.html]       ← template injeta cabeçalho, CSS, Mermaid.js
    │
    ▼
saida/documento.html
    │
    ▼
[Playwright + Chromium]     ← abre HTML, aguarda Mermaid renderizar, imprime
    │
    ▼
saida/documento.pdf
```

O script `gerar-pdf.py` executa os dois passos automaticamente com um único comando.

---

## Requisitos e instalação — Windows

### Ferramentas necessárias

| Ferramenta | Função | Versão mínima |
|------------|--------|---------------|
| Python | Executa o script de automação | 3.11+ |
| Pandoc | Converte `.md` em HTML | 3.0+ |
| Playwright | Gera PDF via Chromium headless | 1.40+ |
| Chromium | Renderizador do PDF | qualquer |

### 1. Instalar o Chocolatey (gerenciador de pacotes)

O Chocolatey é o gerenciador de pacotes recomendado para Windows.
Abra o PowerShell como **Administrador** e execute:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

Verifique:
```powershell
choco --version
```

### 2. Instalar o Pandoc via Chocolatey

```powershell
choco install pandoc -y
```

Recarregue o PATH após a instalação:
```powershell
Import-Module $env:ChocolateyInstall\helpers\chocolateyProfile.psm1
refreshenv
```

Verifique:
```powershell
pandoc --version
```

### 3. Instalar o Python

Baixe em <https://python.org/downloads> e instale marcando a opção
**"Add Python to PATH"** durante a instalação.

Verifique:
```powershell
python --version
```

### 4. Instalar o Playwright e o Chromium

```powershell
python -m pip install playwright
python -m playwright install chromium
```

> **Nota:** O download do Chromium tem cerca de 170 MB. Se a conexão
> for lenta, baixe manualmente o `chrome-win64.zip` em
> <https://playwright.dev> e extraia em
> `C:\Users\SEU_USUARIO\AppData\Local\ms-playwright\chromium-1208\chrome-win64\`

---

## Requisitos e instalação — Linux

### Distribuições baseadas em Debian/Ubuntu

```bash
# Pandoc
sudo apt update && sudo apt install pandoc -y

# Python e pip (geralmente já instalados)
sudo apt install python3 python3-pip -y

# Playwright
pip3 install playwright
playwright install chromium
playwright install-deps chromium
```

### Distribuições baseadas em Arch

```bash
sudo pacman -S pandoc python python-pip
pip install playwright
playwright install chromium
playwright install-deps chromium
```

### Verificar instalação

```bash
pandoc --version
python3 --version
python3 -m playwright --version
```

---

## Estrutura do projeto

```
MKD-Project/
├── cetep.html          ← template Pandoc (moldura visual do documento)
├── gerar-pdf.py        ← script de automação
├── README.md           ← este arquivo
│
├── documentos/         ← seus arquivos .md ficam aqui
│   ├── modelo.md
│   ├── Cap01-Parasitologia.md
│   └── Cap02-Protozoarios.md
│
└── saida/              ← HTMLs e PDFs gerados automaticamente
    ├── Cap01-Parasitologia.html
    ├── Cap01-Parasitologia.pdf
    └── ...
```

> O `cetep.html` é o template — define a aparência visual.
> Nunca edite-o para mudar conteúdo; apenas para ajustar o design.

---

## Fluxo de trabalho diário

### Passo 1 — Escreva no MarkText

Abra ou crie um `.md` na pasta `documentos/`.
Todo arquivo deve começar com o bloco YAML (ver seção [Front matter YAML](#front-matter-yaml)).

### Passo 2 — Gere o documento

**Windows (PowerShell):**
```powershell
cd "C:\Users\SEU_USUARIO\OneDrive\MKD-Project\documentos"
python ..\gerar-pdf.py NomeDoDocumento.md
```

**Linux (Terminal):**
```bash
cd ~/MKD-Project/documentos
python3 ../gerar-pdf.py NomeDoDocumento.md
```

### Passo 3 — Resultado esperado

```
→ Convertendo Cap01-Parasitologia.md com Pandoc...
✓ HTML gerado: .../saida/Cap01-Parasitologia.html
→ Gerando PDF com Playwright...
✓ PDF gerado:  .../saida/Cap01-Parasitologia.pdf
✓ Concluído!
```

### Gerar apenas o HTML (visualização rápida)

```bash
# Windows
pandoc documento.md --template=..\cetep.html --standalone -o ..\saida\documento.html

# Linux
pandoc documento.md --template=../cetep.html --standalone -o ../saida/documento.html
```

Abra o HTML no Chrome ou Edge. Os diagramas Mermaid renderizam no browser.
Use `Ctrl+P` para imprimir manualmente se preferir não usar o script.

---

## Front matter YAML

Todo arquivo `.md` deve começar com um bloco YAML entre `---`.
Ele define as variáveis que preenchem o cabeçalho institucional.

```markdown
---
turma: 1TACM1-M2
disciplina: Parasitologia
professor: Lucas Batista
capitulo: "1"
titulo: "O que é Parasitologia?"
unidade: Unidade 1
ano: "2025"
---
```

### Variáveis disponíveis

| Variável | Obrigatória | Onde aparece no documento | Exemplo |
|----------|:-----------:|---------------------------|---------|
| `turma` | Sim | Cabeçalho | `1TACM1-M2` |
| `disciplina` | Sim | Cabeçalho e rodapé | `Parasitologia` |
| `professor` | Sim | Cabeçalho e rodapé | `Lucas Batista` |
| `capitulo` | Sim | Badge azul no topo | `"1"` |
| `titulo` | Sim | Título da aba do browser | `"O que é Parasitologia?"` |
| `unidade` | Não | Rodapé | `Unidade 1` |
| `ano` | Não | Cabeçalho e rodapé | `"2025"` |

> **Dica:** valores numéricos como `capitulo` e `ano` devem ficar
> entre aspas (`"1"`) para o Pandoc tratá-los como texto.

---

## Marcadores de estilo no Markdown

O template reconhece marcadores especiais que transformam blocos de texto
em componentes visuais estilizados. Todos usam a sintaxe de
**fenced divs** do Pandoc (blocos `:::`).

> **Atenção no MarkText:** os blocos `:::` não são renderizados
> visualmente no editor — aparecem como texto puro. O estilo só é
> aplicado no HTML/PDF gerado pelo Pandoc. Isso é comportamento normal.

---

### `::: conceito` — Box Conceito-chave

**Quando usar:** definições formais, conceitos centrais do conteúdo.

**Visual:** fundo azul claro · barra lateral azul · rótulo CONCEITO-CHAVE

```markdown
::: conceito
**Parasitismo** é uma relação ecológica desarmônica onde o parasita
obtém benefício às custas do hospedeiro, causando-lhe prejuízo contínuo.
:::
```

---

### `::: dica` — Box Dica de Ouro

**Quando usar:** dicas práticas, macetes de memorização, observações pedagógicas.

**Visual:** fundo amarelo · barra lateral laranja · ★ · rótulo DICA DE OURO

```markdown
::: dica
Para lembrar: o Hospedeiro **D**efinitivo tem o parasita **D**esenvolvido
(adulto). O **I**ntermediário tem a fase **I**nfantil (larva).
:::
```

---

### `::: atencao` — Box Atenção

**Quando usar:** alertas, erros conceituais comuns, pontos críticos de prova.

**Visual:** fundo vermelho suave · barra lateral vermelha · rótulo ATENÇÃO

```markdown
::: atencao
Não confunda **vetor biológico** com **hospedeiro intermediário**.
O vetor transporta o parasita; o HI hospeda uma fase do ciclo biológico.
:::
```

---

### `::: exemplo` — Box Exemplo Prático

**Quando usar:** casos clínicos, exemplos do mundo real, aplicações práticas.

**Visual:** fundo verde claro · barra lateral verde · rótulo EXEMPLO PRÁTICO

```markdown
::: exemplo
Paciente com ancilostomíase apresenta anemia ferropriva porque o parasita
se fixa na mucosa intestinal e suga sangue continuamente — ação espoliativa.
:::
```

---

### `::: referencias` — Box Bibliografia

**Quando usar:** ao final do documento para listar as fontes consultadas.

**Visual:** fundo cinza · rótulo BIBLIOGRAFIA CONSULTADA

```markdown
::: referencias
NEVES, D. P. *Parasitologia Humana*. São Paulo: Atheneu, 2016.

REY, L. *Bases da Parasitologia Médica*. Rio de Janeiro: Guanabara Koogan, 2010.
:::
```

---

### `>` — Blockquote genérico

**Quando usar:** destaques rápidos sem categoria específica.

**Visual:** fundo amarelo suave · barra lateral laranja (mesmo estilo do `::: dica`)

```markdown
> A Parasitologia é a base de toda a área de Análises Clínicas.
```

---

### Formatação inline padrão do Markdown

Funciona normalmente dentro de qualquer bloco:

```markdown
**negrito**          → destaque em azul institucional
*itálico*            → texto em itálico cinza
`código inline`      → trecho de código em azul
[link](https://...)  → hiperlink azul sublinhado
```

### Tabela de referência rápida

| Marcador | Cor | Rótulo | Uso indicado |
|----------|-----|--------|--------------|
| `::: conceito` | Azul | CONCEITO-CHAVE | Definições formais |
| `::: dica` | Laranja/Amarelo | DICA DE OURO | Macetes pedagógicos |
| `::: atencao` | Vermelho | ATENÇÃO | Alertas e erros comuns |
| `::: exemplo` | Verde | EXEMPLO PRÁTICO | Casos clínicos |
| `::: referencias` | Cinza | BIBLIOGRAFIA | Fontes ao final |
| `> texto` | Laranja | — | Destaque rápido genérico |

---

## Imagens

### Sintaxe básica com legenda

```markdown
![Legenda da imagem](caminho/imagem.png)
```

### Controle de tamanho

```markdown
![Logo pequeno](imagem.png){width=100px}
![Logo médio](imagem.png){width=250px}
![Logo grande](imagem.png){width=400px}
```

### Imagem centralizada com legenda formal

```markdown
<figure>
  <img src="imagem.png" width="300" alt="Descrição">
  <figcaption>Figura 1 — Descrição detalhada da imagem.</figcaption>
</figure>
```

### Imagens dentro de tabela

```markdown
| Organismo | Imagem | Classificação |
|-----------|--------|---------------|
| Ascaris | ![](ascaris.png){width=100px} | Helminto nematódeo |
| Giardia | ![](giardia.png){width=100px} | Protozoário flagelado |
```

### URLs do GitHub

Sempre use a URL **raw**, não a URL da página do repositório:

```
❌  https://github.com/usuario/repo/blob/main/imagem.png
✓   https://raw.githubusercontent.com/usuario/repo/main/imagem.png
```

### Imagens locais

Salve em `documentos/imagens/` e use caminho relativo:

```markdown
![Ciclo do Plasmodium](imagens/ciclo-plasmodium.png){width=400px}
```

---

## Diagramas Mermaid

O template inclui o Mermaid.js, que renderiza automaticamente
blocos de código marcados como `mermaid`.

### Fluxograma vertical

````markdown
```mermaid
graph TD
    A([Início]) --> B{Decisão}
    B -- Sim --> C[Resultado 1]
    B -- Não --> D[Resultado 2]
```
````

### Fluxograma horizontal

````markdown
```mermaid
graph LR
    A[HD] -->|libera ovos| B[Ambiente]
    B -->|contamina| C[HI]
    C -->|infecta| A
```
````

### Outros tipos suportados

| Tipo | Palavra-chave |
|------|---------------|
| Diagrama de sequência | `sequenceDiagram` |
| Diagrama de classe UML | `classDiagram` |
| Gráfico de pizza | `pie` |
| Linha do tempo | `timeline` |

> O MarkText renderiza os blocos Mermaid em tempo real no editor.
> Se um diagrama aparecer com "Syntax error" no PDF, revise a sintaxe —
> palavras reservadas como `end` e `if` não podem ser usadas como rótulos
> de nós sem estar entre aspas.

---

## Solução de problemas

**`pandoc: command not found`**
Feche e reabra o terminal. No PowerShell com Chocolatey:
```powershell
Import-Module $env:ChocolateyInstall\helpers\chocolateyProfile.psm1
refreshenv
```

**`pip` não reconhecido no PowerShell**
Use `python -m pip` no lugar de `pip` diretamente.

**Erro de permissão ao salvar o PDF**
O arquivo PDF anterior está aberto. Feche-o e execute novamente.

**PDF gerado sem estilos (só texto simples)**
O `cetep.html` não foi encontrado. Verifique o caminho da variável
`TEMPLATE` no `gerar-pdf.py`.

**Fontes não carregadas no PDF**
O Playwright precisa de internet para baixar as fontes do Google Fonts
na primeira vez. Em ambientes offline, substitua os links no `cetep.html`
por fontes locais ou fontes do sistema.

**Erro `PermissionError` com OneDrive**
O OneDrive bloqueia arquivos durante a sincronização. Defina a pasta
`saida/` fora do OneDrive alterando a variável `SAIDA` no `gerar-pdf.py`:
```python
SAIDA = Path(r"D:\CETEP-saida")
```

**Diagramas Mermaid com "Syntax error"**
Verifique: palavras reservadas (`end`, `if`, `class`) usadas como rótulos
sem aspas, aspas mal fechadas, ou indentação incorreta em subgraphs.
