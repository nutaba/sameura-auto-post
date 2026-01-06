import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone

def get_data():
    print("--- データの取得を開始します ---")
    
    # 確実にデータが存在する「一覧表ページ」を解析対象にします
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "--"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=20)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 表のすべての行を取得
        rows = soup.find_all('tr')
        
        # 上から順に見て、7番目の列（貯水率）に数字が入っている最初の行を探す
        found = False
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 7:
                val = cols[6].get_text(strip=True)
                # 「-」や空欄ではなく、数字（小数点含む）が入っているか判定
                if val and val != "-" and val.replace('.', '', 1).isdigit():
                    rate = val
                    print(f"成功：{cols[0].get_text(strip=True)} {cols[1].get_text(strip=True)} の貯水率 {rate}% を採用しました。")
                    found = True
                    break
        if not found:
            print("警告：表の中に有効な貯水率の数値が見つかりませんでした。")
            
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
        print("エラー: 必要なファイルがありません。")
        return

    try:
        img = Image.open(bg_file)
        draw = ImageDraw.Draw(img)
        font_main = ImageFont.truetype(font_file, 150)
        font_sub = ImageFont.truetype(font_file, 80)
        font_date = ImageFont.truetype(font_file, 70) 
        
        line_settings = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

        draw.text((100, 80), date_str, font=font_date, **line_settings)
        draw.text((100, 350), "早明浦ダム貯水率", font=font_sub, **line_settings)
        # 貯水率の表示
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
