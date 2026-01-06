import os
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai

def get_data_with_ai():
    print("--- 1. ブラウザでスクリーンショットを撮影中 ---")
    url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    
    rate, volume = "取得失敗", "取得失敗"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 1500})
            page.goto(url, wait_until="networkidle")
            time.sleep(5)
            
            # 【重要】表の中から、ハイフンではなく数字が入っている最初の「tr（行）」だけを特定して撮影
            # これにより、AIが迷う余地をなくします
            target_element = page.locator("tr:has(td:nth-child(7):not(:text('-')))").first
            if target_element:
                target_element.screenshot(path="temp_shot.png")
                print("数字が入っている行の撮影に成功しました")
            else:
                page.screenshot(path="temp_shot.png") # 予備で全体撮影
            
            browser.close()

        print("--- 2. AI(Gemini)が数値を解析中 ---")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key: return "Key未設定", "Key未設定"

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        img_file = genai.upload_file(path="temp_shot.png")
        
        # 指示を究極にシンプルに
        prompt = "この1行のデータから、『貯水率(%)』と『貯水量』の数字だけを抜き出して。『率:91.1, 量:107400』の形式で回答して。"
        
        response = model.generate_content([prompt, img_file])
        text = response.text.strip()
        print(f"AI回答: {text}")

        # 解析処理
        if "率:" in text and "量:" in text:
            rate = text.split("率:")[1].split(",")[0].replace("%", "").strip()
            volume = text.split("量:")[1].replace("千m3", "").replace(",", "").strip()
        
    except Exception as e:
        print(f"エラー発生: {e}")
    
    return rate, volume

def create_image(rate, volume):
    print("--- 3. 画像の作成を開始します ---")
    jst = timezone(timedelta(hours=+9), 'JST')
    now = datetime.now(jst)
    date_str = now.strftime('%Y年%m月%d日 %H:%M')
    
    bg_file, font_file = "background.jpg", "font.ttf"
    if not os.path.exists(bg_file) or not os.path.exists(font_file): return

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
    print(f"完了: {rate}% / {volume}")

if __name__ == "__main__":
    r, v = get_data_with_ai()
    create_image(r, v)
