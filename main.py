import os
import time
import re
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai

def get_data_with_ai():
    print("--- 1. 高知県のダム図解ページを撮影中 ---")
    url = "https://suibo-kouho.suibou.pref.kochi.lg.jp/suibou/graph/model_dam_8.html?unq=12473017225"
    
    rate, volume = "取得失敗", "取得失敗"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})
            page.goto(url, wait_until="networkidle")
            time.sleep(5)
            # ダムの図解部分を中心にスクリーンショットを撮る
            page.screenshot(path="temp_shot.png")
            browser.close()

        print("--- 2. AI(Gemini)が図解から数値を抽出中 ---")
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        img_file = genai.upload_file(path="temp_shot.png")
        # 図の中にある「利水容量」のパーセントと「貯水量」を狙い撃ちで指示
        prompt = (
            "このダムの図解画像から数値を抜き出してください。"
            "1. 青い矢印の横にある『貯水率(利水容量)』の数値（例：91.20）"
            "2. 左上の『貯水量』の数値（例：106270.000）"
            "回答は必ず『率:91.2, 量:106270』の形式だけで答えてください。"
        )
        
        response = model.generate_content([prompt, img_file])
        text = response.text.strip()
        print(f"AIの回答: {text}")

        # 数字だけをきれいに抜き出す
        r_match = re.search(r'率:([\d.]+)', text)
        v_match = re.search(r'量:([\d.]+)', text)
        if r_match: rate = r_match.group(1)
        if v_match: volume = v_match.group(1).split('.')[0] # 小数点以下をカット
            
    except Exception as e:
        print(f"エラー発生: {e}")
    
    return rate, volume

def create_image(rate, volume):
    print("--- 3. 画像合成中 ---")
    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M')
    
    img = Image.open("background.jpg")
    draw = ImageDraw.Draw(img)
    f_main = ImageFont.truetype("font.ttf", 130)
    f_sub = ImageFont.truetype("font.ttf", 70)
    f_date = ImageFont.truetype("font.ttf", 60)
    
    line = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}
    
    draw.text((100, 80), date_str, font=f_date, **line)
    draw.text((100, 300), "貯水率", font=f_sub, **line)
    draw.text((120, 380), f"{rate}%", font=f_main, **line)
    draw.text((100, 550), "貯水量", font=f_sub, **line)
    draw.text((120, 630), f"{volume}千m³", font=f_main, **line)
    
    img.save("result.jpg")
    print(f"完了しました: {rate}% / {volume}")

if __name__ == "__main__":
    r, v = get_data_with_ai()
    create_image(r, v)
