import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone

def get_data():
    print("--- データの取得を開始します ---")
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "--"

    try:
        # サイトにアクセス
        res = requests.get(dam_url, timeout=20)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # すべての行(tr)を取得
        rows = soup.find_all('tr')
        
        # 数字が入っている行を探す（最新の00分データを優先）
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 7:
                time_val = cols[1].get_text(strip=True) # 時刻 (例: 09:00)
                rate_val = cols[6].get_text(strip=True) # 貯水率
                
                # ハイフンではなく、数字(小数点含む)が入っているか確認
                if rate_val and rate_val != "-" and rate_val.replace('.', '', 1).isdigit():
                    rate = rate_val
                    print(f"成功：{time_val} の貯水率 {rate}% を採用しました。")
                    break # 最初に見つけた数字入りの行（最新）で確定
    except Exception as e:
        print(f"データ取得エラー: {e}")

    # 日本時間で日付を取得
    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日')

    # 天気を取得
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
        return

    try:
        img = Image.open(bg_file)
        draw = ImageDraw.Draw(img)
        font_main = ImageFont.truetype(font_file, 150)
        font_sub = ImageFont.truetype(font_file, 80)
        font_date = ImageFont.truetype(font_file, 70) 
        
        line_settings = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

        # 配置
        draw.text((100, 80), date_str, font=font_date, **line_settings)
        draw.text((100, 350), "早明浦ダム貯水率", font=font_sub, **line_settings)
        # ここで取得した rate を表示
        draw.text((120, 480), f"{rate}%", font=font_main, **line_settings)
        draw.text((100, 750), "本山町の天気", font=font_sub, **line_settings)
        draw.text((120, 870), f"{weather}", font=font_sub, **line_settings)
        
        img.save("result.jpg")
        print(f"成功：貯水率 {rate}% で画像を作成しました")
    except Exception as e:
        print(f"画像作成エラー: {e}")

if __name__ == "__main__":
    r, w, d = get_data()
    create_image(r, w, d)
