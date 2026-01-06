import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone

def get_data():
    print("--- データの取得を開始します ---")
    
    # 水資源機構の利水容量データページ
    dam_url = "https://www.water.go.jp/mizu/ikeda/mizuinfo/dyn/html/p0101/60/p010102.html"
    rate = "--"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=20)
        res.encoding = 'utf-8' # このサイトはUTF-8です
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # サイト内のテーブルから「利水容量」という文字が入った行を探す
        rows = soup.find_all('tr')
        for row in rows:
            if "利水容量" in row.get_text():
                cols = row.find_all('td')
                for col in cols:
                    text = col.get_text(strip=True)
                    # 「91.1」のような数字と「%」が含まれる部分を探す
                    if "%" in text or "％" in text:
                        rate = text.replace('%', '').replace('％', '').strip()
                        print(f"成功：利水容量 {rate}% を取得しました。")
                        break
    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 日本時間で日付を取得
    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日')

    # 本山町の天気を取得
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
        print("エラー: ファイルが足りません。")
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
        draw.text((120, 480), f"{rate}%", font=font_main, **line_settings)
        draw.text((100, 750), "本山町の天気", font=font_sub, **line_settings)
        draw.text((120, 870), f"{weather}", font=font_sub, **line_settings)
        
        img.save("result.jpg")
        print("成功：画像を保存しました")
    except Exception as e:
        print(f"画像作成エラー: {e}")

if __name__ == "__main__":
    r, w, d = get_data()
    create_image(r, w, d)
