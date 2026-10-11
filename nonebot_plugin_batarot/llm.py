"""大模型（LLM）辅助塔罗解读。

本模块调用 **OpenAI 兼容** 的 ``/chat/completions`` 接口，因此 DeepSeek、OpenAI、
Kimi、智谱、通义千问、SiliconFlow、本地 Ollama / vLLM 等只要兼容该协议即可直接使用。

请求会优先使用 ``aiohttp``（插件已声明的依赖），如果运行环境里没有安装 ``aiohttp``，
则自动回退到 Python 标准库，保证功能可用、不会因为缺少 HTTP 库导致整个插件加载失败。

接口地址与密钥等配置见 :mod:`nonebot_plugin_batarot.config`，
示例写法见插件仓库根目录的 ``.env.example``。
"""

from __future__ import annotations

import asyncio
from contextvars import ContextVar
import functools
import json
import socket
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit
from uuid import uuid4

from nonebot.log import logger

try:  # aiohttp 是插件声明的依赖，但开发环境中可能没有安装
    import aiohttp
except ImportError:  # pragma: no cover - 回退到标准库
    aiohttp = None  # type: ignore[assignment]

from .config import config

__all__ = [
    "LLMError",
    "chat_completion",
    "generate_reading",
    "shutdown",
    "build_tarot_prompt",
    "build_spread_prompt",
    "build_fortune_prompt",
    "build_reading_prompt",
]


class LLMError(Exception):
    """大模型接口调用失败，异常文本可直接展示给用户。"""


DEFAULT_SYSTEM_PROMPT = (
    "你是一位温柔而专业的塔罗牌占卜师，同时熟悉《碧蓝档案》的世界观与角色。"
    "用户会告诉你抽到的塔罗牌、正逆位以及它在牌阵中的位置，请据此给出解读。\n"
    "请遵守以下要求：\n"
    "1. 使用简体中文，语气亲切自然，先说明牌面与位置的联系，再结合用户的问题给出解读。\n"
    "2. 单次解读控制在 200 字左右，可以换行分段，但不要使用 Markdown 标记（如 **、#、-、表格）。\n"
    "3. 塔罗解读只是娱乐与自我反思的参考，不要给出医疗、法律、投资的绝对结论，也不要预言灾祸。\n"
    "4. 结尾给出一条具体、温和、可执行的小建议。"
)

_session: Optional["aiohttp.ClientSession"] = None
_session_lock: Optional[asyncio.Lock] = None
_active_requests = 0
usage_context = ContextVar("batarot_usage_context", default="production")

# 当前使用的 HTTP 实现：有 aiohttp 时优先使用，否则回退到标准库
_backend = "aiohttp" if aiohttp is not None else "urllib"


def _endpoint() -> str:
    """根据 ``batarot_llm_api_base`` 拼出完整的 chat completions 地址。"""
    base = (config.batarot_llm_api_base or "").strip().rstrip("/")
    if not base:
        base = "https://api.deepseek.com/v1"
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


async def _get_session() -> "aiohttp.ClientSession":
    """获取（并复用）aiohttp 会话。"""
    global _session, _session_lock
    if _session is None or _session.closed:
        # 锁在事件循环内创建，兼容较老的 Python 版本
        if _session_lock is None:
            _session_lock = asyncio.Lock()
        async with _session_lock:
            if _session is None or _session.closed:
                timeout = aiohttp.ClientTimeout(total=_timeout())
                _session = aiohttp.ClientSession(timeout=timeout)
    return _session


async def shutdown() -> None:
    """机器人关闭 / 插件卸载时释放连接池。"""
    global _session
    if _session is not None and not _session.closed:
        await _session.close()
    _session = None


def _timeout() -> float:
    return max(float(config.batarot_llm_timeout or 60.0), 1.0)


def _blocking_urllib_post(
    url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: float
) -> Tuple[int, str]:
    """标准库实现（在线程池中执行），返回 (状态码, 响应文本)。"""
    import urllib.error
    import urllib.request

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:  # noqa: S310
            return int(resp.status), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if e.fp else str(e.reason)
        return int(e.code), body


async def _post_json(
    url: str, payload: Dict[str, Any], headers: Dict[str, str]
) -> Tuple[int, str]:
    """发送 POST 请求，返回 (状态码, 响应文本)。网络异常统一转为 LLMError。"""
    timeout = _timeout()

    if _backend == "aiohttp" and aiohttp is not None:
        session = await _get_session()
        try:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                return resp.status, await resp.text()
        except asyncio.TimeoutError as e:
            raise LLMError(f"请求超时（{timeout:g} 秒）") from e
        except aiohttp.ClientError as e:
            raise LLMError("网络请求失败，请检查接口地址和网络连接") from e

    loop = asyncio.get_running_loop()
    try:
        future = loop.run_in_executor(
            None,
            functools.partial(_blocking_urllib_post, url, payload, headers, timeout),
        )
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            while not future.done():
                try:
                    await asyncio.shield(future)
                except asyncio.CancelledError:
                    continue
                except Exception:
                    break
            if not future.cancelled():
                future.exception()
            raise
    except (TimeoutError, socket.timeout) as e:
        raise LLMError(f"请求超时（{timeout:g} 秒）") from e
    except Exception as e:
        raise LLMError("网络请求失败，请检查接口地址和网络连接") from e


