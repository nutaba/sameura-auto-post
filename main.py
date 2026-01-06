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
    # response.text が不安定な場合があるので parts 優先
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
# Weather (Motoyama)
# ------------------------------
def get_weather_motoyama():
    """
    例: "本山町　快晴 1.8℃"
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
# Screenshot
# ------------------------------
def take_dam_screenshot(wait_ms: int, out_png: str):
    """
    wait_ms だけ待ってからスクショ。表示が遅い日対策。
    """
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

        # networkidle の方が安定しやすい
        page.goto(DAM_URL, wait_until="networkidle", timeout=60000)

        # さらに少し待つ（描画待ち）
        page.wait_for_timeout(wait_ms)

        # 画面内に「貯水率」という文字が出るまで待つ（出なければスキップ）
        # ※ 要素が無いページでも落ちないよう try
        try:
            page.wait_for_function("() => document.body && document.body.innerText.includes('貯水率')", timeout=15000)
        except Exception:
            pass

        page.screenshot(path=out_png)
        browser.close()


# ------------------------------
# Sameura Dam rate via Gemini (retry)
# ------------------------------
def read_rate_from_image(img_path: str, api_key: str) -> str:
    """
    Geminiで rate を読む。失敗したら "--"
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        pick_model_name(),
        generation_config={"temperature": 0, "max_output_tokens": 256},
    )

    img_file = genai.upload_file(path=img_path)

    prompt = """
出力は 生のJSONのみ。```json 等のコードブロックは禁止。
画像から「貯水率(利水容量)」の数値だけを読み取る（%記号なし、例: 91.10）。
必ず1行で返す：{"rate": <number or null>}
読めない場合は null。
""".strip()

    response = model.generate_content([prompt, img_file])
    text = extract_text_from_response(response)

    # たまに ```json だけになる事故の保険
    if text.strip() in ("```json", "```", ""):
        response = model.generate_content([prompt + "\n今すぐJSON本文を1行で。", img_file])
        text = extract_text_from_response(response)

    return text


def get_sameura_rate_with_ai():
    rate = "--"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return rate

    # 毎回ログを残す
    with open("ai_raw.txt", "w", encoding="utf-8") as f:
        f.write("ai_raw placeholder\n")

    # 2回リトライ：待ち時間を変えて撮り直す
    attempts = [
        (4000, "temp_shot.png"),     # まずは短め
        (12000, "temp_shot2.png"),   # ダメなら長め
    ]

    for idx, (wait_ms, shot_name) in enumerate(attempts, start=1):
        try:
            take_dam_screenshot(wait_ms=wait_ms, out_png=shot_name)

            text = read_rate_from_image(shot_name, api_key)

            # どの試行の結果か分かるように保存
            with open("ai_raw.txt", "w", encoding="utf-8") as f:
                f.write(f"[TRY {idx}] screenshot={shot_name}\n{text}\n")

            fixed = salvage_json(text)
            data = json.loads(fixed)

            r = data.get("rate")
            if r is None:
                continue

            rf = float(r)
            if 0 <= rf <= 100:
                rate = f"{rf:.2f}"
                break

        except Exception as e:
            with open("ai_raw.txt", "a", encoding="utf-8") as f:
                f.write(f"\n[TRY {idx} ERROR] {e}\n")
            continue

    return rate


# ------------------------------
# Image composition
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

from instagrapi import Client

def post_to_instagram_story():
    print("--- Instagramストーリーズに投稿中 ---")
    username = os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("INSTAGRAM_PASSWORD")
    
    if not username or not password:
        print("Instagramの資格情報が設定されていません")
        return

    try:
        cl = Client()
        # ログイン（セッション管理をしない簡易版）
        cl.login(username, password)
        
        # ストーリーズに投稿
        # result.jpg はPillowで作った画像の名前
        cl.photo_upload_to_story("result.jpg", caption="早明浦ダムの貯水率をお届けします")
        print("Instagramストーリーズへの投稿に成功しました！")
    except Exception as e:
        print(f"Instagram投稿エラー: {e}")

# mainの最後に呼び出す
if __name__ == "__main__":
    weather = get_weather_motoyama()
    rate = get_sameura_rate_with_ai()
    create_image(rate, weather)
    post_to_instagram_story() # ここを追加
