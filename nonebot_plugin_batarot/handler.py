import random
import time

from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment, GroupMessageEvent
from nonebot.internal.adapter import Bot as InternalBot
from nonebot.params import CommandArg
from nonebot.plugin import on_command
from nonebot_plugin_saa import Image, Text, MessageFactory, SaaTarget
from nonebot.log import logger

from .config import config
from .commands import tarot, tarot_spread, tarot_fortune, tarot_reading
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
    send_image_as_base64,
    load_fortune_descriptions,
    send_image_as_bytes,
    rotate_image_180,
)

# 记录每位用户上次调用 AI 解读的时间（用于冷却限制）
_llm_last_used: dict = {}


def _position_text(direction: str) -> str:
    """把内部的正逆位标记转成展示/提示词用的文字。"""
    return "正位" if direction == "up" else "逆位"


async def _request_ai_text(event: Event, prompt: str) -> str:
    """按需请求大模型解读。

    - 未开启 AI 解读时返回空字符串（调用方直接跳过发送）；
    - 冷却中或调用失败时返回一段提示文本。
    """
    if not config.batarot_llm_enabled:
        return ""

    user_id = event.get_user_id()
    cooldown = max(int(config.batarot_llm_cooldown or 0), 0)
    now = time.monotonic()

    if cooldown > 0:
        last_used = _llm_last_used.get(user_id)
        if last_used is not None and now - last_used < cooldown:
            remain = int(cooldown - (now - last_used)) + 1
            return f"🔮 AI 解读冷却中，请在 {remain} 秒后再试。"

        # 顺手清理过期记录，避免字典无限增长
        if len(_llm_last_used) > 1024:
            for key in [k for k, v in _llm_last_used.items() if now - v > 3600]:
                _llm_last_used.pop(key, None)

        _llm_last_used[user_id] = now

    try:
        reading = await generate_reading(prompt)
    except LLMError as e:
        logger.warning(f"batarot: AI 解读失败：{e}")
        return f"🔮 AI 解读暂时不可用（{e}）"
    except Exception as e:  # pragma: no cover - 兜底，避免影响正常占卜流程
        logger.exception(f"batarot: AI 解读出现未知错误：{e}")
        return "🔮 AI 解读出现未知错误，请检查机器人日志。"

    return f"🔮 AI 塔罗解读：\n{reading}"


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
        
        image_bytes = send_image_as_bytes(card_url)
         # type: ignore
        if position != "up":
            # 如果是逆位则反转图片字节流
            image_bytes = rotate_image_180(image_bytes)
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
        representation = random.choice(spread_info["representations"])

        if random.random() < 0.5:
            position = "顺位"
            card_meaning = card['meaning']['up']
        else:
            position = "逆位"
            card_meaning = card['meaning']['down']

        card_message = f"{representation}：{card_name}（{position}）\n解释：{card_meaning}\n"

        if card_url:
            base64_image = send_image_as_base64(card_url)
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

    # 发送合并转发消息
    if isinstance(event, GroupMessageEvent):
        try:
            await bot.send_group_forward_msg(group_id=event.group_id, messages=nodes)
        except Exception as e:
            logger.error(f"Failed to send group forward message: {e}")
            await bot.send(event, "消息合并发送失败，逐条发送中…")
            # 如果合并失败，逐条发送
            for node in nodes:
                await bot.send(event, node['data']['content'])
    else:
        # 私聊逐条发送
        # 注意：节点内容可能是 str，也可能是 str 与图片消息段拼接后的 Message 对象，
        # 直接 append 会抛出 ValueError，这里统一用 += 拼接。
        combined_message = Message()
        for node in nodes:
            combined_message += node['data']['content']

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
    cards_dict, tarot_urls = load_tarot_data()
    card_key = random.choice(list(cards_dict.keys()))
    card = cards_dict[card_key]
    card_name = card['name_cn']
    card_url = tarot_urls.get(f"tarot_{card_key}")

    fortune_score = random.randint(1, 100)
    fortune_descriptions = load_fortune_descriptions()
    score_range = f"{(fortune_score - 1) // 10 * 10 + 1}-{(fortune_score - 1) // 10 * 10 + 10}"
    fortune_description = random.choice(fortune_descriptions[score_range])

    # 创建消息工厂
    reply = MessageFactory(
        Text(f"今日塔罗牌：{card_name}\n今日运势指数：{fortune_score}\n运势解读：{fortune_description}\n"))

    # 追加图片信息
    if card_url:

        image_bytes = send_image_as_bytes(card_url)
        if image_bytes:
            reply.append(Image(image_bytes))  # type: ignore
        else:
            reply += "图片加载失败"

    await reply.send(reply=True)

    # 大模型辅助解读（未开启时不会发送任何额外消息）
    prompt = build_fortune_prompt(
        card_name=card_name,
        card_en_name=get_card_en_name(cards_dict, card_key),
        score=fortune_score,
        description=fortune_description,
        question=args.extract_plain_text().strip(),
    )
    await _send_ai_text(await _request_ai_text(event, prompt))

    await tarot_fortune.finish()


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
        specific_card_key = match_card_key(cards_dict, arg_text)
        if specific_card_key is None:
            # 第一个词当作牌名，剩余部分当作要占卜的问题
            head, _, tail = arg_text.partition(" ")
            specific_card_key = match_card_key(cards_dict, head)
            if specific_card_key is not None:
                question = tail.strip()

    if specific_card_key:
        card = cards_dict[specific_card_key]
        card_name = card['name_cn']
        card_description = "\n".join(card['description'])
        card_url = tarot_urls.get(f"tarot_{specific_card_key}")

        # 创建消息工厂
        reply = MessageFactory(Text(f"塔罗牌名称: {card_name}\n原作者解读:\n{card_description}\n"))

        # 追加图片信息
        if card_url:
     
            image_bytes = send_image_as_bytes(card_url)
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
