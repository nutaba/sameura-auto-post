import os
import time
import json
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai

URL = "https://suibo-kouho.suibou.pref.kochi.lg.jp/suibou/graph/model_dam_8.html?unq=12473017225"


def pick_model_name():
    """
    generateContent が使える Gemini モデルを自動選択
    （モデル名変更で壊れないようにする）
    """
    for m in genai.list_models():
        methods = getattr(m, "supported_generation_methods", []) or []
        if "generateContent" in methods:
            return m.name  # 例: models/gemini-2.5-flash
    raise RuntimeError("generateContent 対応の Gemini モデルが見つかりません")


def extract_text_from_response(response):
    """
    response.text が不安定なケース対策：
    candidates[0].content.parts[].text を優先して全文を組み立てる
    """
    try:
        cand = response.candidates[0]
        parts = getattr(cand.content, "parts", []) or []
        text = "".join([getattr(p, "text", "") for p in parts]).strip()
        if text:
            return text
    except Exception:
        pass

    # 最後の手段
    return (getattr(response, "text", "") or "").strip()


def get_data_with_ai():
    print("--- 1. 高知県のダム図解ページを撮影中 ---")

    rate, volume = "--", "--"

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY が未設定")
        return rate, volume

    # ★ ai_raw.txt は必ず作る（失敗時も artifact に残す）
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

        model_name = pick_model_name()
        print("使用するGeminiモデル:", model_name)

        model = genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": 0,
                "max_output_tokens": 256,
            },
        )

        img_file = genai.upload_file(path="temp_shot.png")

        prompt = """
出力は **生のJSONのみ**。
```json のようなコードブロック（コードフェンス）は絶対に付けない。

画像から次の2つを読み取る：
- rate: 貯水率(利水容量) の数値（%記号なし。例: 91.20）
- volume: 貯水量 の数値（カンマなし。例: 106270 または 106270.000）

返すのはこの1行だけ：
{"rate": <number or null>, "volume": <number or null>}

読めない場合は null。
""".strip()

        response = model.generate_content([prompt, img_file])

        text = extract_text_from_response(response)

        # ```json だけ出る事故への最終保険（1回だけ再試行）
        if text.strip() in ("```json", "```", ""):
            retry_prompt = prompt + "\n今すぐJSON本文を出力して。コードフェンス禁止。"
            response = model.generate_content([retry_prompt, img_file])
            text = extract_text_from_response(response)

        print("AIの生回答:", repr(text))

        # ★ 生回答を必ず保存
        with open("ai_raw.txt", "w", encoding="utf-8") as f:
            f.write(text)

        # ===== JSONパース =====
        try:
            data = json.loads(text)
            r = data.get("rate")
            v = data.get("volume")
        except Exception:
            r, v = None, None

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
