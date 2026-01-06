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
            page.set_viewport_size({"width": 1280, "height": 1200})
            page.goto(url, wait_until="networkidle")
            time.sleep(5)
            page.screenshot(path="temp_shot.png")
            browser.close()

        print("--- 2. AI(Gemini)が数値を解析中 ---")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("エラー: APIキーが設定されていません")
            return "Key未設定", "Key未設定"

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 画像アップロード
        img_file = genai.upload_file(path="temp_shot.png")
        prompt = "この早明浦ダムの表から、最新の貯水率(%)と貯水量(×10^3m3)を読み取ってください。回答は必ず『率:91.1, 量:107400』のように数値だけ答えてください。"
        
        response = model.generate_content([prompt, img_file])
        text = response.text
        print(f"AI回答: {text}")

        # 文字列から数値を抽出
        if "率:" in text and "量:" in text:
            rate = text.split("率:")[1].split(",")[0].strip()
            volume = text.split("量:")[1].strip()
        else:
            print("AIの回答形式が想定外です")
            
    except Exception as e:
        print(f"エラー発生: {e}")
    
    return rate, volume

def create_image(rate, volume):
    print("--- 3. 画像の作成を開始します ---")
    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M')
    
    bg_file, font_file = "background.jpg", "font.ttf"
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
    print("画像保存完了")

if __name__ == "__main__":
    r, v = get_data_with_ai()
    create_image(r, v)
