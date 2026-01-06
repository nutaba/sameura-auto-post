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
    
    # 万が一の初期値
    rate, volume = "--", "--"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 900})
            page.goto(url, wait_until="networkidle")
            time.sleep(5)
            # 画像をAIに送るために保存
            page.screenshot(path="temp_shot.png")
            browser.close()

        print("--- 2. AI(Gemini)が数値を抽出中 ---")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return "Key未設定", "Key未設定"

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        img_file = genai.upload_file(path="temp_shot.png")
        
        # 指示（プロンプト）：利水容量の91.20%と、貯水量の106270を狙わせる
        prompt = (
            "この早明浦ダムの図解から数値を抜き出してください。"
            "1. 青い矢印の先にある『貯水率(利水容量)』の数値（例：91.20）"
            "2. 左上の緑色の枠内にある『貯水量』の数値（例：106270.000）"
            "回答は必ず『率:数値, 量:数値』の形式で答えてください。"
        )
        
        response = model.generate_content([prompt, img_file])
        text = response.text.strip()
        print(f"AIの生回答: {text}")

        # 【ここが修正ポイント】正規表現で数字だけを抜き出す
        # 率: の後ろにある「数字.数字」のパターンを探す
        r_match = re.search(r'率[:：]\s*([\d.]+)', text)
        # 量: の後ろにある「数字,数字.数字」のパターンを探す
        v_match = re.search(r'量[:：]\s*([\d,.]+)', text)

        if r_match:
            rate = r_match.group(1)
        if v_match:
            # カンマを除去し、小数点以下（.000）をカットして整数にする
            volume_raw = v_match.group(1).replace(',', '')
            volume = volume_raw.split('.')[0]
            
    except Exception as e:
        print(f"エラー発生: {e}")
    
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
    
    # フォントの準備
    f_main = ImageFont.truetype(font_file, 130)
    f_sub = ImageFont.truetype(font_file, 70)
    f_date = ImageFont.truetype(font_file, 60)
    
    line = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}
    
    # 描画位置の調整
    draw.text((100, 80), date_str, font=f_date, **line)
    
    draw.text((100, 300), "貯水率", font=f_sub, **line)
    draw.text((120, 380), f"{rate}%", font=f_main, **line)
    
    draw.text((100, 550), "貯水量", font=f_sub, **line)
    draw.text((120, 630), f"{volume}千m³", font=f_main, **line)
    
    # 天気情報は以前のコードから引き継ぐ場合はここに追加可能ですが、
    # 今回は貯水データを優先して作成しました。
    
    img.save("result.jpg")
    print(f"合成完了: 率{rate} / 量{volume}")

if __name__ == "__main__":
    r, v = get_data_with_ai()
    create_image(r, v)
