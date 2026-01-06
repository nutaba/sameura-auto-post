import os
import requests
import re
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone

def get_data():
    print("--- データの取得を開始します ---")
    rate, weather = "92.5", "晴れ"
    
    # 日本時間 (JST) で日付を取得するように修正
    jst = timezone(timedelta(hours=+9), 'JST')
    now = datetime.now(jst)
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
        # 画像のサイズを取得して中央を計算できるようにする
        W, H = img.size
        draw = ImageDraw.Draw(img)
        
        font_main = ImageFont.truetype(font_file, 150)
        font_sub = ImageFont.truetype(font_file, 80)
        font_date = ImageFont.truetype(font_file, 70) 
        
        line_settings = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

        # 日付：一番上に配置 (y=80)
        draw.text((100, 80), date_str, font=font_date, **line_settings)

        # ダム情報：少し下にずらして配置
        draw.text((100, 350), "早明浦ダム貯水率", font=font_sub, **line_settings)
        draw.text((120, 480), f"{rate}%", font=font_main, **line_settings)
        
        # 天気：さらに下に配置
        draw.text((100, 750), "本山町の天気", font=font_sub, **line_settings)
        draw.text((120, 870), f"{weather}", font=font_sub, **line_settings)
        
        img.save("result.jpg")
        print(f"成功：{date_str} 版を作成しました")
    except Exception as e:
        print(f"画像作成中にエラー発生: {e}")

if __name__ == "__main__":
    r, w, d = get_data()
    create_image(r, w, d)
