import os
import time
import streamlit as st
from anthropic import Anthropic
import json

MODEL = "claude-sonnet-4-20250514"
MAX_INPUT_CHARS = 12000
MAX_RETRIES = 2
RETRY_DELAY = 3


def get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    if not api_key:
        st.error("未配置 ANTHROPIC_API_KEY，请在 Streamlit Cloud Secrets 或环境变量中设置。")
        st.stop()
    return Anthropic(api_key=api_key)


def truncate_text(text: str, max_chars: int = MAX_INPUT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[文本已截断，仅保留前部分内容]"


def call_api(prompt: str, max_tokens: int = 2000) -> str:
    client = get_client()
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                timeout=60.0,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if "authentication" in err_str or "api key" in err_str or "401" in err_str:
                st.error("API Key 无效或已过期，请更新 ANTHROPIC_API_KEY。")
                st.stop()
            if "insufficient" in err_str or "billing" in err_str or "402" in err_str:
                st.error("API 余额不足，请前往 https://console.anthropic.com/ 充值。")
                st.stop()
            if "rate" in err_str or "429" in err_str:
                wait = RETRY_DELAY * (attempt + 1) * 2
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                    continue
                st.error("API 请求过于频繁，请等待几分钟后重试。")
                st.stop()
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue

    raise RuntimeError(f"API 调用失败（已重试{MAX_RETRIES}次）: {last_error}")


def parse_json_response(text: str):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "```":
                lines = lines[:i]
                break
        text = "\n".join(lines)
    return json.loads(text)
