import os
import requests
import re
from PIL import Image, ImageDraw, ImageFont

def get_data():
    print("--- データの取得を開始します ---")
    rate, weather = "92.5", "晴れ"
    try:
        # 気象庁から天気を取得
        w_res = requests.get("https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json", timeout=10)
        weather = w_res.json()[0]['timeSeries'][0]['areas'][0]['weathers'][0].replace('\u3000', ' ')
    except: pass
    return rate, weather

def create_image(rate, weather):
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
        font_main = ImageFont.truetype(font_file, 150) # 貯水率用（大）
        font_sub = ImageFont.truetype(font_file, 80)   # 文字用（小）
        
        # 【ここがポイント！】縁取りの設定
        # stroke_width: 線の太さ（数字を大きくすると太くなる）
        # stroke_fill: 線の色（"black" で黒い縁取り）
        line_settings = {"fill": "white", "stroke_width": 8, "stroke_fill": "black"}

        # 文字を書き込む (x, y) の位置
        draw.text((100, 400), "早明浦ダム貯水率", font=font_sub, **line_settings)
        draw.text((100, 500), f"{rate}%", font=font_main, **line_settings)
        
        draw.text((100, 800), "本山町の天気", font=font_sub, **line_settings)
        draw.text((100, 900), f"{weather}", font=font_sub, **line_settings)
        
        img.save("result.jpg")
        print("成功：縁取り付きの result.jpg を作成しました")
    except Exception as e:
        print(f"画像作成中にエラー発生: {e}")

if __name__ == "__main__":
    r, w = get_data()
    create_image(r, w)
