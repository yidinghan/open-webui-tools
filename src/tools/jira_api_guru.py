"""
title: Jira API Integration for Open-WebUI
description: 全功能 Jira API 集成工具，支持问题管理、项目查询、状态变更等完整的 Jira 功能，并实现用户级别的权限控制
repository: https://github.com/your-username/open-webui-tools
author: @your-username
author_url: https://github.com/your-username
version: 1.0.0
changelog:
  - 1.0.0: 初始版本，支持完整的 Jira API 调用、用户 PAT 权限控制和服务器配置
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
            f"### {title}\n\n|"
            + "|".join(headers)
            + "|\n|"
            + "|".join(["---"] * len(headers))
            + "|\n"
        )

        for row in rows:
            # Convert all cells to strings and escape pipe characters
            formatted_row = [str(cell).replace("|", "\\|") for cell in row]
            table += "|" + "|".join(formatted_row) + "|\n"

        table += "\n"

        # Reuse the emit_message method
        await self.emit_message(table)


class Tools:
    def __init__(self):
        self.valves = self.Valves()
        self.user_valves = self.UserValves()

    class UserValves(BaseModel):
        user_pat: str = Field(
            "",
            description="您的 Jira 个人访问令牌 (Personal Access Token)",
        )

    class Valves(BaseModel):
        base_url: str = Field(
            "",
            description="Jira 服务器地址 (例如: https://your-company.atlassian.net)",
        )
        pat: str = Field(
            "",
            description="默认的 Jira 个人访问令牌 (如果用户未提供则使用此令牌)",
        )

        @field_validator('base_url')
        def validate_url(cls, v):
            if not v:
                raise ValueError("Base URL cannot be empty")
            return v

    def _get_jira_auth_token(self, __user__: dict = {}) -> Optional[str]:
        """
        从用户值存储获取个人访问令牌
        """
        # 优先使用用户级别的 PAT，如果没有则使用工具级别的 PAT
        try:
            if __user__ and "valves" in __user__ and "user_pat" in __user__["valves"]:
                token = __user__["valves"]["user_pat"]
                if token:
                    return token
            return self.valves.pat
        except Exception as e:
            raise ValueError(f"无法获取 Jira 访问令牌: {str(e)}")

    def _get_jira_server(self) -> str:
        """
        获取 Jira 服务器地址，直接从工具配置中获取
        """
        if self.valves.base_url:
            return self.valves.base_url
        raise ValueError("必须在工具配置中设置 Jira 服务器地址")

    def _make_jira_request(self, method: str, endpoint: str, __user__: dict = {}, data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> str:
        """
        向 Jira API 发送请求

        :param method: HTTP 方法 (GET, POST, PUT, DELETE)
        :param endpoint: API 端点路径
        :param __user__: 用户信息字典
        :param data: 请求体数据字典
        :param params: 请求参数字典
        :return: API 响应结果 JSON 字符串
        """
        token = self._get_jira_auth_token(__user__)
        if not token:
            raise ValueError("未找到 Jira 个人访问令牌。请在用户设置中添加您的令牌。")

        # 获取 Jira 服务器地址
        server_url = self._get_jira_server()

        # 构建完整 URL
        url = f"{server_url.rstrip('/')}/rest/api/latest{endpoint}"

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
                raise ValueError(f"不支持的请求方法: {method}")

            if response.status_code != 200:
                error_message = response.text
                return json.dumps({"error": f"请求失败，状态码: {response.status_code}, 错误信息: {error_message}, 请求 URL: {url}"}, ensure_ascii=False)

            # 检查响应是否包含内容
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
            error_response = {"error": f"Jira API 请求失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_get_issue(self, issue_key: str, expand: str = None, __user__: dict = {}, __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        获取 Jira 问题详情

        :param issue_key: 问题的键值，例如 PROJECT-123
        :param expand: 要展开的字段，例如 "renderedFields,names,schema,transitions,operations,editmeta,changelog"
        :return: 包含问题详细信息的 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"获取 Jira 问题 {issue_key} 的详细信息", False)

        try:
            params = {}
            if expand:
                params["expand"] = expand

            result = self._make_jira_request("GET", f"/issue/{issue_key}", __user__, params=params)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"获取问题详情失败: {result_obj['error']}", True, True)
                else:
                    # 提取关键信息
                    summary = result_obj.get("fields", {}).get("summary", "无标题")
                    status = result_obj.get("fields", {}).get("status", {}).get("name", "未知状态")
                    project = result_obj.get("fields", {}).get("project", {}).get("key", "未知项目")

                    await event_emitter.emit_message(f"""
