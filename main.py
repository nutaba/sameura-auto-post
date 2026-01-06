import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone

def get_data():
    print("--- データの取得を開始します ---")
    
    # 1. 指定された国土交通省のURLから貯水率を取得
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "--"
    
    try:
        # サイトのデータを取得
        res = requests.get(dam_url, timeout=15)
        res.encoding = 'shift_jis' # このサイトはShift_JIS形式です
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # すべての行(tr)を確認し、最新の貯水率（空欄でないもの）を探す
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 7:
                # 7番目の列が「貯水率」です
                val = cols[6].get_text(strip=True)
                # ハイフン(-)や空欄を除き、数値が入っている最新の行を採用
                if val and val != "-" and val.replace('.', '').isdigit():
                    rate = val
                    print(f"成功：サイトから最新の貯水率 {rate}% を取得しました。")
                    break
    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 2. 日本時間で日付を取得
    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日')

    # 3. 本山町の天気を取得
    weather = "確認中"
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
        print("エラー: background.jpg または font.ttf が見つかりません。")
        return

    try:
        img = Image.open(bg_file)
        draw = ImageDraw.Draw(img)
        
        font_main = ImageFont.truetype(font_file, 150)
        font_sub = ImageFont.truetype(font_file, 80)
        font_date = ImageFont.truetype(font_file, 70) 
        
        # 縁取り設定（黒縁）
        line_settings = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

        # 配置
        draw.text((100, 80), date_str, font=font_date, **line_settings)
        draw.text((100, 350), "早明浦ダム貯水率", font=font_sub, **line_settings)
        draw.text((120, 480), f"{rate}%", font=font_main, **line_settings)
        draw.text((100, 750), "本山町の天気", font=font_sub, **line_settings)
        draw.text((120, 870), f"{weather}", font=font_sub, **line_settings)
        
        img.save("result.jpg")
        print(f"成功：画像を作成しました")
    except Exception as e:
        print(f"画像作成中にエラー発生: {e}")

if __name__ == "__main__":
    r, w, d = get_data()
    create_image(r, w, d)
