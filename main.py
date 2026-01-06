import os
import json
import re
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai

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

# ------------------------------
# Gemini utilities
# ------------------------------
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
    m = re.search(r"\{.*", t, flags=re.DOTALL)
    if m:
        t = m.group(0)
    if t.endswith("}"):
        return t
    if t.endswith(","):
        t = t[:-1]
    return t + "}"


# ------------------------------
# Weather (Motoyama)
# ------------------------------
def get_weather_motoyama():
    """
    表示用に短く整形した天気文字列を返す
    例: "本山町　快晴 2.2℃"
    """
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


# ------------------------------
# Sameura Dam rate
# ------------------------------
def get_sameura_rate_with_ai():
    rate = "--"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return rate

    with open("ai_raw.txt", "w", encoding="utf-8") as f:
        f.write("ai_raw placeholder\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2,
            locale="ja-JP",
        )
        page = context.new_page()
        page.goto(DAM_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        page.screenshot(path="temp_shot.png")
        browser.close()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        pick_model_name(),
        generation_config={"temperature": 0, "max_output_tokens": 256},
    )

    img_file = genai.upload_file(path="temp_shot.png")

    prompt = """
出力は JSON のみ。
画像から「貯水率(利水容量)」の数値だけを読む。
{"rate": <number>}
""".strip()

    response = model.generate_content([prompt, img_file])
    text = extract_text_from_response(response)

    with open("ai_raw.txt", "w", encoding="utf-8") as f:
        f.write(text)

    fixed = salvage_json(text)
    try:
        data = json.loads(fixed)
        r = float(data.get("rate"))
        if 0 <= r <= 100:
            rate = f"{r:.2f}"
    except Exception:
        pass

    return rate


# ------------------------------
# Image
# ------------------------------
def create_image(rate: str, weather: str):
    jst = timezone(timedelta(hours=9), "JST")
    date_str = datetime.now(jst).strftime("%Y年%m月%d日 %H:%M")

    img = Image.open("background.jpg")
    draw = ImageDraw.Draw(img)

    font = "font.ttf"
    f_date = ImageFont.truetype(font, 60)
    f_weather = ImageFont.truetype(font, 52)
    f_sub = ImageFont.truetype(font, 70)
    f_main = ImageFont.truetype(font, 130)

    line = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

    draw.text((100, 80), date_str, font=f_date, **line)
    draw.text((100, 155), weather, font=f_weather, **line)

    draw.text((100, 300), "早明浦ダム 貯水率", font=f_sub, **line)
    draw.text((120, 380), f"{rate}%", font=f_main, **line)

    img.save("result.jpg")


if __name__ == "__main__":
    weather = get_weather_motoyama()
    rate = get_sameura_rate_with_ai()
    create_image(rate, weather)