def _clean_content(text: str) -> str:
    """去掉模型偶尔附带的代码块标记与多余引号。"""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text[3:]
        if "\n" in text:
            first_line, rest = text.split("\n", 1)
            # 去掉 ```json 这类语言标记
            text = rest if len(first_line.strip()) <= 12 else text
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip().strip('"').strip()


def _thinking_options(url: str, model: str) -> Dict[str, Any]:
    provider = config.batarot_llm_thinking_provider
    host = urlsplit(url).hostname
    if provider == "auto":
        if host == "api.deepseek.com":
            provider = "deepseek"
        elif host in {"api.siliconflow.cn", "api.siliconflow.com"}:
            name = model.rsplit("/", 1)[-1].lower()
            supported = name.startswith(("qwen3", "deepseek-v3.1", "deepseek-v3.2", "glm-4.5", "glm-4.6"))
            excluded = any(word in name for word in ("instruct", "embedding", "reranker"))
            provider = "siliconflow" if supported and not excluded else "none"
        else:
            provider = "none"
    if provider == "deepseek":
        return {"thinking": {"type": "enabled" if config.batarot_llm_thinking else "disabled"}}
    if provider == "siliconflow":
        return {"enable_thinking": config.batarot_llm_thinking}
    return {}


def _update_usage(record: Dict[str, Any], usage: Any) -> None:
    if not isinstance(usage, dict):
        return
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = usage.get(key)
        record[key] = value if type(value) is int and value >= 0 else None
    details = usage.get("completion_tokens_details")
    value = details.get("reasoning_tokens") if isinstance(details, dict) else None
    record["reasoning_tokens"] = value if type(value) is int and value >= 0 else None


def _write_usage(record: Dict[str, Any]) -> None:
    record = dict(record)
    record.pop("requested", None)
    record["estimated_cost_cny"] = None
    inputs, outputs = record["prompt_tokens"], record["completion_tokens"]
    input_price = config.batarot_llm_input_price_per_million
    output_price = config.batarot_llm_output_price_per_million
    if inputs is not None and outputs is not None and input_price is not None and output_price is not None:
        record["estimated_cost_cny"] = round((inputs * input_price + outputs * output_price) / 1_000_000, 8)
    logger.info("batarot_usage {}", json.dumps(record, ensure_ascii=False, separators=(",", ":")))


