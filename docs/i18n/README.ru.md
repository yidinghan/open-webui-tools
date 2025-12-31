# Open WebUI Tools

[简体中文](../../README.md) | [English](README.en.md) | [日本語](README.ja.md) | [Français](README.fr.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | Русский

Коллекция инструментов и пайплайнов Open WebUI, предоставляющая расширенные функции для улучшения LLM-приложений.

## Возможности

### Pipelines

#### [Poe API Pipeline](../../src/pipelines/poe_api_pipeline.py)

Доступ к различным AI-моделям через Poe API с поддержкой передачи пользовательских параметров `extra_body`.

**GitHub Raw ссылка (можно установить напрямую в Open WebUI):**
```
https://raw.githubusercontent.com/yidinghan/open-webui-tools/main/src/pipelines/poe_api_pipeline.py
```

**Особенности:**
- Поддержка новейших моделей включая GPT-5.2, Claude-Sonnet-4.5, Claude-Opus-4.5, Gemini-3-Pro, Grok-4
- Полная поддержка параметров рассуждения, таких как `reasoning_effort`, `thinking_budget`
- Поддержка параметров генерации мультимедиа, таких как `aspect`, `video_length`
- Динамический список моделей (автоматически получается из Poe API)
- Потоковые/непотоковые ответы

**Быстрый старт:**

```bash
# Скопировать в директорию pipelines
cp src/pipelines/poe_api_pipeline.py /path/to/pipelines/

# Настроить POE_API_KEY в Open WebUI
```

Подробная документация: [docs/poe-api-pipeline-guide.md](../poe-api-pipeline-guide.md)

### Tools

#### [Интеграция Jira API](../../src/tools/jira_api_guru.py)

Полнофункциональный инструмент интеграции с Jira API, поддерживающий управление задачами, запросы проектов, изменение статусов и многое другое.

## Структура проекта

```
.
├── src/
│   ├── pipelines/     # Open WebUI Pipelines
│   ├── tools/         # Open WebUI Tools
│   ├── utils/         # Общие утилиты
│   └── config/        # Конфигурация
├── tests/             # Тестовые файлы
├── docs/              # Документация
└── examples/          # Примеры кода
```

## Разработка

```bash
# Клонировать репозиторий
git clone https://github.com/yidinghan/open-webui-tools.git
cd open-webui-tools

# Установить зависимости
pip install requests pydantic
```

## Лицензия

MIT License