### Jira 问题详情

**问题:** [{issue_key}]({self._get_jira_server()}/browse/{issue_key})
**标题:** {summary}
**项目:** {project}
**状态:** {status}
""")
                    await event_emitter.emit_status(f"成功获取问题 {issue_key} 的详情", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"获取问题详情失败: {error_message}", True, True)

            error_response = {"error": f"获取 Jira 问题失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_create_issue(self, project_key: str, issue_type: str, summary: str,
                    description: str = None, priority: str = None, assignee: str = None,
                    custom_fields: str = None, __user__: dict = {}, __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        创建 Jira 问题

        :param project_key: 项目键值
        :param issue_type: 问题类型 (如 "Bug", "Task" 等)
        :param summary: 问题摘要
        :param description: 问题描述 (可选)
        :param priority: 优先级 (可选)
        :param assignee: 经办人账号 ID (可选)
        :param custom_fields: 自定义字段的JSON字符串 (可选)
        :return: 创建的问题信息 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在创建 Jira 问题: {summary}", False)

        try:
            data = {
                "fields": {
                    "project": {"key": project_key},
                    "issuetype": {"name": issue_type},
                    "summary": summary
                }
            }

            if description:
                data["fields"]["description"] = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                }

            if priority:
                data["fields"]["priority"] = {"name": priority}

            if assignee:
                data["fields"]["assignee"] = {"id": assignee}

            if custom_fields:
                try:
                    custom_fields_dict = json.loads(custom_fields)
                    for field_id, value in custom_fields_dict.items():
                        data["fields"][field_id] = value
                except json.JSONDecodeError:
                    raise ValueError("custom_fields 参数必须是有效的 JSON 字符串")

            result = self._make_jira_request("POST", "/issue", __user__, data=data)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"创建问题失败: {result_obj['error']}", True, True)
                else:
                    issue_key = result_obj.get("key", "未知问题")
                    issue_url = f"{self._get_jira_server()}/browse/{issue_key}"

                    await event_emitter.emit_message(f"""
### ✅ 问题创建成功

**新问题:** [{issue_key}]({issue_url})
**标题:** {summary}
**项目:** {project_key}
**类型:** {issue_type}
""")
                    await event_emitter.emit_status(f"问题 {issue_key} 创建成功", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"创建问题失败: {error_message}", True, True)

            error_response = {"error": f"创建 Jira 问题失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_update_issue(self, issue_key: str, summary: str = None,
                    description: str = None, priority: str = None, assignee: str = None,
                    custom_fields: str = None, __user__: dict = {}, __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        更新 Jira 问题

        :param issue_key: 问题的键值，例如 PROJECT-123
        :param summary: 问题摘要 (可选)
        :param description: 问题描述 (可选)
        :param priority: 优先级 (可选)
        :param assignee: 经办人账号 ID (可选)
        :param custom_fields: 自定义字段的JSON字符串 (可选)
        :return: 更新操作结果 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在更新 Jira 问题 {issue_key}", False)

        try:
            data = {"fields": {}}

            if summary:
                data["fields"]["summary"] = summary

            if description:
                data["fields"]["description"] = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                }

            if priority:
                data["fields"]["priority"] = {"name": priority}

            if assignee:
                data["fields"]["assignee"] = {"id": assignee}

            if custom_fields:
                try:
                    custom_fields_dict = json.loads(custom_fields)
                    for field_id, value in custom_fields_dict.items():
                        data["fields"][field_id] = value
                except json.JSONDecodeError:
                    raise ValueError("custom_fields 参数必须是有效的 JSON 字符串")

            # 检查是否有字段要更新
            if not data["fields"]:
                error_message = "未提供任何要更新的字段"
                if event_emitter:
                    await event_emitter.emit_status(error_message, True, True)
                return json.dumps({"error": error_message}, ensure_ascii=False)

            result = self._make_jira_request("PUT", f"/issue/{issue_key}", __user__, data=data)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"更新问题失败: {result_obj['error']}", True, True)
                else:
                    issue_url = f"{self._get_jira_server()}/browse/{issue_key}"
                    update_fields = []

                    if summary:
                        update_fields.append(f"标题: {summary}")
                    if description:
                        update_fields.append("描述")
                    if priority:
                        update_fields.append(f"优先级: {priority}")
                    if assignee:
                        update_fields.append(f"经办人: {assignee}")
                    if custom_fields:
                        update_fields.append("自定义字段")

                    fields_text = "\n- ".join(update_fields)

                    await event_emitter.emit_message(f"""
