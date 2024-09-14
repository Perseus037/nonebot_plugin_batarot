import random

from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment, GroupMessageEvent
from nonebot.internal.adapter import Bot as InternalBot
from nonebot.plugin import on_command
from nonebot_plugin_saa import Image, Text, MessageFactory, SaaTarget
from nonebot.log import logger

from .config import config
from .commands import tarot, tarot_spread, tarot_fortune, tarot_reading
from .utils import load_tarot_data, load_spread_data, random_tarot_card, send_image_as_base64, load_fortune_descriptions, send_image_as_bytes

@tarot.handle()
async def handle_tarot():
    cards_dict, tarot_urls = load_tarot_data()
    card_name, card_meaning_up, card_meaning_down, card_url = random_tarot_card(cards_dict, tarot_urls)

    # 构建回复文字
    reply_text = Text(f"塔罗牌名称: {card_name}\n正位含义: {card_meaning_up}\n逆位含义: {card_meaning_down}\n")
    # 初始化消息工厂
    reply = MessageFactory([reply_text])
    
    if card_url:
        
        image_bytes = send_image_as_bytes(card_url)
        if image_bytes:
            # 图片加载成功则追加图片到消息工厂
            reply.append(Image(image_bytes))  # type: ignore
        else:
            # 图片加载失败则追加加载失败消息到消息工厂
            reply.append(Text("图片加载失败"))

    await reply.send(reply=True)
    await tarot.finish()

@tarot_spread.handle()
async def handle_tarot_spread(bot: Bot, event: MessageEvent):
    spread_data = load_spread_data()
    cards_dict, tarot_urls = load_tarot_data()

    chosen_spread = random.choice(list(spread_data["formations"].keys()))
    spread_info = spread_data["formations"][chosen_spread]

    selected_cards = random.sample(list(cards_dict.keys()), spread_info["cards_num"])
    nodes = []

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
        combined_message = Message()
        for node in nodes:
            combined_message.append(node['data']['content'])

        await bot.send(event, combined_message)

    await tarot_spread.finish()



@tarot_fortune.handle()
async def handle_daily_fortune():
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
    await tarot_fortune.finish()


@tarot_reading.handle()
async def handle_tarot_reading(event: MessageEvent):
    cards_dict, tarot_urls = load_tarot_data()

    user_input = str(event.get_message()).strip()
    specific_card_key = None

    if user_input == "ba塔罗牌解读":
        specific_card_key = random.choice(list(cards_dict.keys()))

    elif user_input.startswith("ba塔罗牌解读 "):
        specific_card_input = user_input.split(" ", 1)[1].strip()

        if specific_card_input.isdigit() and specific_card_input in cards_dict:
            specific_card_key = specific_card_input
        else:
            specific_card_key = next(
                (key for key, card in cards_dict.items() if card['name_cn'].lower() == specific_card_input.lower()),
                None)

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
    await tarot_reading.finish()
