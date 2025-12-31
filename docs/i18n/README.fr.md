# Open WebUI Tools

[简体中文](../../README.md) | [English](README.en.md) | [日本語](README.ja.md) | Français | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)

Une collection d'outils et de pipelines Open WebUI, fournissant des fonctionnalités étendues pour améliorer les applications LLM.

## Fonctionnalités

### Pipelines

#### [Poe API Pipeline](../../src/pipelines/poe_api_pipeline.py)

Accédez à divers modèles d'IA via l'API Poe, avec prise en charge du passage de paramètres personnalisés `extra_body`.

**Lien GitHub Raw (peut être installé directement dans Open WebUI) :**
```
https://raw.githubusercontent.com/yidinghan/open-webui-tools/main/src/pipelines/poe_api_pipeline.py
```

**Caractéristiques :**
- Prise en charge des derniers modèles incluant GPT-5.2, Claude-Sonnet-4.5, Claude-Opus-4.5, Gemini-3-Pro, Grok-4
- Support complet des paramètres de raisonnement comme `reasoning_effort`, `thinking_budget`
- Support des paramètres de génération multimédia comme `aspect`, `video_length`
- Liste de modèles dynamique (récupérée automatiquement depuis l'API Poe)
- Réponses en streaming/non-streaming

**Démarrage rapide :**

```bash
# Copier dans le répertoire pipelines
cp src/pipelines/poe_api_pipeline.py /path/to/pipelines/

# Configurer POE_API_KEY dans Open WebUI
```

Documentation détaillée : [docs/poe-api-pipeline-guide.md](../poe-api-pipeline-guide.md)

### Tools

#### [Intégration API Jira](../../src/tools/jira_api_guru.py)

Outil d'intégration API Jira complet, prenant en charge la gestion des tickets, les requêtes de projet, les changements de statut, et plus encore.

## Structure du Projet

```
.
├── src/
│   ├── pipelines/     # Open WebUI Pipelines
│   ├── tools/         # Open WebUI Tools
│   ├── utils/         # Fonctions utilitaires communes
│   └── config/        # Configuration
├── tests/             # Fichiers de test
├── docs/              # Documentation
└── examples/          # Code d'exemple
```

## Développement

```bash
# Cloner le dépôt
git clone https://github.com/yidinghan/open-webui-tools.git
cd open-webui-tools

# Installer les dépendances
pip install requests pydantic
```

## Licence

MIT License
