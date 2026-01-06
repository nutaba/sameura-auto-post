import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone

def get_data():
    print("--- データの取得を開始します ---")
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "取得失敗"
    volume = "取得失敗"

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=30)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 7:
                v_text = cols[3].get_text(strip=True) 
                r_text = cols[6].get_text(strip=True)
                
                # 数字が入っている行を探す
                if r_text and r_text != "-" and r_text.replace('.', '', 1).isdigit():
                    rate = r_text
                    volume = v_text
                    print(f"発見：{cols[1].get_text(strip=True)}のデータ（率:{rate}% / 量:{volume}）")
                    break
    except Exception as e:
        print(f"データ取得エラー: {e}")

    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M') # 分まで入れる

    weather = "確認中"
    try:
        w_res = requests.get("https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json", timeout=10)
        weather = w_res.json()[0]['timeSeries'][0]['areas'][0]['weathers'][0].replace('\u3000', ' ')
    except: pass

    return rate, volume, weather, date_str

def create_image(rate, volume, weather, date_str):
    print("--- 画像の作成を開始します ---")
    bg_file = "background.jpg"
    font_file = "font.ttf"
    
    if not os.path.exists(bg_file) or not os.path.exists(font_file):
        return

    try:
        img = Image.open(bg_file)
        draw = ImageDraw.Draw(img)
        font_main = ImageFont.truetype(font_file, 130)
        font_sub = ImageFont.truetype(font_file, 70)
        font_date = ImageFont.truetype(font_file, 60) 
        
        line_settings = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

        draw.text((100, 80), date_str, font=font_date, **line_settings)
        draw.text((100, 280), "貯水率", font=font_sub, **line_settings)
        draw.text((120, 360), f"{rate}%", font=font_main, **line_settings)
        draw.text((100, 530), "貯水量", font=font_sub, **line_settings)
        draw.text((120, 610), f"{volume}千m³", font=font_main, **line_settings)
        draw.text((100, 820), "本山町の天気", font=font_sub, **line_settings)
        draw.text((120, 900), f"{weather}", font=font_sub, **line_settings)
        
        # 確実に「新しいファイル」として認識させるために一度削除して保存
        if os.path.exists("result.jpg"):
            os.remove("result.jpg")
        img.save("result.jpg", quality=95)
        print("成功：画像を作成しました")
    except Exception as e:
        print(f"画像作成エラー: {e}")

if __name__ == "__main__":
    r, v, w, d = get_data()
    create_image(r, v, w, d)
