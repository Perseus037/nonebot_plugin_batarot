import asyncio
import base64
from functools import lru_cache, partial
from io import BytesIO
import json
import os
from pathlib import Path
import random

from nonebot.log import logger
from PIL import Image

current_dir = os.path.dirname(os.path.abspath(__file__))
image_dir = os.path.join(current_dir, "image")
_image_slots = None


@lru_cache(maxsize=4)
def _load_json(filename):
    with open(os.path.join(current_dir, filename), encoding="utf-8") as file:
        return json.load(file)


def load_tarot_data():
    return _load_json("batarot.json")["cards"], _load_json("batarot_url.json")


def load_spread_data():
    return _load_json("batarot_spread.json")


def load_fortune_descriptions():
    return _load_json("batarot_fortune.json")


def random_tarot_card(cards_dict, urls_dict):
    card_key = random.choice(list(cards_dict))
    card = cards_dict[card_key]
    direction = "up" if random.choice([True, False]) else "down"
    return card["name_cn"], direction, card["meaning"][direction], urls_dict.get(f"tarot_{card_key}")


def match_card_key(cards_dict, text: str):
    lowered = (text or "").strip().casefold()
    for key, card in cards_dict.items():
        if lowered in {str(key).casefold(), str(card.get("name_cn", "")).casefold(),
                       str(card.get("name_en", "")).casefold()} and lowered:
            return key
    return None


def parse_card_query(cards_dict, text: str):
    text = (text or "").strip()
    aliases = [(str(name).strip(), key) for key, card in cards_dict.items()
               for name in (key, card.get("name_cn", ""), card.get("name_en", "")) if name]
    for name, key in sorted(aliases, key=lambda pair: len(pair[0]), reverse=True):
        if text[:len(name)].casefold() == name.casefold():
            tail = text[len(name):]
            if not tail or tail[0].isspace():
                return key, tail.strip()
    return None, ""


def get_card_en_name(cards_dict, card_key: str) -> str:
    return str((cards_dict.get(card_key) or {}).get("name_en", "")).strip()


def rotate_image_180(image_bytes: BytesIO) -> BytesIO:
    with Image.open(image_bytes) as image:
        with image.transpose(getattr(Image, "Transpose", Image).ROTATE_180) as rotated:
            output = BytesIO()
            rotated.save(output, format=image.format or "PNG")
    output.seek(0)
    return output


@lru_cache(maxsize=16)
def _read_image_cached(path: str, modified: int, size: int, is_reversed: bool) -> bytes:
    raw = Path(path).read_bytes()
    if is_reversed:
        return rotate_image_180(BytesIO(raw)).getvalue()
    with Image.open(BytesIO(raw)) as image:
        image.verify()
    return raw


def _read_image(image_path: str, is_reversed: bool = False):
    try:
        path = Path(image_dir) / image_path
        stat = path.stat()
        return _read_image_cached(str(path), stat.st_mtime_ns, stat.st_size, is_reversed)
    except (OSError, ValueError, SyntaxError):
        logger.warning("batarot: 牌图不可读取：{}", image_path)
        return None


def send_image_as_bytes(image_path: str, is_reversed: bool = False):
    raw = _read_image(image_path, is_reversed)
    return BytesIO(raw) if raw else None


def send_image_as_base64(image_path: str, is_reversed: bool = False):
    raw = _read_image(image_path, is_reversed)
    return "base64://" + base64.b64encode(raw).decode("ascii") if raw else None


async def _image_job(function, image_path, is_reversed):
    global _image_slots
    if _image_slots is None:
        _image_slots = asyncio.Semaphore(2)
    async with _image_slots:
        future = asyncio.get_running_loop().run_in_executor(None, partial(function, image_path, is_reversed))
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            try:
                await future
            finally:
                raise


async def load_image_as_bytes(image_path: str, is_reversed: bool = False):
    return await _image_job(send_image_as_bytes, image_path, is_reversed)


async def load_image_as_base64(image_path: str, is_reversed: bool = False):
    return await _image_job(send_image_as_base64, image_path, is_reversed)
