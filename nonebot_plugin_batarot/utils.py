import json
import os
import random
import aiohttp
import base64
from io import BytesIO

current_dir = os.path.dirname(os.path.abspath(__file__))


def load_tarot_data():
    with open(os.path.join(current_dir, "batarot.json"), 'r', encoding='utf-8') as file:
        batarot_json = json.load(file)
    with open(os.path.join(current_dir, "batarot_url.json"), 'r', encoding='utf-8') as file:
        batarot_urls = json.load(file)
    return batarot_json['cards'], batarot_urls


def load_spread_data():
    with open(os.path.join(current_dir, "batarot_spread.json"), 'r', encoding='utf-8') as file:
        batarot_spread = json.load(file)
        return batarot_spread


def random_tarot_card(cards_dict, urls_dict):
    card_key = random.choice(list(cards_dict.keys()))
    card = cards_dict[card_key]
    card_name = card['name_cn']
    card_meaning_up = card['meaning']['up']
    card_meaning_down = card['meaning']['down']

    url_key = f"tarot_{card_key}"
    card_url = urls_dict.get(url_key)

    return card_name, card_meaning_up, card_meaning_down, card_url


def load_fortune_descriptions():
    with open(os.path.join(current_dir, "batarot_fortune.json"), 'r', encoding='utf-8') as file:
        return json.load(file)


# 以base64格式发送图片
async def send_image_as_base64(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                buffered = BytesIO(image_data)
                b64_encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')
                return f"base64://{b64_encoded}"
            else:
                return None

# 返回BytesIO对象图片
async def send_image_as_bytes(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                buffered = BytesIO(image_data)
                return buffered
            else:
                return None
