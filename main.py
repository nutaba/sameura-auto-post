import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone

def get_data():
    print("--- データの取得を開始します ---")
    # 高知県のダム情報ページ
    url = "https://suibo-kouho.suibou.pref.kochi.lg.jp/suibou/graph/model_dam_8.html?unq=12473017225"
    rate = "--"
    volume = "--"

    try:
        res = requests.get(url, timeout=30)
        res.encoding = 'utf-8' # 高知県のサイトはUTF-8
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # サイト内の「最新値」が表示されている表のセルを探します
        # 貯水量は3番目のtd、貯水率は5番目のtdにあります
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    # 「貯水量」と「貯水率」の文字が含まれる行を探す
                    row_text = row.get_text()
                    if "貯水量" in row_text and "貯水率" in row_text:
                        volume = cols[2].get_text(strip=True).replace('m3', '').replace(',', '')
                        rate = cols[4].get_text(strip=True).replace('%', '')
                        print(f"成功：貯水量 {volume} / 貯水率 {rate}% を取得")
                        break
    except Exception as e:
        print(f"データ取得エラー: {e}")

    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M')

    return rate, volume, date_str

def create_image(rate, volume, date_str):
    print("--- 画像の作成を開始します ---")
    bg_file, font_file = "background.jpg", "font.ttf"
    if not os.path.exists(bg_file) or not os.path.exists(font_file):
        return

    img = Image.open(bg_file)
    draw = ImageDraw.Draw(img)
    f_main = ImageFont.truetype(font_file, 130)
    f_sub = ImageFont.truetype(font_file, 70)
    f_date = ImageFont.truetype(font_file, 60)
    
    line = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

    # 配置
    draw.text((100, 80), date_str, font=f_date, **line)
    draw.text((100, 300), "貯水率", font=f_sub, **line)
    draw.text((120, 380), f"{rate}%", font=f_main, **line)
    draw.text((100, 550), "貯水量", font=f_sub, **line)
    draw.text((120, 630), f"{volume}千m³", font=f_main, **line)
    
    img.save("result.jpg")
    print("成功：画像を保存しました")

if __name__ == "__main__":
    r, v, d = get_data()
    create_image(r, v, d)
