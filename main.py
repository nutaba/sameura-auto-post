import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone

def get_data():
    print("--- データの取得を開始します ---")
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "--"
    volume = "--"

    try:
        # サイトにアクセス（ユーザーエージェントを設定して拒否を防ぐ）
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=30)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # サイト内のすべての行(tr)をチェック
        rows = soup.find_all('tr')
        print(f"解析中: {len(rows)} 行のデータを確認しています...")
        
        for row in rows:
            cols = row.find_all('td')
            # 最低限の列数がある行だけを対象にする
            if len(cols) >= 7:
                v_text = cols[3].get_text(strip=True) # 貯水量の列
                r_text = cols[6].get_text(strip=True) # 貯水率の列
                
                # 貯水率(r_text)に「-」ではなく数字が入っている最新の行を探す
                if r_text and r_text != "-" and r_text.replace('.', '', 1).isdigit():
                    rate = r_text
                    volume = v_text
                    print(f"成功！時刻:{cols[1].get_text(strip=True)} のデータ（率:{rate}% / 量:{volume}）を取得しました")
                    break # 最新の1件が見つかったら終了
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

    return rate, volume, weather, date_str

def create_image(rate, volume, weather, date_str):
    print("--- 画像の作成を開始します ---")
    bg_file = "background.jpg"
    font_file = "font.ttf"
    
    if not os.path.exists(bg_file) or not os.path.exists(font_file):
        print("エラー: 必要なファイルが不足しています。")
        return

    try:
        img = Image.open(bg_file)
        draw = ImageDraw.Draw(img)
        
        # フォントサイズを調整（貯水量を考慮）
        font_main = ImageFont.truetype(font_file, 130)
        font_sub = ImageFont.truetype(font_file, 70)
        font_date = ImageFont.truetype(font_file, 80) 
        
        line_settings = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

        # --- 文字の配置 ---
        # 1. 日付
        draw.text((100, 80), date_str, font=font_date, **line_settings)
        
        # 2. 貯水率
        draw.text((100, 280), "貯水率", font=font_sub, **line_settings)
        draw.text((120, 360), f"{rate}%", font=font_main, **line_settings)
        
        # 3. 貯水量
        draw.text((100, 530), "貯水量", font=font_sub, **line_settings)
        draw.text((120, 610), f"{volume}千m³", font=font_main, **line_settings)
        
        # 4. 天気
        draw.text((100, 800), "本山町の天気", font=font_sub, **line_settings)
        draw.text((120, 880), f"{weather}", font=font_sub, **line_settings)
        
        img.save("result.jpg")
        print(f"完了：貯水率{rate}%、貯水量{volume}で保存しました")
    except Exception as e:
        print(f"画像作成エラー: {e}")

if __name__ == "__main__":
    r, v, w, d = get_data()
    create_image(r, v, w, d)
