# Poe API Pipeline 开发指引

> 支持 **extra_body 自定义参数** 的 Poe API Pipeline，实现对推理模型、图像/视频生成等高级功能的完整支持。

## 支持的模型

- **OpenAI**: GPT-5.2, GPT-5.2-Pro, GPT-5.2-Instant
- **Anthropic**: Claude-Sonnet-4.5, Claude-Opus-4.5, Claude-Opus-4.1, Claude-Haiku-4.5
- **Google**: Gemini-3-Pro, Gemini-3-Flash
- **xAI**: Grok-4
- **Others**: GLM-4.7, Minimax-M2.1

## 核心需求：extra_body 参数

### 为什么需要 extra_body？

Poe API 虽然兼容 OpenAI API 格式，但提供了许多 **模型特有的高级参数**，这些参数需要通过 `extra_body` 传递：

| 参数 | 适用模型 | 说明 |
|------|----------|------|
| `reasoning_effort` | o1, o3, GPT-5 | 推理深度：`low`/`medium`/`high` |
| `thinking_budget` | Claude 系列 | 思考预算控制 |
| `aspect` | Sora, Runway, Imagen | 图片/视频宽高比，如 `1280x720` |
| `video_length` | 视频生成模型 | 视频时长（秒） |
| `style` | 图像生成模型 | 生成风格 |

### Poe 官方用法

```python
import openai

client = openai.OpenAI(
    api_key="YOUR_POE_API_KEY",
    base_url="https://api.poe.com/v1"
)

# 推理模型 - reasoning_effort
response = client.chat.completions.create(
    model="o1",
    messages=[{"role": "user", "content": "Solve this math problem..."}],
    extra_body={"reasoning_effort": "high"}
)

# 视频生成 - aspect, video_length
response = client.chat.completions.create(
    model="Sora-2",
    messages=[{"role": "user", "content": "A cat playing piano"}],
    extra_body={"aspect": "1920x1080", "video_length": 5}
)
```

参考: [Poe 官方文档 - extra_body](https://creator.poe.com/docs/external-applications/openai-compatible-api#using-custom-parameters-with-extra_body)

---

## Pipeline 实现要点

完整代码: [`src/pipelines/poe_api_pipeline.py`](../src/pipelines/poe_api_pipeline.py)

### 1. extra_body 透传机制

Pipeline 支持两种方式传递自定义参数：

```python
# 方式1：显式 extra_body 字段
body = {
    "model": "o1",
    "messages": [...],
    "extra_body": {"reasoning_effort": "high"}
}

# 方式2：直接在 body 中传递（自动识别非标准参数）
body = {
    "model": "o1",
    "messages": [...],
    "reasoning_effort": "high"
}
```

核心实现逻辑：

```python
STANDARD_PARAMS = {
    "model", "messages", "stream", "temperature", "max_tokens",
    "top_p", "frequency_penalty", "presence_penalty", "stop",
    "n", "logprobs", "echo", "best_of", "logit_bias", "user"
}

def _build_request_body(self, body: dict, model_id: str) -> dict:
    request_body = {
        "model": model_id,
        "messages": body.get("messages", []),
        "stream": body.get("stream", True)
    }
    
    # 方式1：显式 extra_body
    if "extra_body" in body and isinstance(body["extra_body"], dict):
        for key, value in body["extra_body"].items():
            request_body[key] = value
    
    # 方式2：非标准参数自动透传
    for key, value in body.items():
        if key not in STANDARD_PARAMS and key != "extra_body":
            if key not in request_body:
                request_body[key] = value
    
    return request_body
```

### 2. 多媒体模型处理

Poe 建议多媒体模型（图像/视频）禁用流式响应：

```python
media_models = {"Sora-2", "Runway-Gen-4-Turbo", "DALL-E-3", "Imagen"}
if model_id in media_models:
    request_body["stream"] = False
```

### 3. Manifold 类型声明

Pipeline 作为 Manifold 类型，暴露多个模型：

```python
class Pipeline:
    def __init__(self):
        self.type = "manifold"
        self.id = "poeapipp"
        self.name = "poeapipp/"
        self.pipelines = [
            {"id": "GPT-5.2", "name": "GPT-5.2"},
            {"id": "Claude-Sonnet-4.5", "name": "Claude-Sonnet-4.5"},
            {"id": "Gemini-3-Pro", "name": "Gemini-3-Pro"},
            {"id": "Grok-4", "name": "Grok-4"},
            # ...
        ]
```

---

## 部署

### Docker

```bash
# 复制 Pipeline 文件到 pipelines 目录
cp src/pipelines/poe_api_pipeline.py ./pipelines/

# 启动服务
docker run -d \
  -p 9099:9099 \
  -v $(pwd)/pipelines:/app/pipelines \
  --name pipelines \
  ghcr.io/open-webui/pipelines:main
```

### Open WebUI 配置

1. **Settings → Connections**: 添加 `http://localhost:9099`
2. **Settings → Pipelines → Poe**: 配置 `POE_API_KEY`

---

## 测试

```bash
# 测试 reasoning_effort 参数
curl -X POST http://localhost:9099/v1/chat/completions \
  -H "Authorization: Bearer 0p3n-w3bu!" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "poeapipp.o1",
    "messages": [{"role": "user", "content": "What is 25 * 47?"}],
    "stream": false,
    "reasoning_effort": "high"
  }'

# 测试视频生成
curl -X POST http://localhost:9099/v1/chat/completions \
  -H "Authorization: Bearer 0p3n-w3bu!" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "poeapipp.Sora-2",
    "messages": [{"role": "user", "content": "A sunset over ocean"}],
    "stream": false,
    "extra_body": {"aspect": "1920x1080", "video_length": 5}
  }'
```

---

## 常用 extra_body 参数

| 模型类型 | 参数 | 值示例 | 说明 |
|----------|------|--------|------|
| o1/o3 | `reasoning_effort` | `"low"`, `"medium"`, `"high"` | 推理深度 |
| Claude | `thinking_budget` | `1000` | 思考 token 预算 |
| Sora/Runway | `aspect` | `"1920x1080"`, `"16:9"` | 宽高比 |
| Sora/Runway | `video_length` | `5`, `10` | 视频时长(秒) |
| DALL-E | `size` | `"1024x1024"` | 图片尺寸 |
| DALL-E | `quality` | `"standard"`, `"hd"` | 图片质量 |

---

## 参考

- [Poe OpenAI Compatible API - extra_body](https://creator.poe.com/docs/external-applications/openai-compatible-api#using-custom-parameters-with-extra_body)
- [Poe API Reference](https://creator.poe.com/api-reference/overview)
- [Open WebUI Pipelines](https://docs.openwebui.com/features/pipelines/)
