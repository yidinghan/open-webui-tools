# Open WebUI Tools

Open WebUI 工具和 Pipeline 集合，提供增强 LLM 应用的扩展功能。

## 功能

### Pipelines

#### [Poe API Pipeline](src/pipelines/poe_api_pipeline.py)

通过 Poe API 访问多种 AI 模型，支持 `extra_body` 自定义参数透传。

**GitHub Raw 链接（可直接在 Open WebUI 中安装）：**
```
https://raw.githubusercontent.com/yidinghan/open-webui-tools/main/src/pipelines/poe_api_pipeline.py
```

**特性：**
- 支持 GPT-5.2、Claude-Sonnet-4.5、Claude-Opus-4.5、Gemini-3-Pro、Grok-4 等最新模型
- 完整支持 `reasoning_effort`、`thinking_budget` 等推理参数
- 支持 `aspect`、`video_length` 等多媒体生成参数
- 动态模型列表（从 Poe API 自动获取）
- 流式/非流式响应

**快速开始：**

```bash
# 复制到 pipelines 目录
cp src/pipelines/poe_api_pipeline.py /path/to/pipelines/

# 在 Open WebUI 中配置 POE_API_KEY
```

详细文档: [docs/poe-api-pipeline-guide.md](docs/poe-api-pipeline-guide.md)

### Tools

#### [Jira API Integration](src/tools/jira_api_guru.py)

全功能 Jira API 集成工具，支持问题管理、项目查询、状态变更等。

## 项目结构

```
.
├── src/
│   ├── pipelines/     # Open WebUI Pipelines
│   ├── tools/         # Open WebUI Tools
│   ├── utils/         # 通用工具函数
│   └── config/        # 配置相关
├── tests/             # 测试文件
├── docs/              # 文档
└── examples/          # 示例代码
```

## 开发

```bash
# 克隆仓库
git clone https://github.com/yidinghan/open-webui-tools.git
cd open-webui-tools

# 安装依赖
pip install requests pydantic
```

## 许可证

MIT License
