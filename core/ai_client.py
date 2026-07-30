"""OpenAI 兼容对话客户端（模型可替换）。"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIClient:
    """通过 OpenAI-compatible Chat Completions API 对话。"""

    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    temperature: float = 0.85
    max_tokens: int = 220
    timeout_s: float = 45.0
    system_prompt: str = ""
    history: list[dict[str, str]] = field(default_factory=list)
    max_history: int = 12

    @classmethod
    def from_config(cls, cfg: dict[str, Any], system_prompt: str = "") -> "AIClient":
        env_key = os.environ.get("DESKTOP_PET_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        env_base = os.environ.get("DESKTOP_PET_BASE_URL") or os.environ.get("OPENAI_BASE_URL", "")
        env_model = os.environ.get("DESKTOP_PET_MODEL") or os.environ.get("OPENAI_MODEL", "")
        return cls(
            api_key=cfg.get("api_key") or env_key,
            base_url=(cfg.get("base_url") or env_base or "https://api.openai.com/v1").rstrip("/"),
            model=cfg.get("model") or env_model or "gpt-4o-mini",
            temperature=float(cfg.get("temperature", 0.85)),
            max_tokens=int(cfg.get("max_tokens", 220)),
            timeout_s=float(cfg.get("timeout_s", 45)),
            system_prompt=system_prompt,
            max_history=int(cfg.get("max_history", 12)),
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt

    def clear_history(self) -> None:
        self.history.clear()

    def chat(self, user_text: str) -> str:
        """同步请求一轮对话，返回助手文本。"""
        if not self.api_key:
            raise RuntimeError(
                "未配置 API Key。请在 config.json 的 ai.api_key 填写，"
                "或设置环境变量 DESKTOP_PET_API_KEY / OPENAI_API_KEY。"
            )

        self.history.append({"role": "user", "content": user_text})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

        messages: list[dict[str, str]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(self.history)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"AI 请求失败 HTTP {e.code}: {detail[:300]}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"无法连接 AI 服务: {e.reason}") from e

        try:
            text = body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"AI 返回格式异常: {body!r}") from e

        self.history.append({"role": "assistant", "content": text})
        return text

    def offline_reply(self, user_text: str, fallbacks: list[str]) -> str:
        """无 Key 时的本地萌点回复。"""
        text = user_text.strip().lower()
        import random

        if any(k in text for k in ("你好", "嗨", "hello", "管理员")):
            return random.choice(
                [
                    "哼……来了就来了，又不是专门等你。",
                    "管理员？我、我才没有盯着你的窗口看呢！",
                    "有话快说，狼群的事可多着呢……不过可以先听你一句。",
                ]
            )
        if any(k in text for k in ("可爱", "漂亮", "喜欢", "萌")):
            return random.choice(
                [
                    "才、才不可爱！耳朵……别盯着看！",
                    "你、你突然说这个干什么啦……尾巴自己晃起来了啦！",
                    "哼，被看穿了也不许笑！……谢谢。",
                ]
            )
        if any(k in text for k in ("累", "困", "休息")):
            return random.choice(
                [
                    "那你先歇着。我守着……不是陪你，是巡逻！",
                    "要睡觉就睡，别仗着我在就偷懒太多哦。",
                ]
            )
        if fallbacks:
            return random.choice(fallbacks)
        return "嗯……我听见了。再说清楚一点，我才好帮你。"
