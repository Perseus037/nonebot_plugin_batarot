from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import random
import time

from nonebot.adapters import Event, Message
from nonebot.adapters.onebot.v11 import Bot, Message as OneBotMessage, MessageEvent, MessageSegment, GroupMessageEvent
from nonebot.params import CommandArg
from nonebot_plugin_saa import Image, Text, MessageFactory, SaaTarget
from nonebot.log import logger
from nonebot.matcher import current_bot

from .config import config
from .commands import tarot, tarot_spread, tarot_fortune, tarot_reading
from .state import StateError, StateStore
from .llm import (
    LLMError,
    build_fortune_prompt,
    build_reading_prompt,
    build_spread_prompt,
    build_tarot_prompt,
    generate_reading,
)
from .utils import (
    load_tarot_data,
    load_spread_data,
    random_tarot_card,
    match_card_key,
    get_card_en_name,
    load_image_as_base64,
    load_image_as_bytes,
    parse_card_query,
)

# 记录每位用户上次调用 AI 解读的时间（用于冷却限制）
_llm_last_used: dict = {}
_llm_inflight: set = set()
_state_store = None
_fortune_tasks: dict = {}


def _today() -> str:
    return datetime.now(timezone(timedelta(hours=config.batarot_day_utc_offset))).date().isoformat()


def _user_key(event: Event) -> str:
    try:
        bot = current_bot.get()
        platform = bot.adapter.get_name()
        bot_id = bot.self_id
    except LookupError:
        platform = type(event).__module__
        bot_id = str(getattr(event, "self_id", ""))
    group = getattr(event, "group_id", None)
    if group is None:
        group = getattr(event, "channel_id", None)
    scope = f"group:{group}" if group is not None else "private"
    return f"{platform}:{bot_id}:{scope}:{event.get_user_id()}"


def _store() -> StateStore:
    global _state_store
    path = Path(config.batarot_data_file).resolve()
    if _state_store is None or _state_store.path != path:
        _state_store = StateStore(path)
    return _state_store


@dataclass(frozen=True)
class _AIResult:
    text: str
    status: str


def _position_text(direction: str) -> str:
    """把内部的正逆位标记转成展示/提示词用的文字。"""
    return "正位" if direction == "up" else "逆位"


async def _request_ai_result(event: Event, prompt: str, *, daily: bool = False,
                             day: str = "") -> _AIResult:
    if not config.batarot_llm_enabled:
        return _AIResult("", "disabled")
    if not config.batarot_llm_api_key.strip() or not config.batarot_llm_model.strip():
        return _AIResult("🔮 AI 解读暂未配置完成。", "skipped")

    user_id = _user_key(event)
    if daily:
        deadline = time.monotonic() + float(config.batarot_llm_timeout) + 2.0
        while user_id in _llm_inflight or len(_llm_inflight) >= config.batarot_llm_max_concurrency:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return _AIResult("🔮 等待已有 AI 解读结束超时，今日解读未生成。", "skipped")
            await asyncio.sleep(min(0.05, remaining))
            if time.monotonic() >= deadline:
                return _AIResult("🔮 等待已有 AI 解读结束超时，今日解读未生成。", "skipped")
    else:
        if user_id in _llm_inflight:
            return _AIResult("🔮 你的上一条 AI 解读还在处理中。", "skipped")
        if len(_llm_inflight) >= config.batarot_llm_max_concurrency:
            return _AIResult("🔮 当前解读较多，请稍后再试。", "skipped")
    cooldown = max(int(config.batarot_llm_cooldown or 0), 0)
    now = time.monotonic()

    if cooldown > 0 and not daily:
        last_used = _llm_last_used.get(user_id)
        if last_used is not None and now - last_used < cooldown:
            remain = int(cooldown - (now - last_used)) + 1
            return _AIResult(f"🔮 AI 解读冷却中，请在 {remain} 秒后再试。", "skipped")

        # 顺手清理过期记录，避免字典无限增长
        if len(_llm_last_used) > 1024:
            for key in [k for k, v in _llm_last_used.items() if now - v > 3600]:
                _llm_last_used.pop(key, None)

    _llm_inflight.add(user_id)
    try:
        if not daily and not await _store().reserve_ai(user_id, day or _today(), config.batarot_llm_daily_limit):
            return _AIResult(f"🔮 你在当前群聊今日的 {config.batarot_llm_daily_limit} 次占卜 AI 解读额度已用完。", "skipped")
        _llm_last_used[user_id] = time.monotonic()
        reading = await generate_reading(prompt)
    except StateError:
        logger.error("batarot: 状态文件不可读写，已跳过 AI 请求")
        return _AIResult("🔮 暂时无法保存解读额度，请联系管理员。", "skipped")
    except LLMError as e:
        logger.warning(f"batarot: AI 解读失败：{e}")
        return _AIResult(f"🔮 AI 解读暂时不可用（{e}）", "failed")
    except Exception as e:  # pragma: no cover - 兜底，避免影响正常占卜流程
        # 异常正文、堆栈局部变量可能包含 Key 或请求内容。
        logger.error(f"batarot: AI 解读出现未知错误（{type(e).__name__}）")
        return _AIResult("🔮 AI 解读出现未知错误，请检查机器人日志。", "failed")
    finally:
        _llm_inflight.discard(user_id)

    return _AIResult(f"🔮 AI 塔罗解读：\n{reading}", "completed")