### 🔄 问题更新成功

**问题:** [{issue_key}]({issue_url})

已更新字段:
- {fields_text}
""")
                    await event_emitter.emit_status(f"问题 {issue_key} 更新成功", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"更新问题失败: {error_message}", True, True)

            error_response = {"error": f"更新 Jira 问题失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_delete_issue(self, issue_key: str, delete_subtasks: bool = False, __user__: dict = {}, __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        删除 Jira 问题

        :param issue_key: 问题的键值，例如 PROJECT-123
        :param delete_subtasks: 是否删除子任务
        :return: 删除操作结果 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在删除 Jira 问题 {issue_key}", False)

        try:
            params = {}
            if delete_subtasks:
                params["deleteSubtasks"] = "true"

            result = self._make_jira_request("DELETE", f"/issue/{issue_key}", __user__, params=params)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"删除问题失败: {result_obj['error']}", True, True)
                else:
                    message = f"问题 {issue_key} 已成功删除"
                    if delete_subtasks:
                        message += "（包括所有子任务）"

                    await event_emitter.emit_message(f"""
### 🗑️ 问题删除成功

{message}
""")
                    await event_emitter.emit_status(f"问题 {issue_key} 删除成功", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"删除问题失败: {error_message}", True, True)

            error_response = {"error": f"删除 Jira 问题失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_search_issues(self, jql: str, start_at: int = 0,
                     max_results: int = 50, fields: str = None, expand: str = None, __user__: dict = {},
                     __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        使用 JQL 搜索 Jira 问题

        :param jql: JQL 查询语句
        :param start_at: 起始索引
        :param max_results: 最大结果数
        :param fields: 要返回的字段列表，逗号分隔的字符串
        :param expand: 要展开的字段
        :return: 匹配的问题列表 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在搜索 Jira 问题: {jql}", False)

        try:
            data = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results
            }

            if fields:
                data["fields"] = fields.split(',')

            if expand:
                data["expand"] = expand

            result = self._make_jira_request("POST", "/search", __user__, data=data)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"搜索问题失败: {result_obj['error']}", True, True)
                else:
                    issues = result_obj.get("issues", [])
                    total = result_obj.get("total", 0)

                    if not issues:
                        await event_emitter.emit_message(f"""
### 🔍 搜索结果

未找到符合查询条件的问题: `{jql}`
""")
                    else:
                        # 准备表格数据
                        rows = []
                        for issue in issues:
                            key = issue.get("key", "")
                            fields = issue.get("fields", {})
                            summary = fields.get("summary", "")
                            status = fields.get("status", {}).get("name", "")
                            priority = fields.get("priority", {}).get("name", "")

                            link = f"[{key}]({self._get_jira_server()}/browse/{key})"
                            rows.append([link, summary, status, priority])

                        # 显示分页信息
                        start = start_at + 1
                        end = min(start_at + len(issues), total)
                        pagination = f"显示 {start} 到 {end}，共 {total} 个结果"

                        await event_emitter.emit_table(
                            ["问题", "标题", "状态", "优先级"],
                            rows,
                            f"搜索结果: {pagination}"
                        )

                    await event_emitter.emit_status(f"搜索完成，找到 {total} 个问题", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"搜索问题失败: {error_message}", True, True)

            error_response = {"error": f"搜索 Jira 问题失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_get_projects(self, __user__: dict = {}, __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        获取所有项目

        :return: 项目列表 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status("正在获取 Jira 项目列表", False)

        try:
            result = self._make_jira_request("GET", "/project", __user__)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"获取项目列表失败: {result_obj['error']}", True, True)
                else:
                    if isinstance(result_obj, list) and result_obj:
                        # 准备表格数据
                        rows = []
                        for project in result_obj:
                            key = project.get("key", "")
                            name = project.get("name", "")
                            lead = project.get("lead", {}).get("displayName", "")
                            project_url = f"{self._get_jira_server()}/browse/{key}"
                            link = f"[{key}]({project_url})"

                            rows.append([link, name, lead])

                        await event_emitter.emit_table(
                            ["项目键", "项目名称", "负责人"],
                            rows,
                            "Jira 项目列表"
                        )
                    else:
                        await event_emitter.emit_message("未找到任何项目")

                    await event_emitter.emit_status("项目列表获取完成", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"获取项目列表失败: {error_message}", True, True)

            error_response = {"error": f"获取 Jira 项目列表失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_get_project(self, project_key: str, expand: str = None, __user__: dict = {}, __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        获取特定项目详情

        :param project_key: 项目键值
        :param expand: 要展开的字段
        :return: 项目详细信息 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在获取项目 {project_key} 的详细信息", False)

        try:
            params = {}
            if expand:
                params["expand"] = expand

            result = self._make_jira_request("GET", f"/project/{project_key}", __user__, params=params)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"获取项目详情失败: {result_obj['error']}", True, True)
                else:
                    name = result_obj.get("name", "")
                    lead = result_obj.get("lead", {}).get("displayName", "")
                    description = result_obj.get("description", "无描述")
                    url = result_obj.get("url", "")
                    project_url = f"{self._get_jira_server()}/browse/{project_key}"

                    await event_emitter.emit_message(f"""
