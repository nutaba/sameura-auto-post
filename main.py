import os
import json
import re
import requests
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai

# ==============================
# 設定
# ==============================
DAM_URL = "https://suibo-kouho.suibou.pref.kochi.lg.jp/suibou/graph/model_dam_8.html?unq=12473017225"

# 本山町（固定座標）
MOTOYAMA_LAT = 33.75
MOTOYAMA_LON = 133.5833

WMO_MAP = {
    0: "快晴", 1: "晴れ", 2: "薄曇り", 3: "くもり",
    45: "霧", 48: "霧",
    51: "霧雨", 53: "霧雨", 55: "霧雨",
    61: "小雨", 63: "雨", 65: "大雨",
    71: "小雪", 73: "雪", 75: "大雪",
    80: "にわか雨", 81: "にわか雨",
    95: "雷雨",
}

# ==============================
# Gemini utilities
# ==============================
def pick_model_name():
    for m in genai.list_models():
        methods = getattr(m, "supported_generation_methods", []) or []
        if "generateContent" in methods:
            return m.name
    raise RuntimeError("generateContent 対応の Gemini モデルが見つかりません")

def extract_text_from_response(response):
    try:
        cand = response.candidates[0]
        parts = getattr(cand.content, "parts", []) or []
        text = "".join([getattr(p, "text", "") for p in parts]).strip()
        if text:
            return text
    except Exception:
        pass
    return (getattr(response, "text", "") or "").strip()

def salvage_json(text: str):
    t = (text or "").strip()
    m = re.search(r"\{.*\}", t, flags=re.DOTALL)
    if not m:
        return "{}"
    return m.group(0)

# ==============================
# Weather (Motoyama)
# ==============================
def get_weather_motoyama():
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": MOTOYAMA_LAT,
            "longitude": MOTOYAMA_LON,
            "current": "temperature_2m,weather_code",
            "timezone": "Asia/Tokyo",
        }
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        current = data.get("current", {})
        temp = current.get("temperature_2m")
        wcode = current.get("weather_code")

        cond = WMO_MAP.get(int(wcode), "不明") if wcode is not None else "不明"
        temp_str = f"{temp:.1f}℃" if isinstance(temp, (int, float)) else "--℃"
        return f"本山町　{cond} {temp_str}"
    except Exception:
        return "本山町　天気不明"

# ==============================
# Screenshot
# ==============================
def take_dam_screenshot(wait_ms: int, out_png: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2,
            locale="ja-JP",
        )
        page = context.new_page()
        page.goto(DAM_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(wait_ms)
        page.screenshot(path=out_png)
        browser.close()

# ==============================
# Sameura Dam rate via Gemini
# ==============================
def read_rate_from_image(img_path: str, api_key: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        pick_model_name(),
        generation_config={"temperature": 0, "max_output_tokens": 256},
    )

    img_file = genai.upload_file(path=img_path)

    prompt = """
出力は生のJSONのみ。
画像から「貯水率(利水容量)」の数値だけを読み取る（%なし）。
{"rate": <number or null>}
""".strip()

    response = model.generate_content([prompt, img_file])
    return extract_text_from_response(response)

def get_sameura_rate_with_ai():
    rate = "--"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return rate

    attempts = [
        (4000, "temp_shot.png"),
        (12000, "temp_shot2.png"),
    ]

    for idx, (wait_ms, shot_name) in enumerate(attempts, start=1):
        try:
            take_dam_screenshot(wait_ms, shot_name)
            text = read_rate_from_image(shot_name, api_key)

            fixed = salvage_json(text)
            data = json.loads(fixed)

            r = data.get("rate")
            if r is None:
                continue

            rf = float(r)
            if 0 <= rf <= 100:
                rate = f"{rf:.2f}"
                break

        except Exception:
            continue

    return rate

# ==============================
# Background picker（1分ごと）
# ==============================
def pick_background_per_minute(now: datetime) -> str:
    candidates = sorted(Path("images").glob("bg_*.jpg"))
    if not candidates:
        return "background.jpg"

    seed = int(now.strftime("%Y%m%d%H%M"))
    rng = random.Random(seed)
    return str(rng.choice(candidates))

# ==============================
# Image composition
# ==============================
def create_image(rate: str, weather: str):
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    date_str = now.strftime("%Y年%m月%d日 %H:%M")

    bg_path = pick_background_per_minute(now)
    img = Image.open(bg_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype("font.ttf", 60)
    font_big = ImageFont.truetype("font.ttf", 130)
    font_mid = ImageFont.truetype("font.ttf", 70)

    style = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

    draw.text((100, 80), date_str, font=font, **style)
    draw.text((100, 155), weather, font=font, **style)
    draw.text((100, 300), "早明浦ダム 貯水率", font=font_mid, **style)
    draw.text((120, 380), f"{rate}%", font=font_big, **style)

    img.save("result.jpg", quality=95)

    with open("bg_used.txt", "w", encoding="utf-8") as f:
        f.write(bg_path)

# ==============================
# main
# ==============================
if __name__ == "__main__":
    weather = get_weather_motoyama()
    rate = get_sameura_rate_with_ai()
    create_image(rate, weather)
