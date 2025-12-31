"""
title: Poe API Pipeline with extra_body Support
description: 支持 extra_body 自定义参数的 Poe API Pipeline，完整支持推理模型、图像/视频生成等高级功能
author: yidinghan
author_url: https://github.com/yidinghan
version: 1.0.0
license: MIT
requirements: requests, pydantic
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional, Union, Generator, Iterator

import requests
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pipeline:
    """
    Poe API Manifold Pipeline
    
    核心特性：
    - 完整支持 extra_body 自定义参数透传
    - 支持 reasoning_effort、thinking_budget 等推理参数
    - 支持 aspect、video_length 等多媒体参数
    - 流式/非流式响应处理
    """
    
    class Valves(BaseModel):
        """管理员配置"""
        POE_API_KEY: str = Field(
            default="",
            description="Poe API 密钥 (https://poe.com/api_key)"
        )
        POE_API_BASE_URL: str = Field(
            default="https://api.poe.com/v1",
            description="Poe API 基础 URL"
        )
        DEFAULT_MODEL: str = Field(
            default="Claude-Sonnet-4.5",
            description="默认模型"
        )
        REQUEST_TIMEOUT: int = Field(
            default=300,
            description="请求超时（秒），视频生成建议设置更长"
        )
        MAX_RETRIES: int = Field(
            default=3,
            description="最大重试次数"
        )
        DEBUG_MODE: bool = Field(
            default=False,
            description="调试模式"
        )

    class UserValves(BaseModel):
        """用户配置"""
        POE_API_KEY: str = Field(
            default="",
            description="用户 Poe API 密钥（优先使用）"
        )

    # OpenAI 标准参数（不放入 extra_body）
    STANDARD_PARAMS = {
        "model", "messages", "stream", "temperature", "max_tokens",
        "top_p", "frequency_penalty", "presence_penalty", "stop",
        "n", "logprobs", "echo", "best_of", "logit_bias", "user"
    }
    
    # 备用模型列表（API 不可用时使用）
    FALLBACK_MODELS = [
        # OpenAI
        {"id": "GPT-5.2", "name": "GPT-5.2"},
        {"id": "GPT-5.2-Pro", "name": "GPT-5.2-Pro"},
        {"id": "GPT-5.2-Instant", "name": "GPT-5.2-Instant"},
        # Anthropic
        {"id": "Claude-Sonnet-4.5", "name": "Claude-Sonnet-4.5"},
        {"id": "Claude-Opus-4.5", "name": "Claude-Opus-4.5"},
        {"id": "Claude-Opus-4.1", "name": "Claude-Opus-4.1"},
        {"id": "Claude-Haiku-4.5", "name": "Claude-Haiku-4.5"},
        # Google
        {"id": "Gemini-3-Pro", "name": "Gemini-3-Pro"},
        {"id": "Gemini-3-Flash", "name": "Gemini-3-Flash"},
        # xAI
        {"id": "Grok-4", "name": "Grok-4"},
        # Others
        {"id": "GLM-4.7", "name": "GLM-4.7"},
        {"id": "Minimax-M2.1", "name": "Minimax-M2.1"},
    ]

    def __init__(self):
        self.type = "manifold"
        self.id = "poeapipp"
        self.name = "poeapipp/"
        self.valves = self.Valves(
            **{"POE_API_KEY": os.getenv("POE_API_KEY", "")}
        )
        self.pipelines = self.FALLBACK_MODELS  # 初始使用备用列表

    async def on_startup(self):
        """启动时获取模型列表"""
        await self._refresh_models()
        logger.info(f"[{self.name}] Pipeline started with {len(self.pipelines)} models")

    async def on_shutdown(self):
        logger.info(f"[{self.name}] Pipeline shutdown")

    async def on_valves_updated(self):
        """配置更新时刷新模型列表"""
        await self._refresh_models()
        logger.info(f"[{self.name}] Valves updated, models refreshed")

    async def _refresh_models(self):
        """从 Poe API 动态获取模型列表"""
        if not self.valves.POE_API_KEY:
            logger.warning(f"[{self.name}] No API key, using fallback models")
            self.pipelines = self.FALLBACK_MODELS
            return
        
        try:
            response = requests.get(
                f"{self.valves.POE_API_BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.valves.POE_API_KEY}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("data", []):
                    model_id = model.get("id", "")
                    if model_id:
                        models.append({
                            "id": model_id,
                            "name": model.get("name", model_id)
                        })
                
                if models:
                    self.pipelines = models
                    logger.info(f"[{self.name}] Fetched {len(models)} models from API")
                    return
            
            logger.warning(f"[{self.name}] Failed to fetch models: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to fetch models: {e}")
        
        self.pipelines = self.FALLBACK_MODELS

    def _get_api_key(self) -> str:
        """获取 API Key"""
        return self.valves.POE_API_KEY

    def _build_request_body(self, model_id: str, messages: List[dict], body: dict) -> dict:
        """
        构建请求体，核心功能：识别并透传 extra_body 参数
        
        处理逻辑：
        1. 提取标准 OpenAI 参数
        2. 其余参数作为 extra_body 透传到 Poe
        """
        # 基础请求体
        request_body = {
            "model": model_id,
            "messages": messages,
            "stream": body.get("stream", True)
        }
        
        # 添加标准可选参数
        for param in ["temperature", "max_tokens", "top_p", 
                      "frequency_penalty", "presence_penalty", "stop"]:
            if param in body and body[param] is not None:
                request_body[param] = body[param]
        
        # ========== 核心：处理 extra_body ==========
        # 方式1：显式的 extra_body 字段
        if "extra_body" in body and isinstance(body["extra_body"], dict):
            for key, value in body["extra_body"].items():
                request_body[key] = value
            if self.valves.DEBUG_MODE:
                logger.debug(f"[{self.name}] extra_body params: {body['extra_body']}")
        
        # 方式2：body 中的非标准参数直接透传
        # 这允许 Open WebUI 或其他客户端直接在 body 中传递自定义参数
        for key, value in body.items():
            if key not in self.STANDARD_PARAMS and key != "extra_body":
                if key not in request_body:  # 避免覆盖已设置的参数
                    request_body[key] = value
                    if self.valves.DEBUG_MODE:
                        logger.debug(f"[{self.name}] Passthrough param: {key}={value}")
        
        return request_body

    def _make_request(
        self,
        url: str,
        headers: dict,
        body: dict,
        stream: bool = False
    ) -> requests.Response:
        """带重试的请求"""
        last_error = None
        
        for attempt in range(self.valves.MAX_RETRIES):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    stream=stream,
                    timeout=self.valves.REQUEST_TIMEOUT
                )
                
                if response.status_code < 500:
                    return response
                    
                last_error = f"HTTP {response.status_code}"
                logger.warning(f"[{self.name}] Retry {attempt+1}/{self.valves.MAX_RETRIES}: {last_error}")
                
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                logger.warning(f"[{self.name}] Retry {attempt+1}/{self.valves.MAX_RETRIES}: {last_error}")
            
            if attempt < self.valves.MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # 指数退避
        
        raise Exception(f"Request failed after {self.valves.MAX_RETRIES} retries: {last_error}")

    def _stream_response(self, response: requests.Response) -> Generator[str, None, None]:
        """处理 SSE 流式响应"""
        for line in response.iter_lines():
            if not line:
                continue
            
            line_str = line.decode("utf-8")
            if not line_str.startswith("data:"):
                continue
            
            data_str = line_str[5:].strip()
            if data_str == "[DONE]":
                break
            
            try:
                data = json.loads(data_str)
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("delta", {}).get("content", "")
                    if content:
                        yield content
            except json.JSONDecodeError:
                continue

    def _parse_response(self, response: requests.Response) -> str:
        """解析非流式响应"""
        data = response.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""

    def _format_error(self, response: requests.Response) -> str:
        """格式化错误信息"""
        try:
            error_msg = response.json().get("error", {}).get("message", response.text)
        except:
            error_msg = response.text[:500]
        
        status_messages = {
            400: "请求参数错误",
            401: "API Key 无效",
            403: "无权访问此模型",
            404: "模型不存在",
            429: "请求频率超限",
            500: "服务器错误",
        }
        
        error_type = status_messages.get(response.status_code, "请求失败")
        return f"❌ **{error_type}** (HTTP {response.status_code})\n\n{error_msg}"

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        核心处理方法
        
        Args:
            user_message: 用户最新消息
            model_id: 模型 ID（已由框架处理好，无前缀）
            messages: 完整消息列表
            body: 请求体，包含 stream、temperature 等参数
        
        支持的 extra_body 参数示例：
        - reasoning_effort: "low" | "medium" | "high" (o1/o3 模型)
        - thinking_budget: int (Claude 模型)
        - aspect: "1280x720" (视频/图像模型)
        - video_length: int (视频模型)
        - style: str (图像模型)
        """
        # 验证 API Key
        api_key = self._get_api_key()
        if not api_key:
            return "❌ **错误**: 未配置 Poe API Key"
        
        # 构建请求体（包含 extra_body 处理）
        request_body = self._build_request_body(model_id, messages, body)
        is_streaming = request_body.get("stream", True)
        
        # 多媒体模型建议禁用流式
        media_models = {"Sora-2", "Runway-Gen-4-Turbo", "DALL-E-3", "Imagen"}
        if model_id in media_models and is_streaming:
            request_body["stream"] = False
            is_streaming = False
            logger.info(f"[{self.name}] Disabled streaming for media model: {model_id}")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.valves.POE_API_BASE_URL}/chat/completions"
        
        if self.valves.DEBUG_MODE:
            # 脱敏日志
            safe_body = {k: v for k, v in request_body.items() if k != "messages"}
            safe_body["messages"] = f"[{len(messages)} messages]"
            logger.debug(f"[{self.name}] Request: {json.dumps(safe_body, ensure_ascii=False)}")
        
        try:
            response = self._make_request(url, headers, request_body, is_streaming)
            
            if response.status_code >= 400:
                return self._format_error(response)
            
            if is_streaming:
                return self._stream_response(response)
            else:
                return self._parse_response(response)
                
        except requests.exceptions.Timeout:
            return f"❌ **超时**: 请求超过 {self.valves.REQUEST_TIMEOUT} 秒"
        except requests.exceptions.ConnectionError:
            return "❌ **连接失败**: 无法连接 Poe API"
        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}", exc_info=True)
            return f"❌ **错误**: {str(e)}"