### 项目详情: {name}

**项目键:** [{project_key}]({project_url})
**名称:** {name}
**负责人:** {lead}
**描述:** {description}
**URL:** {url if url else "无"}
""")
                    await event_emitter.emit_status(f"项目 {project_key} 详情获取完成", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"获取项目详情失败: {error_message}", True, True)

            error_response = {"error": f"获取项目详情失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_add_comment(self, issue_key: str, comment: str, __user__: dict = {}, __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        添加评论到问题

        :param issue_key: 问题的键值，例如 PROJECT-123
        :param comment: 评论内容
        :return: 创建的评论信息 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在向问题 {issue_key} 添加评论", False)

        try:
            data = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment
                                }
                            ]
                        }
                    ]
                }
            }

            result = self._make_jira_request("POST", f"/issue/{issue_key}/comment", __user__, data=data)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"添加评论失败: {result_obj['error']}", True, True)
                else:
                    issue_url = f"{self._get_jira_server()}/browse/{issue_key}"
                    created = result_obj.get("created", "")

                    await event_emitter.emit_message(f"""
### 💬 评论已添加

成功添加评论到问题 [{issue_key}]({issue_url})
**添加时间:** {created}
""")
                    await event_emitter.emit_status(f"评论已添加到问题 {issue_key}", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"添加评论失败: {error_message}", True, True)

            error_response = {"error": f"添加评论失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_get_comments(self, issue_key: str, start_at: int = 0, max_results: int = 50, __user__: dict = {}, __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        获取问题的所有评论

        :param issue_key: 问题的键值，例如 PROJECT-123
        :param start_at: 起始索引
        :param max_results: 最大结果数
        :return: 评论列表 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在获取问题 {issue_key} 的评论", False)

        try:
            params = {
                "startAt": start_at,
                "maxResults": max_results
            }

            result = self._make_jira_request("GET", f"/issue/{issue_key}/comment", __user__, params=params)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"获取评论失败: {result_obj['error']}", True, True)
                else:
                    comments = result_obj.get("comments", [])
                    total = result_obj.get("total", 0)
                    issue_url = f"{self._get_jira_server()}/browse/{issue_key}"

                    if not comments:
                        await event_emitter.emit_message(f"""
### 💬 问题评论

问题 [{issue_key}]({issue_url}) 没有评论
""")
                    else:
                        comments_text = ""
                        for i, comment in enumerate(comments, 1):
                            author = comment.get("author", {}).get("displayName", "未知用户")
                            created = comment.get("created", "")
                            body = "未能提取评论正文"

                            # 尝试从不同的 Jira API 版本中提取评论内容
                            if "body" in comment:
                                # 处理 Jira API 的不同版本
                                body_value = comment["body"]
                                if isinstance(body_value, dict) and "content" in body_value:
                                    # 尝试提取格式化文本内容
                                    try:
                                        paragraphs = []
                                        for content_item in body_value["content"]:
                                            if content_item["type"] == "paragraph":
                                                paragraph_text = []
                                                for text_item in content_item["content"]:
                                                    if text_item["type"] == "text":
                                                        paragraph_text.append(text_item["text"])
                                                paragraphs.append("".join(paragraph_text))
                                        body = "\n".join(paragraphs)
                                    except:
                                        body = "无法解析评论格式"
                                else:
                                    # 纯文本评论
                                    body = str(body_value)

                            comments_text += f"""
