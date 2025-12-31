# Open WebUI Tools

[简体中文](../../README.md) | [English](README.en.md) | [日本語](README.ja.md) | [Français](README.fr.md) | [Español](README.es.md) | Deutsch | [Português](README.pt-BR.md) | [Русский](README.ru.md)

Eine Sammlung von Open WebUI-Tools und Pipelines, die erweiterte Funktionen zur Verbesserung von LLM-Anwendungen bieten.

## Funktionen

### Pipelines

#### [Poe API Pipeline](../../src/pipelines/poe_api_pipeline.py)

Greifen Sie über die Poe-API auf verschiedene KI-Modelle zu, mit Unterstützung für die Durchreichung benutzerdefinierter `extra_body`-Parameter.

**GitHub Raw-Link (kann direkt in Open WebUI installiert werden):**
```
https://raw.githubusercontent.com/yidinghan/open-webui-tools/main/src/pipelines/poe_api_pipeline.py
```

**Funktionen:**
- Unterstützt die neuesten Modelle einschließlich GPT-5.2, Claude-Sonnet-4.5, Claude-Opus-4.5, Gemini-3-Pro, Grok-4
- Vollständige Unterstützung für Reasoning-Parameter wie `reasoning_effort`, `thinking_budget`
- Unterstützung für Multimedia-Generierungsparameter wie `aspect`, `video_length`
- Dynamische Modellliste (automatisch von der Poe-API abgerufen)
- Streaming-/Nicht-Streaming-Antworten

**Schnellstart:**

```bash
# In das Pipelines-Verzeichnis kopieren
cp src/pipelines/poe_api_pipeline.py /path/to/pipelines/

# POE_API_KEY in Open WebUI konfigurieren
```

Ausführliche Dokumentation: [docs/poe-api-pipeline-guide.md](../poe-api-pipeline-guide.md)

### Tools

#### [Jira API Integration](../../src/tools/jira_api_guru.py)

Voll ausgestattetes Jira-API-Integrationstool mit Unterstützung für Issue-Management, Projektabfragen, Statusänderungen und mehr.

## Projektstruktur

```
.
├── src/
│   ├── pipelines/     # Open WebUI Pipelines
│   ├── tools/         # Open WebUI Tools
│   ├── utils/         # Gemeinsame Hilfsfunktionen
│   └── config/        # Konfiguration
├── tests/             # Testdateien
├── docs/              # Dokumentation
└── examples/          # Beispielcode
```

## Entwicklung

```bash
# Repository klonen
git clone https://github.com/yidinghan/open-webui-tools.git
cd open-webui-tools

# Abhängigkeiten installieren
pip install requests pydantic
```

## Lizenz

MIT License
