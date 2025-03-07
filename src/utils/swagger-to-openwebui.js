#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');
const url = require('url');

// 处理命令行参数
if (process.argv.length < 3) {
  console.error('Usage: node swagger-to-openwebui.js <swagger-json-file-or-url> [output-py-file]');
  process.exit(1);
}

const swaggerInput = process.argv[2];
const outputFileName = process.argv[3] || '';

// 检查输入是文件路径还是URL
const isUrl = swaggerInput.startsWith('http://') || swaggerInput.startsWith('https://');

// 创建输出目录
const scriptDir = path.dirname(process.argv[1]);
const outputDir = path.join(scriptDir, 'generated_tools');

// 确保输出目录存在
if (!fs.existsSync(outputDir)) {
  try {
    fs.mkdirSync(outputDir, { recursive: true });
    console.log(`Created output directory: ${outputDir}`);
  } catch (error) {
    console.error(`Error creating output directory: ${error.message}`);
    process.exit(1);
  }
}

// 生成带时间戳的文件名
function generateOutputFilePath(baseFileName = '') {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

  let fileName;
  if (baseFileName) {
    // 拆分文件名和扩展名
    const ext = path.extname(baseFileName);
    const name = path.basename(baseFileName, ext);
    fileName = `${name}_${timestamp}${ext || '.py'}`;
  } else {
    // 从Swagger输入生成文件名
    const sourceName = isUrl
      ? new URL(swaggerInput).hostname.replace(/\./g, '_')
      : path.basename(swaggerInput, path.extname(swaggerInput));
    fileName = `${sourceName}_${timestamp}.py`;
  }

  return path.join(outputDir, fileName);
}

// 从URL或文件获取Swagger JSON
function fetchSwaggerJson(callback) {
  if (isUrl) {
    console.log(`Fetching Swagger JSON from URL: ${swaggerInput}`);

    // 解析URL
    const parsedUrl = url.parse(swaggerInput);
    const isHttps = parsedUrl.protocol === 'https:';
    const client = isHttps ? https : http;

    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (isHttps ? 443 : 80),
      path: parsedUrl.path,
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    };

    const req = client.request(options, (res) => {
      if (res.statusCode !== 200) {
        callback(new Error(`Failed to fetch Swagger JSON: HTTP status ${res.statusCode}`));
        return;
      }

      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const swagger = JSON.parse(data);
          callback(null, swagger);
        } catch (error) {
          callback(new Error(`Failed to parse Swagger JSON: ${error.message}`));
        }
      });
    });

    req.on('error', (error) => {
      callback(new Error(`Failed to fetch Swagger JSON: ${error.message}`));
    });

    req.end();
  } else {
    // 从文件读取
    console.log(`Reading Swagger JSON from file: ${swaggerInput}`);
    try {
      const swaggerContent = fs.readFileSync(swaggerInput, 'utf8');
      const swagger = JSON.parse(swaggerContent);
      callback(null, swagger);
    } catch (error) {
      callback(new Error(`Error reading or parsing Swagger file: ${error.message}`));
    }
  }
}