async def _request_ai_text(event: Event, prompt: str) -> str:
    return (await _request_ai_result(event, prompt)).text


async def _send_ai_text(text: str) -> None:
    """把 AI 解读作为一条独立消息发出（空字符串表示未开启，直接跳过）。"""
    if not text:
        return
    try:
        await MessageFactory(Text(text)).send()
    except Exception as e:  # pragma: no cover - 发送失败不影响主流程
        logger.error(f"batarot: AI 解读发送失败：{e}")


@tarot.handle()
async def handle_tarot(event: Event, args: Message = CommandArg()):
    cards_dict, tarot_urls = load_tarot_data()
    card_name, position, card_meaning, card_url = random_tarot_card(cards_dict, tarot_urls)

    # 构建回复文字
    reply_text = Text(f"塔罗牌名称: {card_name}\n" + ("正位" if position == "up" else "逆位") + f"含义: {card_meaning}\n")
    # 初始化消息工厂
    reply = MessageFactory([reply_text])
    
    if card_url:
        
        image_bytes = await load_image_as_bytes(card_url, position != "up")
        if image_bytes:
            # 图片加载成功则追加图片到消息工厂
            reply.append(Image(image_bytes))  # type: ignore

        else:
            # 图片加载失败则追加加载失败消息到消息工厂
            reply.append(Text("图片加载失败"))

    await reply.send(reply=True)

    # 大模型辅助解读（未开启时不会发送任何额外消息）
    question = args.extract_plain_text().strip()
    card_key = match_card_key(cards_dict, card_name)
    prompt = build_tarot_prompt(
        card_name=card_name,
        card_en_name=get_card_en_name(cards_dict, card_key) if card_key else "",
        position=_position_text(position),
        meaning=card_meaning,
        question=question,
    )
    await _send_ai_text(await _request_ai_text(event, prompt))

    await tarot.finish()