async def chat_completion(
    messages: List[Dict[str, str]], *, temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    global _active_requests
    if _active_requests >= config.batarot_llm_max_concurrency:
        raise LLMError("当前解读较多，请稍后再试")
    _active_requests += 1
    started = time.monotonic()
    record = {"request_id": uuid4().hex, "model": config.batarot_llm_model,
              "purpose": usage_context.get(), "state": "failed", "requested": False,
              "http_status": None, "prompt_tokens": None, "completion_tokens": None,
              "total_tokens": None, "reasoning_tokens": None}
    try:
        result = await _chat_completion_impl(messages, temperature=temperature, max_tokens=max_tokens, record=record)
        record["state"] = "completed"
        return result
    except asyncio.CancelledError:
        record["state"] = "cancelled"
        raise
    finally:
        _active_requests -= 1
        if record["requested"]:
            record["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)
            _write_usage(record)


async def _chat_completion_impl(
    messages: List[Dict[str, str]],
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    record: Dict[str, Any],
) -> str:
    """调用 OpenAI 兼容接口并返回模型回复文本。

    :raises LLMError: 未开启、未配置密钥、网络异常或接口返回异常时抛出。
    """
    if not config.batarot_llm_enabled:
        raise LLMError("AI 解读未开启（BATAROT_LLM_ENABLED=false）")

    api_key = (config.batarot_llm_api_key or "").strip()
    if not api_key:
        raise LLMError("未配置 API Key，请在 .env 中填写 BATAROT_LLM_API_KEY 后重启")

    model = (config.batarot_llm_model or "").strip()
    if not model:
        raise LLMError("未配置 BATAROT_LLM_MODEL")

    payload: Dict[str, Any] = {"model": model, "messages": messages, "stream": False}

    temp = config.batarot_llm_temperature if temperature is None else temperature
    if temp is not None:
        payload["temperature"] = float(temp)

    tokens = config.batarot_llm_max_tokens if max_tokens is None else max_tokens
    if tokens and int(tokens) > 0:
        payload["max_tokens"] = int(tokens)

    url = _endpoint()
    payload.update(_thinking_options(url, model))
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    record["requested"] = True
    status, raw = await _post_json(url, payload, headers)
    record["http_status"] = status

    if status != 200:
        # 服务商报错可能回显密钥或用户问题，不向群聊或日志透传正文。
        reason = {
            400: "请求参数不受支持，请检查模型和参数配置",
            401: "接口鉴权失败，请管理员检查 API Key",
            402: "接口余额不足，请管理员检查账户额度",
            403: "接口访问被拒绝，请管理员检查权限",
            404: "接口或模型不存在，请管理员检查地址和模型名",
            429: "接口请求过于频繁或额度受限，请稍后再试",
        }.get(status, "模型服务暂时不可用，请稍后再试")
        raise LLMError(f"{reason}（HTTP {status}）")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise LLMError("接口返回内容无法解析") from e

    if not isinstance(data, dict):
        raise LLMError("接口返回格式不正确")
    _update_usage(record, data.get("usage"))
    if data.get("error"):
        raise LLMError("模型服务返回错误，请管理员检查接口配置与账户状态")
    choices = data.get("choices") or []
    if not choices:
        raise LLMError("接口未返回解读内容")

    if not isinstance(choices, list) or not isinstance(choices[0], dict):
        raise LLMError("接口返回格式不正确")
    message = choices[0].get("message") or {}
    if not isinstance(message, dict):
        raise LLMError("接口返回格式不正确")
    content = message.get("content")
    if isinstance(content, list):  # 少数网关返回分段内容
        content = "".join(
            part["text"] for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )
    if not isinstance(content, str) or not content.strip():
        raise LLMError("接口返回的解读内容为空")

    return _clean_content(content)


async def generate_reading(prompt: str) -> str:
    """带上占卜师人设，让大模型生成一段解读。"""
    system_prompt = (config.batarot_llm_system_prompt or "").strip() or DEFAULT_SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    return await chat_completion(messages)


# ----------------------------------------------------------------------
# 提示词构造
# ----------------------------------------------------------------------


def _name_with_en(card_name: str, card_en_name: str = "") -> str:
    card_en_name = (card_en_name or "").strip()
    return f"{card_name}（{card_en_name}）" if card_en_name else card_name


def _question_line(question: str = "") -> str:
    question = (question or "").strip()[:config.batarot_llm_max_question_chars]
    if question:
        return f"老师提出的问题是：{question}"
    return "老师没有提出具体问题，请围绕抽到的牌给出整体解读。"


def build_tarot_prompt(
    *,
    card_name: str,
    card_en_name: str = "",
    position: str = "正位",
    meaning: str = "",
    question: str = "",
) -> str:
    """单张塔罗牌的解读提示词。"""
    return "\n".join(
        [
            "我抽到了一张塔罗牌，请你为我解读。",
            f"牌面：{_name_with_en(card_name, card_en_name)}",
            f"位置：{position}",
            f"牌义：{meaning}",
            _question_line(question),
        ]
    )


def build_spread_prompt(
    *,
    spread_name: str,
    cards: List[Dict[str, str]],
    question: str = "",
) -> str:
    """牌阵占卜的解读提示词。

    ``cards`` 每一项包含 ``position``（牌阵位置含义）、``name``、``en_name``、
    ``direction``（正位/逆位）与 ``meaning``。
    """
    lines = [f"我抽到的牌阵是：{spread_name}", "牌阵中的牌如下："]
    for index, card in enumerate(cards, start=1):
        lines.append(
            f"{index}. {card.get('position', '')}："
            f"{_name_with_en(card.get('name', ''), card.get('en_name', ''))}"
            f"（{card.get('direction', '')}），牌义：{card.get('meaning', '')}"
        )
    lines.append(_question_line(question))
    lines.append("请结合每张牌所在的牌阵位置，给出整体的解读与建议。")
    return "\n".join(lines)


def build_fortune_prompt(
    *,
    card_name: str,
    card_en_name: str = "",
    position: str,
    meaning: str,
    question: str = "",
) -> str:
    """固定每日幸运牌的解读提示词。"""
    return "\n".join(
        [
            "我抽到了今日的幸运牌，请结合牌面给出简洁的解读和建议。",
            f"幸运牌：{_name_with_en(card_name, card_en_name)}（{position}）",
            f"牌义：{meaning}",
            _question_line(question),
            "请只解读牌面、正逆位和牌义，不讨论或编造游戏积分、幸运值及排名。",
        ]
    )


def build_reading_prompt(
    *,
    card_name: str,
    card_en_name: str = "",
    meaning_up: str = "",
    meaning_down: str = "",
    description: str = "",
    question: str = "",
) -> str:
    """卡牌解读（原画师解读 + AI 扩展）的提示词。"""
    description = (description or "").strip()
    if len(description) > 800:
        description = f"{description[:800]}……"
    return "\n".join(
        [
            "我想深入了解一张塔罗牌，请你为我解读。",
            f"牌面：{_name_with_en(card_name, card_en_name)}",
            f"正位含义：{meaning_up}",
            f"逆位含义：{meaning_down}",
            f"原画师的解读：{description}",
            _question_line(question),
            "请用通俗的语言讲清这张牌的核心含义，并说明它在生活里可以怎么用。",
        ]
    )