// 生成Python文件
function generatePythonToolFile(swagger) {
  const apiTitle = swagger.info?.title || 'API Integration';
  const apiDesc = swagger.info?.description || 'API Integration Tool for Open-WebUI';
  const apiVersion = swagger.info?.version || '1.0.0';
  const basePath = swagger.basePath || '';
  const host = swagger.host || '';
  const schemes = swagger.schemes || ['https'];
  const defaultScheme = schemes[0];

  // 提取API路径和操作
  const paths = swagger.paths || {};
  const definitions = swagger.definitions || {};

  let pythonCode = `"""
title: ${apiTitle} for Open-WebUI
description: ${apiDesc}
repository: https://github.com/your-username/open-webui-tools
author: @your-username
author_url: https://github.com/your-username
version: ${apiVersion}
changelog:
  - ${apiVersion}: Initial version
"""

import requests
import json
import os
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from pydantic import BaseModel, Field, field_validator


class EventEmitter:
    def __init__(self, event_emitter: Callable[[dict], Awaitable[None]]):
        self.event_emitter = event_emitter

    async def emit_status(
        self, description: str, done: bool, error: bool = False
    ) -> None:
        """
        Emit a status event with a description and completion status.

        Args:
            description: Text description of the status.
            done: Whether the process is complete.
            error: Whether an error occurred during the process.
        """
        if error and not done:
            raise ValueError("Error status must also be marked as done")

        icon = "✅" if done and not error else "🚫 " if error else "💬"

        try:
            await self.event_emitter(
                {
                    "data": {
                        "description": f"{icon} {description}",
                        "status": "complete" if done else "in_progress",
                        "done": done,
                    },
                    "type": "status",
                }
            )

        except Exception as e:
            raise RuntimeError(f"Failed to emit status event: {str(e)}") from e

    async def emit_message(self, content: str) -> None:
        """
        Emit a simple message event.

        Args:
            content: The message content to emit.
        """
        if not content:
            raise ValueError("Message content cannot be empty")

        try:
            await self.event_emitter({"data": {"content": content}, "type": "message"})

        except Exception as e:
            raise RuntimeError(f"Failed to emit message event: {str(e)}") from e

    async def emit_source(
        self, name: str, url: str, content: str, html: bool = False
    ) -> None:
        """
        Emit a citation source event.

        Args:
            name: The name of the source.
            url: The URL of the source.
            content: The content of the citation.
            html: Whether the content is HTML formatted.
        """
        if not name or not url or not content:
            raise ValueError("Source name, URL, and content are required")

        try:
            await self.event_emitter(
                {
                    "type": "citation",
                    "data": {
                        "document": [content],
                        "metadata": [{"source": url, "html": html}],
                        "source": {"name": name},
                    },
                }
            )
        except Exception as e:
            raise RuntimeError(f"Failed to emit source event: {str(e)}") from e

    async def emit_table(
        self,
        headers: List[str],
        rows: List[List[Any]],
        title: Optional[str] = "Results",
    ) -> None:
        """
        Emit a formatted markdown table of data.

        Args:
            headers: List of column headers for the table.
            rows: List of rows, where each row is a list of values.
            title: Optional title for the table, defaults to "Results".
        """
        if not headers:
            raise ValueError("Table must have at least one header")

        if any(len(row) != len(headers) for row in rows):
            raise ValueError("All rows must have the same number of columns as headers")

        # Create markdown table
        table = (
            f"### {title}\\n\\n|"
            + "|".join(headers)
            + "|\\n|"
            + "|".join(["---"] * len(headers))
            + "|\\n"
        )

        for row in rows:
            # Convert all cells to strings and escape pipe characters
            formatted_row = [str(cell).replace("|", "\\\\|") for cell in row]
            table += "|" + "|".join(formatted_row) + "|\\n"

        table += "\\n"

        # Reuse the emit_message method
        await self.emit_message(table)


class Tools:
    def __init__(self):
        self.valves = self.Valves()
        self.user_valves = self.UserValves()
        # 存储API基本配置
        self._base_path = "${basePath}"
        self._default_scheme = "${defaultScheme}"
        self._host = "${host}"

    class UserValves(BaseModel):
        user_token: str = Field(
            "",
            description="Your API access token",
        )

    class Valves(BaseModel):
        base_url: str = Field(
            "${host ? `${defaultScheme}://${host}` : ""}",
            description="API server address (e.g., ${host ? `${defaultScheme}://${host}` : 'https://api.example.com'})",
        )
        api_token: str = Field(
            "",
            description="Default API token (used if user doesn't provide one)",
        )

        @field_validator('base_url')
        def validate_url(cls, v):
            if not v:
                raise ValueError("Base URL cannot be empty")
            return v

    def _get_auth_token(self, __user__: dict = {}) -> Optional[str]:
        """
        Get the authentication token from user valves or tool valves
        """
        # Prioritize user token, fall back to tool token
        try:
            if __user__ and "valves" in __user__ and "user_token" in __user__["valves"]:
                token = __user__["valves"]["user_token"]
                if token:
                    return token
            return self.valves.api_token
        except Exception as e:
            raise ValueError(f"Unable to get API token: {str(e)}")

    def _get_api_server(self) -> str:
        """
        Get the API server URL from tool configuration
        """
        if self.valves.base_url:
            return self.valves.base_url
        raise ValueError("API server address must be set in tool configuration")

    def _make_api_request(self, method: str, endpoint: str, __user__: dict = {}, data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> str:
        """
        Send a request to the API

        :param method: HTTP method (GET, POST, PUT, DELETE)
        :param endpoint: API endpoint path
        :param __user__: User information dictionary
        :param data: Request body data dictionary
        :param params: Request parameters dictionary
        :return: API response as JSON string
        """
        token = self._get_auth_token(__user__)
        if not token:
            raise ValueError("API token not found. Please add your token in user settings.")

        # Get API server address
        server_url = self._get_api_server()

        # Build complete URL
        url = f"{server_url.rstrip('/')}{self._base_path}{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            if method.lower() == "get":
                response = requests.get(url, headers=headers, params=params)
            elif method.lower() == "post":
                response = requests.post(url, headers=headers, json=data, params=params)
            elif method.lower() == "put":
                response = requests.put(url, headers=headers, json=data, params=params)
            elif method.lower() == "delete":
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported request method: {method}")

            if response.status_code < 200 or response.status_code >= 300:
                error_message = response.text
                return json.dumps({"error": f"Request failed, status code: {response.status_code}, error message: {error_message}, request URL: {url}"}, ensure_ascii=False)

            # Check if response contains content
            if response.text.strip():
                return json.dumps(response.json(), ensure_ascii=False)
            return json.dumps({"status": "success", "status_code": response.status_code}, ensure_ascii=False)

        except requests.exceptions.RequestException as e:
            error_message = str(e)
            try:
                if hasattr(e, 'response') and e.response and e.response.text:
                    error_message = f"{error_message}: {e.response.text}"
            except:
                pass
            error_response = {"error": f"API request failed: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)
`;

  // 生成API方法
  for (const path in paths) {
    const operations = paths[path];
    for (const method in operations) {
      if (['get', 'post', 'put', 'delete', 'patch'].includes(method)) {
        const operation = operations[method];

        const operationId = operation.operationId || `${method}_${path.replace(/\//g, '_').replace(/\{|\}/g, '')}`;
        const summary = operation.summary || operationId;
        const description = operation.description || `${summary} operation`;

        // 解析参数
        const pathParams = (operation.parameters || []).filter(p => p.in === 'path');
        const queryParams = (operation.parameters || []).filter(p => p.in === 'query');
        const bodyParam = (operation.parameters || []).find(p => p.in === 'body');

        // 构建方法参数列表
        let paramsSignature = [];
        let paramsDoc = [];

        // 添加路径参数
        pathParams.forEach(param => {
          const paramType = getParamType(param);
          paramsSignature.push(`${param.name}: ${paramType}`);
          paramsDoc.push(`:param ${param.name}: ${param.description || param.name}`);
        });

        // 添加查询参数
        queryParams.forEach(param => {
          const paramType = getParamType(param);
          const defaultValue = param.required ? '' : ' = None';
          paramsSignature.push(`${param.name}: ${paramType}${defaultValue}`);
          paramsDoc.push(`:param ${param.name}: ${param.description || param.name}`);
        });

        // 添加请求体参数
        if (bodyParam) {
          paramsSignature.push(`data: Dict[str, Any] = None`);
          paramsDoc.push(`:param data: ${bodyParam.description || 'Request body data'}`);
        }

        // 添加用户和事件发射器参数
        paramsSignature.push(`__user__: dict = {}`);
        paramsSignature.push(`__event_emitter__: Callable[[dict], Awaitable[None]] = None`);

        // 格式化路径变量
        let endpointPath = path;
        pathParams.forEach(param => {
          // 确保正确的f-string格式
          endpointPath = endpointPath.replace(`{${param.name}}`, `{${param.name}}`);
        });

        // 生成方法代码
        let methodCode = `
    async def ${operationId}(self, ${paramsSignature.join(', ')}) -> str:
        """
        ${description}

${paramsDoc.map(doc => '        ' + doc).join('\n')}
        :return: API response as JSON string
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status("Processing ${summary}", False)

        try:`;

        // 处理路径参数替换
        if (pathParams.length > 0) {
          methodCode += `
            endpoint = f"${endpointPath}"`;
        } else {
          methodCode += `
            endpoint = "${path}"`;
        }

        // 处理查询参数
        if (queryParams.length > 0) {
          methodCode += `
            params = {}`;

          queryParams.forEach(param => {
            methodCode += `
            if ${param.name} is not None:
                params["${param.name}"] = ${param.name}`;
          });
        } else {
          methodCode += `
            params = None`;
        }

        // 处理请求体
        if (method !== 'get' && method !== 'delete') {
          if (bodyParam) {
            methodCode += `
            request_data = data or {}`;
          } else {
            methodCode += `
            request_data = None`;
          }
        }

        // 调用API请求方法 - 修复这里的代码，确保正确处理参数和返回结果
        methodCode += `

            result = self._make_api_request("${method.toUpperCase()}", endpoint, __user__, ${(method !== 'get' && method !== 'delete') ? 'data=request_data, ' : ''}params=params)

            if event_emitter:
                try:
                    result_obj = json.loads(result)
                    if "error" in result_obj:
                        await event_emitter.emit_status("Request failed: " + str(result_obj["error"]), True, True)
                    else:
                        formatted_json = json.dumps(result_obj, indent=2)
                        await event_emitter.emit_message("### ${summary} Result\\n\\n\`\`\`json\\n" + formatted_json + "\\n\`\`\`")
                        await event_emitter.emit_status("${summary} completed successfully", True)
                except Exception as json_error:
                    await event_emitter.emit_status(f"Error formatting response: {str(json_error)}", True, True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status("Operation failed: " + error_message, True, True)

            error_response = {"error": "${summary} failed: " + error_message}
            return json.dumps(error_response, ensure_ascii=False)`;

        pythonCode += methodCode;
      }
    }
  }

  return pythonCode;
}

