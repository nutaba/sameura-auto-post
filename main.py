import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone

def get_data():
    print("--- データの取得を開始します ---")
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "--"
    volume = "--" # 貯水量用

    try:
        res = requests.get(dam_url, timeout=30)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            # 貯水量(4列目)と貯水率(7列目)があるか確認
            if len(cols) >= 7:
                v_val = cols[3].get_text(strip=True) # 貯水量 (×10^3 m3)
                r_val = cols[6].get_text(strip=True) # 貯水率 (%)
                
                # 数値が入っている行を採用
                if r_val and r_val != "-" and r_val.replace('.', '', 1).isdigit():
                    rate = r_val
                    # 単位を調整（サイトの数値は1000m3単位なので、10で割って「万m3」にするなど）
                    # ここではサイトの数値をそのまま「貯水量」として取得します
                    volume = v_val
                    print(f"成功：{cols[1].get_text(strip=True)}のデータ（貯水量:{volume}, 貯水率:{rate}%）を採用")
                    break
    except Exception as e:
        print(f"データ取得エラー: {e}")

    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日')

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
        font_main = ImageFont.truetype(font_file, 130) # 少し小さく調整
        font_sub = ImageFont.truetype(font_file, 70)
        font_date = ImageFont.truetype(font_file, 60) 
        
        line_settings = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

        # 配置（重ならないようにy座標を調整）
        draw.text((100, 80), date_str, font=font_date, **line_settings)
        
        # 貯水率
        draw.text((100, 300), "貯水率", font=font_sub, **line_settings)
        draw.text((120, 380), f"{rate}%", font=font_main, **line_settings)
        
        # 貯水量（新しく追加）
        draw.text((100, 550), "貯水量", font=font_sub, **line_settings)
        draw.text((120, 630), f"{volume}千m³", font=font_main, **line_settings)
        
        # 天気
        draw.text((100, 820), "本山町の天気", font=font_sub, **line_settings)
        draw.text((120, 900), f"{weather}", font=font_sub, **line_settings)
        
        img.save("result.jpg")
        print("成功：貯水量入りの画像を保存しました")
    except Exception as e:
        print(f"画像作成エラー: {e}")

if __name__ == "__main__":
    r, v, w, d = get_data()
    create_image(r, v, w, d)
