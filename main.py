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
# 天気（本山町）
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
# ダム画面スクショ
# ==============================
def take_dam_screenshot(wait_ms: int, out_png: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
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
# Geminiで貯水率取得
# ==============================
def pick_model_name():
    for m in genai.list_models():
        if "generateContent" in getattr(m, "supported_generation_methods", []):
            return m.name
    raise RuntimeError("Gemini model not found")

def read_rate_from_image(img_path: str, api_key: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        pick_model_name(),
        generation_config={"temperature": 0, "max_output_tokens": 256},
    )

    img_file = genai.upload_file(path=img_path)
    prompt = '画像から「貯水率(利水容量)」の数値だけをJSONで返す。{"rate": <number or null>}'
    response = model.generate_content([prompt, img_file])
    return response.text or ""

def get_sameura_rate_with_ai():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "--"

    for wait_ms, shot in [(4000, "shot1.png"), (12000, "shot2.png")]:
        try:
            take_dam_screenshot(wait_ms, shot)
            text = read_rate_from_image(shot, api_key)
            m = re.search(r"\{.*\}", text)
            if not m:
                continue
            data = json.loads(m.group(0))
            r = data.get("rate")
            if r is not None:
                return f"{float(r):.2f}"
        except Exception:
            continue

    return "--"

# ==============================
# 背景：毎日ランダム固定
# ==============================
def pick_daily_background(now: datetime) -> str:
    candidates = sorted(Path("images").glob("bg_*.jpg"))
    if not candidates:
        return "background.jpg"

    seed = int(now.strftime("%Y%m%d"))  # ← その日固定
    rng = random.Random(seed)
    return str(rng.choice(candidates))

# ==============================
# 画像生成
# ==============================
def create_image(rate: str, weather: str):
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)

    bg_path = pick_daily_background(now)
    img = Image.open(bg_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype("font.ttf", 60)
    font_mid = ImageFont.truetype("font.ttf", 70)
    font_big = ImageFont.truetype("font.ttf", 130)

    style = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

    draw.text((100, 80), now.strftime("%Y年%m月%d日 %H:%M"), font=font, **style)
    draw.text((100, 155), weather, font=font, **style)
    draw.text((100, 300), "早明浦ダム 貯水率", font=font_mid, **style)
    draw.text((120, 380), f"{rate}%", font=font_big, **style)

    img.save("result.jpg", quality=95)

# ==============================
# main
# ==============================
if __name__ == "__main__":
    weather = get_weather_motoyama()
    rate = get_sameura_rate_with_ai()
    create_image(rate, weather)