// 辅助函数，根据Swagger参数类型返回Python类型
function getParamType(param) {
  const type = param.type || (param.schema && param.schema.type);

  if (!type) return 'Any';

  switch (type) {
    case 'string':
      return 'str';
    case 'integer':
      return 'int';
    case 'number':
      return 'float';
    case 'boolean':
      return 'bool';
    case 'array':
      const itemsType = param.items ? getParamType(param.items) : 'Any';
      return `List[${itemsType}]`;
    case 'object':
      return 'Dict[str, Any]';
    default:
      return 'Any';
  }
}

// 处理 Swagger JSON 并生成 Python 代码
fetchSwaggerJson((error, swagger) => {
  if (error) {
    console.error(error.message);
    process.exit(1);
  }

  try {
    // 根据Swagger信息生成API名称，用于文件名
    const apiName = swagger.info?.title?.replace(/\s+/g, '_')?.toLowerCase() || 'api';

    // 生成带时间戳的输出文件路径
    const outputFilePath = generateOutputFilePath(outputFileName || `${apiName}.py`);

    // 生成Python代码
    const pythonCode = generatePythonToolFile(swagger);

    // 替换模板变量以避免在Python中使用未定义的变量
    const finalCode = pythonCode
      .replace('${basePath}', swagger.basePath || '')
      .replace('${defaultScheme}', swagger.schemes ? swagger.schemes[0] : 'https')
      .replace('${host}', swagger.host || '');

    fs.writeFileSync(outputFilePath, finalCode, 'utf8');

    // 创建一个不带时间戳的最新版本的副本（可选）
    const latestFilePath = path.join(outputDir, `${apiName}_latest.py`);
    fs.writeFileSync(latestFilePath, finalCode, 'utf8');

    console.log(`Generated files:`);
    console.log(`1. Version with timestamp: ${outputFilePath}`);
    console.log(`2. Latest version: ${latestFilePath}`);
    console.log(`\nSource: ${isUrl ? 'URL' : 'file'}: ${swaggerInput}`);
  } catch (error) {
    console.error(`Error generating Python file: ${error.message}`);
    process.exit(1);
  }
});