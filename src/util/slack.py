"""Slack incoming-webhook 알림 전송 유틸.

장시간 돌리는 크롤러/배치 잡이 끝나거나 에러를 만났을 때 Slack 채널로
한 줄 알림을 쏘기 위해 만들었다. 호출 시점에 ``.env`` 의
``SLACK_WEBHOOK_URL`` 을 읽어 사용한다 (URL은 시크릿이라 코드에 직접 안 박음).
"""
from __future__ import annotations

import json
import os
import sys

import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


def send_msg(msg: str) -> None:
    """Crawling 알림 형식으로 한 줄짜리 메시지를 Slack에 전송.

    Args:
        msg: 알림 본문. 앞에 ``"Crawling 알림\\n"`` 프리픽스가 자동으로 붙는다.

    Raises:
        Exception: HTTP 응답이 200이 아닐 때 (webhook URL 누락/권한 오류 등).
    """
    url = os.getenv("SLACK_WEBHOOK_URL")
    message = "Crawling 알림\n" + msg
    title = "New Incoming Message :zap:"
    slack_data = {
        "username": "NotificationBot",
        "icon_emoji": ":satellite:",
        "attachments": [
            {
                "color": "#9733EE",
                "fields": [
                    {
                        "title": title,
                        "value": message,
                        "short": "false",
                    }
                ],
            }
        ],
    }
    byte_length = str(sys.getsizeof(slack_data))
    headers = {"Content-Type": "application/json", "Content-Length": byte_length}
    response = requests.post(url, data=json.dumps(slack_data), headers=headers)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)