import os
import time
import re
import json
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai

URL = "https://suibo-kouho.suibou.pref.kochi.lg.jp/suibou/graph/model_dam_8.html?unq=12473017225"

def _safe_json_loads(text: str):
    t = (text or "").strip()
    # コードフェンス対策
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return json.loads(t)

def _validate(rate, volume):
    # rate: 0-100
    if rate is not None:
        try:
            r = float(rate)
            if 0 <= r <= 100:
                rate = f"{r:.2f}"
            else:
                rate = None
        except:
            rate = None

    # volume: 0以上、整数化
    if volume is not None:
        try:
            v = float(str(volume).replace(",", ""))
            if v >= 0:
                volume = str(int(v))
            else:
                volume = None
        except:
            volume = None

    return rate, volume

def _fallback_regex(text: str):
    # JSONが崩れた時の保険（できれば使わない）
    rate = None
    volume = None

    m = re.search(r"(?:貯水率|率)\s*[:：]?\s*(--|[\d]+(?:\.\d+)?)\s*(?:%|％)?", text)
    if m and m.group(1) != "--":
        rate = m.group(1)

    m = re.search(r"(?:貯水量|量)\s*[:：]?\s*(--|[\d,]+(?:\.\d+)?)", text)
    if m and m.group(1) != "--":
        volume = m.group(1).replace(",", "")

    return rate, volume

def get_data_with_ai():
    print("--- 1. 高知県のダム図解ページを撮影中 ---")

    rate, volume = "--", "--"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Key未設定", "Key未設定"

    # 1) Playwrightでスクショ（くっきり＋描画待ち）
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                viewport={"width": 1400, "height": 900},
                device_scale_factor=2,
                locale="ja-JP",
            )
            page = context.new_page()
            page.goto(URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # デバッグ用に残す
            page.screenshot(path="temp_shot_full.png", full_page=True)
            page.screenshot(path="temp_shot.png")

            browser.close()
    except Exception as e:
        print(f"スクショでエラー: {e}")
        return rate, volume

    # 2) Geminiで抽出（JSON固定）
    print("--- 2. AI(Gemini)が数値を抽出中 ---")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"temperature": 0, "max_output_tokens": 128},
        )

        img_file = genai.upload_file(path="temp_shot.png")

        prompt = """
あなたは厳密な情報抽出エンジンです。出力はJSONのみ。
画像から次を読み取ってください。

- rate: 「貯水率(利水容量)」の数値（%記号なし。例: 91.20）
- volume: 「貯水量」の数値（カンマなし。例: 106270 または 106270.000）

必ず次のJSONだけを返してください（余計な文章は禁止）:
{"rate": <number or null>, "volume": <number or null>}
読めない場合は null。
""".strip()

        response = model.generate_content([prompt, img_file])
        text = (response.text or "").strip()
        print(f"AIの生回答: {text}")

        # 生回答を保存（Actionsで原因追跡できる）
        with open("ai_raw.txt", "w", encoding="utf-8") as f:
            f.write(text)

        # JSON優先でパース
        try:
            data = _safe_json_loads(text)
            r = data.get("rate")
            v = data.get("volume")
        except Exception:
            r, v = _fallback_regex(text)

        r, v = _validate(r, v)
        rate = r if r is not None else "--"
        volume = v if v is not None else "--"

    except Exception as e:
        print(f"Geminiでエラー: {e}")

    return rate, volume

def create_image(rate, volume):
    print("--- 3. 画像合成中 ---")
    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M')

    bg_file, font_file = "background.jpg", "font.ttf"
    if not os.path.exists(bg_file) or not os.path.exists(font_file):
        print("ファイルが見つかりません")
        return

    img = Image.open(bg_file)
    draw = ImageDraw.Draw(img)

    f_main = ImageFont.truetype(font_file, 130)
    f_sub = ImageFont.truetype(font_file, 70)
    f_date = ImageFont.truetype(font_file, 60)

    line = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

    draw.text((100, 80), date_str, font=f_date, **line)

    draw.text((100, 300), "貯水率", font=f_sub, **line)
    draw.text((120, 380), f"{rate}%", font=f_main, **line)

    draw.text((100, 550), "貯水量", font=f_sub, **line)
    draw.text((120, 630), f"{volume}千m³", font=f_main, **line)

    img.save("result.jpg")
    print(f"合成完了: 率{rate} / 量{volume}")

if __name__ == "__main__":
    r, v = get_data_with_ai()
    create_image(r, v)
