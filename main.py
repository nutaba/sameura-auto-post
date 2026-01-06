import os
import time
import re
import json
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai

URL = "https://suibo-kouho.suibou.pref.kochi.lg.jp/suibou/graph/model_dam_8.html?unq=12473017225"


def get_data_with_ai():
    print("--- 1. 高知県のダム図解ページを撮影中 ---")

    # 初期値
    rate, volume = "--", "--"

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY が未設定")
        return rate, volume

    # ===== 先に ai_raw.txt を必ず作る（重要） =====
    with open("ai_raw.txt", "w", encoding="utf-8") as f:
        f.write("ai_raw placeholder\n")

    # ===== Playwrightでスクショ =====
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

            page.screenshot(path="temp_shot_full.png", full_page=True)
            page.screenshot(path="temp_shot.png")

            browser.close()
    except Exception as e:
        with open("ai_raw.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[SCREENSHOT ERROR] {e}\n")
        print("スクショでエラー:", e)
        return rate, volume

    print("--- 2. AI(Gemini)が数値を抽出中 ---")

    # ===== Gemini =====
    try:
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={
                "temperature": 0,
                "max_output_tokens": 128,
            },
        )

        img_file = genai.upload_file(path="temp_shot.png")

        prompt = """
あなたは厳密な情報抽出エンジンです。
出力は JSON のみ。余計な文章は禁止。

画像から次の2つを読み取ってください。

- rate: 貯水率(利水容量) の数値（%記号なし。例: 91.20）
- volume: 貯水量 の数値（カンマなし。例: 106270 または 106270.000）

必ず次の形式だけを返してください。
{"rate": <number or null>, "volume": <number or null>}

読めない場合は null。
""".strip()

        response = model.generate_content([prompt, img_file])
        text = (response.text or "").strip()

        print("AIの生回答:", text)

        # ===== 生回答を必ず保存 =====
        with open("ai_raw.txt", "w", encoding="utf-8") as f:
            f.write(text)

        # ===== JSONでパース =====
        try:
            data = json.loads(text)
            r = data.get("rate")
            v = data.get("volume")
        except Exception:
            # JSONが壊れていた場合の保険
            r = None
            v = None

        # ===== 値チェック =====
        if r is not None:
            try:
                rf = float(r)
                if 0 <= rf <= 100:
                    rate = f"{rf:.2f}"
            except:
                pass

        if v is not None:
            try:
                vf = float(str(v).replace(",", ""))
                if vf >= 0:
                    volume = str(int(vf))
            except:
                pass

    except Exception as e:
        with open("ai_raw.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[GEMINI ERROR] {e}\n")
        print("Geminiでエラー:", e)

    return rate, volume


def create_image(rate, volume):
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

    line = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

    draw.text((100, 80), date_str, font=f_date, **line)

    draw.text((100, 300), "貯水率", font=f_sub, **line)
    draw.text((120, 380), f"{rate}%", font=f_main, **line)

    draw.text((100, 550), "貯水量", font=f_sub, **line)
    draw.text((120, 630), f"{volume}千m³", font=f_main, **line)

    img.save("result.jpg")
    print(f"合成完了: 率={rate}, 量={volume}")


if __name__ == "__main__":
    r, v = get_data_with_ai()
    create_image(r, v)
