"""
title: Jira API Tool for Open-WebUI
description: 通用的 Jira API 工具，支持基础 URL 配置和基本 API 调用示例
repository: https://github.com/your-username/open-webui-tools
author: @your-username
author_url: https://github.com/your-username
version: 1.0.0
changelog:
  - 1.0.0: 初始版本，支持基础 URL 配置和获取 Jira 问题的示例调用
"""

import requests
import json
from typing import Optional

class JiraApiTool:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def get_issue(self, issue_key: str) -> str:
        """
        获取 Jira 问题的详细信息

        :param issue_key: 问题的键值，例如 PROJECT-123
        :return: 包含问题详细信息的 JSON 字符串
        """
        url = f"{self.base_url}/rest/api/latest/issue/{issue_key}"
        headers = {
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return json.dumps({"error": f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}"}, ensure_ascii=False)

        return response.json()

# 示例用法
if __name__ == "__main__":
    jira_tool = JiraApiTool(base_url="https://your-company.atlassian.net")
    issue_details = jira_tool.get_issue("PROJECT-123")
    print(json.dumps(issue_details, ensure_ascii=False, indent=2))