#### 评论 {i}/{len(comments)}
**作者:** {author}
**时间:** {created}
**内容:**
{body}

---
"""

                        await event_emitter.emit_message(f"""
### 💬 问题评论

问题 [{issue_key}]({issue_url}) 的评论 (共 {total} 条):
{comments_text}
""")

                    await event_emitter.emit_status(f"已获取问题 {issue_key} 的评论", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"获取评论失败: {error_message}", True, True)

            error_response = {"error": f"获取评论失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_get_transitions(self, issue_key: str, __user__: dict = {}, __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        获取问题可用的转换状态

        :param issue_key: 问题的键值，例如 PROJECT-123
        :return: 可用的转换状态列表 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在获取问题 {issue_key} 可用的状态转换", False)

        try:
            result = self._make_jira_request("GET", f"/issue/{issue_key}/transitions", __user__)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"获取状态转换失败: {result_obj['error']}", True, True)
                else:
                    transitions = result_obj.get("transitions", [])
                    issue_url = f"{self._get_jira_server()}/browse/{issue_key}"

                    if not transitions:
                        await event_emitter.emit_message(f"""
### 🔄 状态转换

问题 [{issue_key}]({issue_url}) 没有可用的状态转换
""")
                    else:
                        # 准备表格数据
                        rows = []
                        for transition in transitions:
                            id = transition.get("id", "")
                            name = transition.get("name", "")
                            to_status = transition.get("to", {}).get("name", "")

                            rows.append([id, name, to_status])

                        await event_emitter.emit_table(
                            ["转换ID", "名称", "目标状态"],
                            rows,
                            f"问题 {issue_key} 可用的状态转换"
                        )

                    await event_emitter.emit_status(f"已获取问题 {issue_key} 的状态转换", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"获取状态转换失败: {error_message}", True, True)

            error_response = {"error": f"获取状态转换失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_transition_issue(self, issue_key: str, transition_id: str,
                        comment: str = None, resolution: str = None, __user__: dict = {},
                        __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        转换问题状态

        :param issue_key: 问题的键值，例如 PROJECT-123
        :param transition_id: 转换 ID
        :param comment: 转换评论 (可选)
        :param resolution: 解决结果 (可选)
        :return: 转换操作结果 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在更新问题 {issue_key} 的状态", False)

        try:
            data = {
                "transition": {
                    "id": transition_id
                }
            }

            update = {}

            if comment:
                update["comment"] = [{
                    "add": {
                        "body": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": comment
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }]

            if resolution:
                data["fields"] = {
                    "resolution": {"name": resolution}
                }

            if update:
                data["update"] = update

            result = self._make_jira_request("POST", f"/issue/{issue_key}/transitions", __user__, data=data)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"状态转换失败: {result_obj['error']}", True, True)
                else:
                    issue_url = f"{self._get_jira_server()}/browse/{issue_key}"

                    # 尝试获取转换名称
                    transition_name = "新状态"
                    transitions_result = json.loads(self._make_jira_request("GET", f"/issue/{issue_key}/transitions", __user__))

                    if not "error" in transitions_result:
                        for t in transitions_result.get("transitions", []):
                            if t.get("id") == transition_id:
                                transition_name = t.get("to", {}).get("name", transition_name)
                                break

                    message = f"""
### 🔄 问题状态已更新

问题 [{issue_key}]({issue_url}) 已转换到 **{transition_name}** 状态
"""
                    if comment:
                        message += f"""
**添加评论:** {comment}
"""
                    if resolution:
                        message += f"""
