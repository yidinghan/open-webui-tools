# Open WebUI Tools

[简体中文](../../README.md) | English | [日本語](README.ja.md) | [Français](README.fr.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)

A collection of Open WebUI tools and pipelines, providing extended functionality to enhance LLM applications.

## Features

### Pipelines

#### [Poe API Pipeline](../../src/pipelines/poe_api_pipeline.py)

Access various AI models through Poe API, with support for `extra_body` custom parameter passthrough.

**GitHub Raw Link (can be installed directly in Open WebUI):**
```
https://raw.githubusercontent.com/yidinghan/open-webui-tools/main/src/pipelines/poe_api_pipeline.py
```

**Features:**
- Supports latest models including GPT-5.2, Claude-Sonnet-4.5, Claude-Opus-4.5, Gemini-3-Pro, Grok-4
- Full support for reasoning parameters like `reasoning_effort`, `thinking_budget`
- Support for multimedia generation parameters like `aspect`, `video_length`
- Dynamic model list (automatically fetched from Poe API)
- Streaming/non-streaming responses

**Quick Start:**

```bash
# Copy to pipelines directory
cp src/pipelines/poe_api_pipeline.py /path/to/pipelines/

# Configure POE_API_KEY in Open WebUI
```

Detailed documentation: [docs/poe-api-pipeline-guide.md](../poe-api-pipeline-guide.md)

### Tools

#### [Jira API Integration](../../src/tools/jira_api_guru.py)

Full-featured Jira API integration tool, supporting issue management, project queries, status changes, and more.

## Project Structure

```
.
├── src/
│   ├── pipelines/     # Open WebUI Pipelines
│   ├── tools/         # Open WebUI Tools
│   ├── utils/         # Common utility functions
│   └── config/        # Configuration related
├── tests/             # Test files
├── docs/              # Documentation
└── examples/          # Example code
```

## Development

```bash
# Clone repository
git clone https://github.com/yidinghan/open-webui-tools.git
cd open-webui-tools

# Install dependencies
pip install requests pydantic
```

## License

MIT License
