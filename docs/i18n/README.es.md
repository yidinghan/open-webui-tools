# Open WebUI Tools

[简体中文](../../README.md) | [English](README.en.md) | [日本語](README.ja.md) | [Français](README.fr.md) | Español | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)

Una colección de herramientas y pipelines de Open WebUI, que proporciona funcionalidad extendida para mejorar las aplicaciones LLM.

## Características

### Pipelines

#### [Poe API Pipeline](../../src/pipelines/poe_api_pipeline.py)

Acceda a varios modelos de IA a través de la API de Poe, con soporte para el paso de parámetros personalizados `extra_body`.

**Enlace GitHub Raw (se puede instalar directamente en Open WebUI):**
```
https://raw.githubusercontent.com/yidinghan/open-webui-tools/main/src/pipelines/poe_api_pipeline.py
```

**Características:**
- Soporta los últimos modelos incluyendo GPT-5.2, Claude-Sonnet-4.5, Claude-Opus-4.5, Gemini-3-Pro, Grok-4
- Soporte completo para parámetros de razonamiento como `reasoning_effort`, `thinking_budget`
- Soporte para parámetros de generación multimedia como `aspect`, `video_length`
- Lista de modelos dinámica (obtenida automáticamente desde la API de Poe)
- Respuestas en streaming/no-streaming

**Inicio Rápido:**

```bash
# Copiar al directorio de pipelines
cp src/pipelines/poe_api_pipeline.py /path/to/pipelines/

# Configurar POE_API_KEY en Open WebUI
```

Documentación detallada: [docs/poe-api-pipeline-guide.md](../poe-api-pipeline-guide.md)

### Tools

#### [Integración API Jira](../../src/tools/jira_api_guru.py)

Herramienta de integración completa con la API de Jira, que soporta gestión de incidencias, consultas de proyectos, cambios de estado y más.

## Estructura del Proyecto

```
.
├── src/
│   ├── pipelines/     # Open WebUI Pipelines
│   ├── tools/         # Open WebUI Tools
│   ├── utils/         # Funciones de utilidad comunes
│   └── config/        # Configuración
├── tests/             # Archivos de prueba
├── docs/              # Documentación
└── examples/          # Código de ejemplo
```

## Desarrollo

```bash
# Clonar repositorio
git clone https://github.com/yidinghan/open-webui-tools.git
cd open-webui-tools

# Instalar dependencias
pip install requests pydantic
```

## Licencia

MIT License
