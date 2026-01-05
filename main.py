import requests
import re
from PIL import Image, ImageDraw, ImageFont

def get_data():
    print("--- データの取得を開始します ---")
    
    # 1. 早明浦ダムの貯水率を取得 (水資源機構)
    dam_url = "https://www.water.go.jp/yoshino/sameura/index.html"
    rate = "--"
    try:
        res = requests.get(dam_url, timeout=15)
        res.encoding = 'utf-8'
        # 「貯水率：92.5％」のような箇所を探す
        match = re.search(r'(\d+\.\d)％', res.text)
        if match:
            rate = match.group(1)
        else:
            # 整数（100%など）も考慮
            match_int = re.search(r'(\d+)％', res.text)
            if match_int:
                rate = match_int[0]
    except:
        rate = "--"

    # 2. 本山町の天気を取得
    weather_info = "確認中"
    try:
        weather_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json"
        w_data = requests.get(weather_url).json()
        weather_info = w_data[0]['timeSeries'][0]['areas'][0]['weathers'][0]
        weather_info = weather_info.replace('\u3000', ' ')
    except:
        weather_info = "確認中"

    return rate, weather_info

def create_image(rate, weather):
    print("--- 画像の作成を開始します ---")
    try:
        # 画像とフォントの読み込み
        img = Image.open("background.jpg")
        draw = ImageDraw.Draw(img)
        
        # フォントサイズは画像に合わせて調整（1080x1920想定）
        # もし文字が大きすぎる/小さすぎる場合は数字を変えてください
        font_large = ImageFont.truetype("font.ttf", 150)
        font_small = ImageFont.truetype("font.ttf", 80)

        # 文字を書く（白文字、少し影をつける設定）
        # 位置(x, y)は画像の真ん中あたりに来るように調整しています
        draw.text((100, 400), "早明浦ダム貯水率", font=font_small, fill="white")
        draw.text((100, 550), f"{rate} %", font=font_large, fill="white")
        draw.text((100, 850), f"本山町の天気", font=font_small, fill="white")
        draw.text((100, 950), f"{weather}", font=font_small, fill="white")

        # 保存
        img.save("result.jpg")
        print("成功：result.jpg を作成しました！")
    except Exception as e:
        print(f"画像作成エラー: {e}")

if __name__ == "__main__":
    r, w = get_data()
    print(f"取得データ: 貯水率 {r}% / 天気 {w}")
    create_image(r, w)
