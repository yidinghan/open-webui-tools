# Open WebUI Tools

[简体中文](../../README.md) | [English](README.en.md) | [日本語](README.ja.md) | [Français](README.fr.md) | [Español](README.es.md) | [Deutsch](README.de.md) | Português | [Русский](README.ru.md)

Uma coleção de ferramentas e pipelines do Open WebUI, fornecendo funcionalidades estendidas para aprimorar aplicações LLM.

## Funcionalidades

### Pipelines

#### [Poe API Pipeline](../../src/pipelines/poe_api_pipeline.py)

Acesse vários modelos de IA através da API Poe, com suporte para passagem de parâmetros personalizados `extra_body`.

**Link GitHub Raw (pode ser instalado diretamente no Open WebUI):**
```
https://raw.githubusercontent.com/yidinghan/open-webui-tools/main/src/pipelines/poe_api_pipeline.py
```

**Características:**
- Suporta os modelos mais recentes incluindo GPT-5.2, Claude-Sonnet-4.5, Claude-Opus-4.5, Gemini-3-Pro, Grok-4
- Suporte completo para parâmetros de raciocínio como `reasoning_effort`, `thinking_budget`
- Suporte para parâmetros de geração multimídia como `aspect`, `video_length`
- Lista de modelos dinâmica (obtida automaticamente da API Poe)
- Respostas em streaming/não-streaming

**Início Rápido:**

```bash
# Copiar para o diretório de pipelines
cp src/pipelines/poe_api_pipeline.py /path/to/pipelines/

# Configurar POE_API_KEY no Open WebUI
```

Documentação detalhada: [docs/poe-api-pipeline-guide.md](../poe-api-pipeline-guide.md)

### Tools

#### [Integração API Jira](../../src/tools/jira_api_guru.py)

Ferramenta de integração completa com a API do Jira, suportando gerenciamento de issues, consultas de projetos, alterações de status e mais.

## Estrutura do Projeto

```
.
├── src/
│   ├── pipelines/     # Open WebUI Pipelines
│   ├── tools/         # Open WebUI Tools
│   ├── utils/         # Funções utilitárias comuns
│   └── config/        # Configuração
├── tests/             # Arquivos de teste
├── docs/              # Documentação
└── examples/          # Código de exemplo
```

## Desenvolvimento

```bash
# Clonar repositório
git clone https://github.com/yidinghan/open-webui-tools.git
cd open-webui-tools

# Instalar dependências
pip install requests pydantic
```

## Licença

MIT License