@tarot_spread.handle()
async def handle_tarot_spread(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    spread_data = load_spread_data()
    cards_dict, tarot_urls = load_tarot_data()

    chosen_spread = random.choice(list(spread_data["formations"].keys()))
    spread_info = spread_data["formations"][chosen_spread]

    selected_cards = random.sample(list(cards_dict.keys()), spread_info["cards_num"])
    # 一次选定整套位置，随后按牌序逐一对应。
    representations = random.choice(spread_info["representations"])
    nodes = []
    ai_cards = []

    # 添加起始信息节点
    nodes.append({
        "type": "node",
        "data": {
            "name": "塔罗占卜",
            "uin": str(event.self_id),  # 确保是字符串类型
            "content": f"老师，你抽到的牌阵是：{chosen_spread}\n"
        }
    })

    # 遍历选中的卡片并生成消息
    for i, card_key in enumerate(selected_cards):
        card = cards_dict[card_key]
        card_name = card['name_cn']
        card_url = tarot_urls.get(f"tarot_{card_key}")
        representation = representations[i]

        if random.random() < 0.5:
            position = "正位"
            card_meaning = card['meaning']['up']
        else:
            position = "逆位"
            card_meaning = card['meaning']['down']

        card_message = f"{representation}：{card_name}（{position}）\n解释：{card_meaning}\n"

        if card_url:
            base64_image = await load_image_as_base64(card_url, position == "逆位")
            if base64_image:
                card_message += MessageSegment.image(base64_image)
            else:
                card_message += "图片加载失败\n"

        nodes.append({
            "type": "node",
            "data": {
                "name": "塔罗占卜",
                "uin": str(event.self_id),  # 确保是字符串类型
                "content": card_message
            }
        })

        ai_cards.append({
            "position": representation,
            "name": card_name,
            "en_name": get_card_en_name(cards_dict, card_key),
            "direction": position,
            "meaning": card_meaning,
        })

    combined_message = OneBotMessage()
    for node in nodes:
        if combined_message:
            combined_message += "\n"
        combined_message += node['data']['content']

    if isinstance(event, GroupMessageEvent) and not config.forward_mode:
        try:
            await bot.send_group_forward_msg(group_id=event.group_id, messages=nodes)
        except Exception as e:
            logger.warning(f"batarot: 合并转发失败，改为一条图文消息（{type(e).__name__}）")
            await bot.send(event, combined_message)
    else:
        await bot.send(event, combined_message)

    # 大模型辅助解读（未开启时不会发送任何额外消息）
    prompt = build_spread_prompt(
        spread_name=chosen_spread,
        cards=ai_cards,
        question=args.extract_plain_text().strip(),
    )
    await _send_ai_text(await _request_ai_text(event, prompt))

    await tarot_spread.finish()



@tarot_fortune.handle()
async def handle_daily_fortune(event: Event, args: Message = CommandArg()):
    key, day = _user_key(event), _today()
    task_key = (key, day)
    task = _fortune_tasks.get(task_key)
    joined = task is not None
    if task is None:
        task = asyncio.create_task(_daily_fortune(event, key, day, args.extract_plain_text().strip()))
        _fortune_tasks[task_key] = task

        def completed(done):
            if _fortune_tasks.get(task_key) is done:
                _fortune_tasks.pop(task_key, None)
            if not done.cancelled():
                done.exception()

        task.add_done_callback(completed)
    try:
        record, created = await asyncio.shield(task)
    except StateError:
        logger.error("batarot: 幸运牌状态文件不可读写，未重置存档")
        await MessageFactory(Text("幸运牌存档暂时不可用，请联系管理员。")).send()
        return

    prefix = "今天已经抽取过幸运牌了。\n\n" if joined or not created else ""
    text = (f"{prefix}今日幸运牌：{record['name']}（{_position_text(record['position'])}）\n"
            f"{record['meaning']}\n\n幸运值：{record['delta']:+d}\n累计幸运值：{record['total']}")
    reply = MessageFactory(Text(text))
    if record.get("image"):
        image_bytes = await load_image_as_bytes(record["image"], record["position"] == "down")
        if image_bytes:
            reply.append(Image(image_bytes))
    ai_text = record.get("ai_text", "")
    if not ai_text and record.get("ai_status") == "pending":
        ai_text = "今日解读未完成，已保留本次牌面。"
    if ai_text:
        reply.append(Text("\n\n" + ai_text))
    await reply.send(reply=True)
    await tarot_fortune.finish()


def _draw_lucky_card():
    cards_dict, tarot_urls = load_tarot_data()
    card_key = random.choice(list(cards_dict.keys()))
    card = cards_dict[card_key]
    position = random.choice(["up", "down"])
    if position == "up":
        delta = random.randint(1, config.batarot_luck_max) if config.batarot_luck_max else 0
    else:
        delta = random.randint(config.batarot_luck_min, -1) if config.batarot_luck_min else 0
    return {"card_key": str(card_key), "name": card["name_cn"],
            "en_name": get_card_en_name(cards_dict, card_key), "position": position,
            "meaning": card["meaning"][position], "image": tarot_urls.get(f"tarot_{card_key}", ""),
            "delta": delta, "ai_status": "pending" if config.batarot_llm_enabled else "disabled",
            "ai_text": ""}


async def _daily_fortune(event, key, day, question):
    store = _store()
    record, created = await store.get_or_draw(key, day, _draw_lucky_card, config.batarot_initial_luck)
    if not created or record["ai_status"] != "pending":
        return record, created
    prompt = build_fortune_prompt(
        card_name=record["name"], card_en_name=record["en_name"],
        position=_position_text(record["position"]), meaning=record["meaning"],
        delta=record["delta"], total=record["total"], question=question,
    )
    try:
        result = await _request_ai_result(event, prompt, daily=True, day=day)
    except asyncio.CancelledError:
        await store.complete_daily(key, day, "今日解读未完成，已保留本次牌面。", "failed")
        raise
    text = result.text
    if result.status == "skipped":
        text = result.text + "\n已保留本次牌面；当天不会重复请求 AI。"
    await store.complete_daily(key, day, text, result.status)
    record.update(ai_text=text, ai_status=result.status)
    return record, True


@tarot_reading.handle()
async def handle_tarot_reading(event: Event, args: Message = CommandArg()):
    cards_dict, tarot_urls = load_tarot_data()

    # 参数形如「7」「愚者」「愚者 我最近的工作怎么样」
    arg_text = args.extract_plain_text().strip()
    specific_card_key = None
    question = ""

    if not arg_text:
        specific_card_key = random.choice(list(cards_dict.keys()))
    else:
        specific_card_key, question = parse_card_query(cards_dict, arg_text)

    if specific_card_key:
        card = cards_dict[specific_card_key]
        card_name = card['name_cn']
        card_description = "\n".join(card['description'])
        card_url = tarot_urls.get(f"tarot_{specific_card_key}")

        # 创建消息工厂
        reply = MessageFactory(Text(f"塔罗牌名称: {card_name}\n原作者解读:\n{card_description}\n"))

        # 追加图片信息
        if card_url:
     
            image_bytes = await load_image_as_bytes(card_url)
            if image_bytes:
                reply.append(Image(image_bytes))  # type: ignore
            else:
                reply += "图片加载失败"
    else:
        reply = MessageFactory(Text("未找到指定的塔罗牌或输入格式错误，请输入正确的卡牌编号或名称。\n"))

    await reply.send(reply=True)

    # 大模型辅助解读（未开启时不会发送任何额外消息）
    if specific_card_key:
        card = cards_dict[specific_card_key]
        prompt = build_reading_prompt(
            card_name=card['name_cn'],
            card_en_name=get_card_en_name(cards_dict, specific_card_key),
            meaning_up=card['meaning']['up'],
            meaning_down=card['meaning']['down'],
            description="\n".join(card['description']),
            question=question,
        )
        await _send_ai_text(await _request_ai_text(event, prompt))

    await tarot_reading.finish()
