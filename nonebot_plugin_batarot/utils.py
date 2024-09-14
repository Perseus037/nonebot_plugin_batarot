import json
import os
import random
import base64
from io import BytesIO

current_dir = os.path.dirname(os.path.abspath(__file__))

# 图片文件夹路径
image_dir = os.path.join(current_dir, "image")


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

# 从本地读取图片并返回BytesIO
def send_image_as_bytes(image_path: str):
    local_image_path = os.path.join(image_dir, image_path)  
    if os.path.exists(local_image_path):
        with open(local_image_path, 'rb') as image_file:
            image_data = image_file.read()
            return BytesIO(image_data)
    else:
        print(f"Image not found at: {local_image_path}")  
        return None

# 从本地读取图片并以base64格式发送
def send_image_as_base64(image_path: str):
    local_image_path = os.path.join(image_dir, image_path)  
    if os.path.exists(local_image_path):
        with open(local_image_path, 'rb') as image_file:
            image_data = image_file.read()
            b64_encoded = base64.b64encode(image_data).decode('utf-8')
            return f"base64://{b64_encoded}"
    else:
        print(f"Image not found at: {local_image_path}")  
        return None
