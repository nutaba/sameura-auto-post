import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone

def get_data():
    print("--- データの取得を開始します ---")
    # ご提示いただいた国土交通省の一覧ページ
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "--"
    update_time = ""

    try:
        res = requests.get(dam_url, timeout=20)
        res.encoding = 'shift_jis' # このサイトの文字コード
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 表の行をすべて取得
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            # 貯水率が記載される7列目があるか確認
            if len(cols) >= 7:
                val = cols[6].get_text(strip=True)
                # 数字(91.1など)が入っている最新の行を探す
                if val and val != "-" and val.replace('.', '', 1).isdigit():
                    rate = val
                    # サイト上の更新時刻（例: 09:00）を取得
                    update_time = cols[1].get_text(strip=True)
                    print(f"成功：{update_time}時点の貯水率 {rate}% を取得")
                    break
    except Exception as e:
        print(f"データ取得エラー: {e}")

    # 日本時間で今日の日付を取得
    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日')

    # 気象庁から天気を取得
    weather = "確認中"
    try:
        w_res = requests.get("https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json", timeout=10)
        weather = w_res.json()[0]['timeSeries'][0]['areas'][0]['weathers'][0].replace('\u3000', ' ')
    except: pass

    return rate, weather, date_str, update_time

def create_image(rate, weather, date_str, update_time):
    print("--- 画像の作成を開始します ---")
    bg_file = "background.jpg"
    font_file = "font.ttf"
    
    if not os.path.exists(bg_file) or not os.path.exists(font_file):
        print("エラー: 必要なファイルが不足しています。")
        return

    try:
        img = Image.open(bg_file)
        draw = ImageDraw.Draw(img)
        font_main = ImageFont.truetype(font_file, 150)
        font_sub = ImageFont.truetype(font_file, 80)
        font_date = ImageFont.truetype(font_file, 70) 
        font_small = ImageFont.truetype(font_file, 40)
        
        line_settings = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

        # 配置
        draw.text((100, 80), date_str, font=font_date, **line_settings)
        draw.text((100, 350), "早明浦ダム貯水率", font=font_sub, **line_settings)
        draw.text((120, 480), f"{rate}%", font=font_main, **line_settings)
        
        # サイトの更新時刻を小さく添える（任意）
        if update_time:
            draw.text((120, 630), f"({update_time} 現在のデータ)", font=font_small, **line_settings)

        draw.text((100, 750), "本山町の天気", font=font_sub, **line_settings)
        draw.text((120, 870), f"{weather}", font=font_sub, **line_settings)
        
        img.save("result.jpg")
        print("成功：画像を保存しました")
    except Exception as e:
        print(f"画像作成エラー: {e}")

if __name__ == "__main__":
    r, w, d, t = get_data()
    create_image(r, w, d, t)
