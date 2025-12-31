# Open WebUI Tools

[简体中文](../../README.md) | [English](README.en.md) | 日本語 | [Français](README.fr.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)

Open WebUI ツールとパイプラインのコレクション。LLM アプリケーションを強化する拡張機能を提供します。

## 機能

### Pipelines

#### [Poe API Pipeline](../../src/pipelines/poe_api_pipeline.py)

Poe API を通じて様々な AI モデルにアクセスし、`extra_body` カスタムパラメータのパススルーをサポートします。

**GitHub Raw リンク（Open WebUI で直接インストール可能）：**
```
https://raw.githubusercontent.com/yidinghan/open-webui-tools/main/src/pipelines/poe_api_pipeline.py
```

**特徴：**
- GPT-5.2、Claude-Sonnet-4.5、Claude-Opus-4.5、Gemini-3-Pro、Grok-4 などの最新モデルをサポート
- `reasoning_effort`、`thinking_budget` などの推論パラメータを完全サポート
- `aspect`、`video_length` などのマルチメディア生成パラメータをサポート
- 動的モデルリスト（Poe API から自動取得）
- ストリーミング/非ストリーミングレスポンス

**クイックスタート：**

```bash
# pipelines ディレクトリにコピー
cp src/pipelines/poe_api_pipeline.py /path/to/pipelines/

# Open WebUI で POE_API_KEY を設定
```

詳細ドキュメント: [docs/poe-api-pipeline-guide.md](../poe-api-pipeline-guide.md)

### Tools

#### [Jira API Integration](../../src/tools/jira_api_guru.py)

フル機能の Jira API 統合ツール。課題管理、プロジェクトクエリ、ステータス変更などをサポートします。

## プロジェクト構成

```
.
├── src/
│   ├── pipelines/     # Open WebUI Pipelines
│   ├── tools/         # Open WebUI Tools
│   ├── utils/         # 共通ユーティリティ関数
│   └── config/        # 設定関連
├── tests/             # テストファイル
├── docs/              # ドキュメント
└── examples/          # サンプルコード
```

## 開発

```bash
# リポジトリをクローン
git clone https://github.com/yidinghan/open-webui-tools.git
cd open-webui-tools

# 依存関係をインストール
pip install requests pydantic
```

## ライセンス

MIT License
