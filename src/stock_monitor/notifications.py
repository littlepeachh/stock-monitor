from __future__ import annotations

import logging
import os

import requests

LOGGER = logging.getLogger(__name__)


def send_feishu(markdown: str) -> bool:
    webhook = os.getenv("FEISHU_WEBHOOK", "").strip()
    if not webhook:
        LOGGER.info("未配置 FEISHU_WEBHOOK，跳过飞书推送")
        return False

    # Keep the message within a practical webhook payload size.
    content = markdown[:18000]
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": "个股跟踪晨报"}},
            "elements": [{"tag": "markdown", "content": content}],
        },
    }
    try:
        response = requests.post(webhook, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        if result.get("code", 0) not in (0, None):
            raise RuntimeError(str(result))
        return True
    except Exception as exc:
        LOGGER.warning("飞书推送失败: %s", exc)
        return False