**解决结果:** {resolution}
"""

                    await event_emitter.emit_message(message)
                    await event_emitter.emit_status(f"问题 {issue_key} 状态已更新", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"状态转换失败: {error_message}", True, True)

            error_response = {"error": f"状态转换失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_search_projects(self, jql: str, start_at: int = 0,
                     max_results: int = 50, fields: str = None, expand: str = None, __user__: dict = {},
                     __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        使用 JQL 搜索 Jira 项目

        :param jql: JQL 查询语句
        :param start_at: 起始索引
        :param max_results: 最大结果数
        :param fields: 要返回的字段列表，逗号分隔的字符串
        :param expand: 要展开的字段
        :return: 匹配的项目列表 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在搜索 Jira 项目: {jql}", False)

        try:
            data = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results
            }

            if fields:
                data["fields"] = fields.split(',')

            if expand:
                data["expand"] = expand

            result = self._make_jira_request("POST", "/project/search", __user__, data=data)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"搜索项目失败: {result_obj['error']}", True, True)
                else:
                    projects = result_obj.get("projects", [])
                    total = result_obj.get("total", 0)

                    if not projects:
                        await event_emitter.emit_message(f"""
### 🔍 搜索结果

未找到符合查询条件的项目: `{jql}`
""")
                    else:
                        # 准备表格数据
                        rows = []
                        for project in projects:
                            key = project.get("key", "")
                            name = project.get("name", "")
                            lead = project.get("lead", {}).get("displayName", "")

                            link = f"[{key}]({self._get_jira_server()}/browse/{key})"
                            rows.append([link, name, lead])

                        # 显示分页信息
                        start = start_at + 1
                        end = min(start_at + len(projects), total)
                        pagination = f"显示 {start} 到 {end}，共 {total} 个结果"

                        await event_emitter.emit_table(
                            ["项目", "名称", "负责人"],
                            rows,
                            f"搜索结果: {pagination}"
                        )

                    await event_emitter.emit_status(f"搜索完成，找到 {total} 个项目", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"搜索项目失败: {error_message}", True, True)

            error_response = {"error": f"搜索 Jira 项目失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)

    async def jira_search_issues(self, jql: str, start_at: int = 0,
                     max_results: int = 50, fields: str = None, expand: str = None, __user__: dict = {},
                     __event_emitter__: Callable[[dict], Awaitable[None]] = None) -> str:
        """
        使用 JQL 搜索 Jira 问题

        :param jql: JQL 查询语句
        :param start_at: 起始索引
        :param max_results: 最大结果数
        :param fields: 要返回的字段列表，逗号分隔的字符串
        :param expand: 要展开的字段
        :return: 匹配的问题列表 JSON 字符串
        """
        event_emitter = None
        if __event_emitter__:
            event_emitter = EventEmitter(__event_emitter__)
            await event_emitter.emit_status(f"正在搜索 Jira 问题: {jql}", False)

        try:
            data = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results
            }

            if fields:
                data["fields"] = fields.split(',')

            if expand:
                data["expand"] = expand

            result = self._make_jira_request("POST", "/search", __user__, data=data)

            if event_emitter:
                result_obj = json.loads(result)
                if "error" in result_obj:
                    await event_emitter.emit_status(f"搜索问题失败: {result_obj['error']}", True, True)
                else:
                    issues = result_obj.get("issues", [])
                    total = result_obj.get("total", 0)

                    if not issues:
                        await event_emitter.emit_message(f"""
### 🔍 搜索结果

未找到符合查询条件的问题: `{jql}`
""")
                    else:
                        # 准备表格数据
                        rows = []
                        for issue in issues:
                            key = issue.get("key", "")
                            fields = issue.get("fields", {})
                            summary = fields.get("summary", "")
                            status = fields.get("status", {}).get("name", "")
                            priority = fields.get("priority", {}).get("name", "")

                            link = f"[{key}]({self._get_jira_server()}/browse/{key})"
                            rows.append([link, summary, status, priority])

                        # 显示分页信息
                        start = start_at + 1
                        end = min(start_at + len(issues), total)
                        pagination = f"显示 {start} 到 {end}，共 {total} 个结果"

                        await event_emitter.emit_table(
                            ["问题", "标题", "状态", "优先级"],
                            rows,
                            f"搜索结果: {pagination}"
                        )

                    await event_emitter.emit_status(f"搜索完成，找到 {total} 个问题", True)

            return result

        except Exception as e:
            error_message = str(e)
            if event_emitter:
                await event_emitter.emit_status(f"搜索问题失败: {error_message}", True, True)

            error_response = {"error": f"搜索 Jira 问题失败: {error_message}"}
            return json.dumps(error_response, ensure_ascii=False)
    # 剩余方法的模式类似，都需要添加 __event_emitter__ 参数并实现相应的事件通知逻辑
