import os
import time
import json
import re
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai

URL = "https://suibo-kouho.suibou.pref.kochi.lg.jp/suibou/graph/model_dam_8.html?unq=12473017225"


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

    t = t.rstrip()
    if t.endswith(","):
        t = t[:-1].rstrip()
    return t + "}"


# ------------------------------
# Weather (Motoyama, Kochi) via Open-Meteo
# ------------------------------
WMO_MAP = {
    0: "快晴", 1: "晴れ", 2: "薄曇り", 3: "くもり",
    45: "霧", 48: "霧",
    51: "霧雨", 53: "霧雨", 55: "霧雨",
    56: "凍る霧雨", 57: "凍る霧雨",
    61: "小雨", 63: "雨", 65: "大雨",
    66: "凍る雨", 67: "凍る雨",
    71: "小雪", 73: "雪", 75: "大雪",
    77: "霰",
    80: "にわか雨", 81: "にわか雨", 82: "激しいにわか雨",
    85: "にわか雪", 86: "激しいにわか雪",
    95: "雷雨", 96: "雷雨(雹)", 99: "雷雨(雹)",
}

def get_motoyama_latlon():
    # Open-Meteo geocoding (no key)
    q = "本山町 高知県"
    url = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(url, params={"name": q, "count": 1, "language": "ja", "format": "json"}, timeout=15)
    r.raise_for_status()
    data = r.json()
    results = data.get("results") or []
    if not results:
        raise RuntimeError("geocoding結果なし")
    return float(results[0]["latitude"]), float(results[0]["longitude"])

def get_weather_motoyama():
    """
    画像に載せる用の短い天気文字列を返す
    例: "本山町 天気: くもり 8.3℃ / 降水30%"
    """
    try:
        lat, lon = get_motoyama_latlon()

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
            "daily": "precipitation_probability_max",
            "timezone": "Asia/Tokyo",
        }
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        current = data.get("current") or {}
        daily = data.get("daily") or {}

        temp = current.get("temperature_2m")
        wcode = current.get("weather_code")
        pop_list = daily.get("precipitation_probability_max") or []
        pop = pop_list[0] if pop_list else None

        cond = WMO_MAP.get(int(wcode), "天気不明") if wcode is not None else "天気不明"
        temp_str = f"{temp:.1f}℃" if isinstance(temp, (int, float)) else "--℃"
        pop_str = f"{int(pop)}%" if isinstance(pop, (int, float)) else "--%"

        return f"本山町 天気: {cond} {temp_str} / 降水{pop_str}"

    except Exception as e:
        # 失敗しても画像生成は続ける
        return f"本山町 天気: --（取得失敗）"


# ------------------------------
# Dam rate via screenshot + Gemini
# ------------------------------
def get_rate_with_ai():
    print("--- 1. 早明浦ダムページを撮影中 ---")

    rate = "--"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY が未設定")
        return rate

    # ai_raw.txt は必ず作る
    with open("ai_raw.txt", "w", encoding="utf-8") as f:
        f.write("ai_raw placeholder\n")

    # Screenshot
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            context = browser.new_context(
                viewport={"width": 1400, "height": 900},
                device_scale_factor=2,
                locale="ja-JP",
            )
            page = context.new_page()
            page.goto(URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            page.screenshot(path="temp_shot_full.png", full_page=True)
            page.screenshot(path="temp_shot.png")

            browser.close()
    except Exception as e:
        with open("ai_raw.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[SCREENSHOT ERROR] {e}\n")
        print("スクショでエラー:", e)
        return rate

    print("--- 2. Geminiで貯水率を抽出中 ---")

    try:
        genai.configure(api_key=api_key)
        model_name = pick_model_name()
        print("使用するGeminiモデル:", model_name)

        model = genai.GenerativeModel(
            model_name,
            generation_config={"temperature": 0, "max_output_tokens": 512},
        )

        img_file = genai.upload_file(path="temp_shot.png")

        prompt = """
出力は 生のJSONのみ。```json 等のコードブロックは禁止。
画像から「貯水率(利水容量)」の数値だけを読み取る（%記号なし。例: 91.20）。
必ず1行で返す：{"rate": <number or null>}
改行禁止。読めない場合は null。
""".strip()

        response = model.generate_content([prompt, img_file])
        text = extract_text_from_response(response)

        if text.strip() in ("```json", "```", ""):
            retry_prompt = prompt + "\n今すぐJSON本文を1行で出力。"
            response = model.generate_content([retry_prompt, img_file])
            text = extract_text_from_response(response)

        print("AIの生回答:", repr(text))
        with open("ai_raw.txt", "w", encoding="utf-8") as f:
            f.write(text)

        fixed = salvage_json(text)
        try:
            data = json.loads(fixed)
        except Exception:
            data = {}

        r = data.get("rate")
        if r is not None:
            try:
                rf = float(r)
                if 0 <= rf <= 100:
                    rate = f"{rf:.2f}"
            except:
                pass

    except Exception as e:
        with open("ai_raw.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[GEMINI ERROR] {e}\n")
        print("Geminiでエラー:", e)

    return rate


# ------------------------------
# Image composition
# ------------------------------
def create_image(rate: str, weather_line: str):
    print("--- 3. 画像合成中 ---")

    jst = timezone(timedelta(hours=9), "JST")
    date_str = datetime.now(jst).strftime("%Y年%m月%d日 %H:%M")

    bg_file = "background.jpg"
    font_file = "font.ttf"

    if not os.path.exists(bg_file) or not os.path.exists(font_file):
        print("背景画像またはフォントが見つかりません")
        return

    img = Image.open(bg_file)
    draw = ImageDraw.Draw(img)

    f_main = ImageFont.truetype(font_file, 130)
    f_sub = ImageFont.truetype(font_file, 70)
    f_date = ImageFont.truetype(font_file, 60)
    f_weather = ImageFont.truetype(font_file, 52)

    line = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

    # 日時
    draw.text((100, 80), date_str, font=f_date, **line)

    # 天気（上部に追加）
    draw.text((100, 165), weather_line, font=f_weather, **line)

    # 貯水率のみ
    draw.text((100, 320), "貯水率", font=f_sub, **line)
    draw.text((120, 400), f"{rate}%", font=f_main, **line)

    img.save("result.jpg")
    print(f"合成完了: rate={rate} / weather='{weather_line}'")


if __name__ == "__main__":
    weather = get_weather_motoyama()
    r = get_rate_with_ai()
    create_image(r, weather)
