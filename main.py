import os
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai
import re

def get_data_with_ai():
    print("--- 1. ブラウザで最新の数字がある行を特定して撮影 ---")
    url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    
    rate, volume = "取得失敗", "取得失敗"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 2000})
            page.goto(url, wait_until="networkidle")
            time.sleep(5)
            
            # 【重要】貯水率(7列目)がハイフンではない最新の「行(tr)」を直接指定して撮影
            # これでAIに「余計な空欄行」を見せないようにします
            target_row = page.locator("tr:has(td:nth-child(7):not(:text-is('-')))").first
            
            if target_row.count() > 0:
                target_row.screenshot(path="temp_shot.png")
                print("数字入りの行をピンポイントで撮影しました")
            else:
                # 万が一見つからない場合は全体を撮る
                page.screenshot(path="temp_shot.png")
            
            browser.close()

        print("--- 2. AI(Gemini)に数字だけを抽出させる ---")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key: return "Key未設定", "Key未設定"

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        img_file = genai.upload_file(path="temp_shot.png")
        
        # 指示をさらに厳格化
        prompt = "この画像に書かれている『貯水率』と『貯水量』の数字を抜き出してください。回答は必ず『率:数値, 量:数値』の形式のみで答えて。例：率:91.1, 量:107400"
        
        response = model.generate_content([prompt, img_file])
        text = response.text.strip()
        print(f"AI回答: {text}")

        # 正規表現を使って、AIの回答から数字だけを抽出（より確実な方法）
        rate_match = re.search(r'率:([\d.]+)', text)
        volume_match = re.search(r'量:([\d,]+)', text)
        
        if rate_match: rate = rate_match.group(1)
        if volume_match: volume = volume_match.group(1).replace(",", "")
        
    except Exception as e:
        print(f"エラー発生: {e}")
    
    return rate, volume

def create_image(rate, volume):
    print("--- 3. 画像の作成と合成 ---")
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
    
    # 配置
    draw.text((100, 80), date_str, font=f_date, **line)
    draw.text((100, 300), "貯水率", font=f_sub, **line)
    draw.text((120, 380), f"{rate}%", font=f_main, **line)
    draw.text((100, 550), "貯水量", font=f_sub, **line)
    draw.text((120, 630), f"{volume}千m³", font=f_main, **line)
    
    img.save("result.jpg")
    print(f"成功完了: {rate}% / {volume}")

if __name__ == "__main__":
    r, v = get_data_with_ai()
    create_image(r, v)
