import os
import requests
import re
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime # 日付用の機能を追加

def get_data():
    print("--- データの取得を開始します ---")
    rate, weather = "92.5", "晴れ"
    
    # 今日の日付を取得 (例: 2026年1月6日)
    now = datetime.now()
    date_str = now.strftime('%Y年%m月%d日')
    
    try:
        w_res = requests.get("https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json", timeout=10)
        weather = w_res.json()[0]['timeSeries'][0]['areas'][0]['weathers'][0].replace('\u3000', ' ')
    except: pass
    
    return rate, weather, date_str

def create_image(rate, weather, date_str):
    print("--- 画像の作成を開始します ---")
    bg_file = "background.jpg"
    font_file = "font.ttf"
    
    if not os.path.exists(bg_file) or not os.path.exists(font_file):
        print("エラー: 必要なファイルが足りません。")
        return

    try:
        img = Image.open(bg_file)
        draw = ImageDraw.Draw(img)
        
        # フォントサイズの設定
        font_main = ImageFont.truetype(font_file, 150)
        font_sub = ImageFont.truetype(font_file, 80)
        font_date = ImageFont.truetype(font_file, 60) # 日付用（少し小さめ）
        
        # 縁取り設定
        line_settings = {"fill": "white", "stroke_width": 8, "stroke_fill": "black"}

        # 1. 日付を一番上に書く (少し右上に寄せる場合は x を大きくしてください)
        draw.text((100, 150), date_str, font=font_date, **line_settings)

        # 2. 貯水率と天気を書く
        draw.text((100, 400), "早明浦ダム貯水率", font=font_sub, **line_settings)
        draw.text((100, 500), f"{rate}%", font=font_main, **line_settings)
        
        draw.text((100, 800), "本山町の天気", font=font_sub, **line_settings)
        draw.text((100, 900), f"{weather}", font=font_sub, **line_settings)
        
        img.save("result.jpg")
        print(f"成功：{date_str} 版の result.jpg を作成しました")
    except Exception as e:
        print(f"画像作成中にエラー発生: {e}")

if __name__ == "__main__":
    r, w, d = get_data()
    create_image(r, w, d)
