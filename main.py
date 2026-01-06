import os
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

def get_data_from_kochi():
    print("--- 1. 高知県のサイトから最新の数値を読み取ります ---")
    url = "https://suibo-kouho.suibou.pref.kochi.lg.jp/suibou/graph/model_dam_8.html?unq=12473017225"
    
    rate = "取得失敗"
    volume = "取得失敗"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            time.sleep(3) # 読み込み待ち

            # サイト内の「最新値」の表から数字をピンポイントで抽出
            # 貯水量は3番目のtd、貯水率は5番目のtdに入っています
            data_cells = page.locator("table.item_table tr:nth-child(2) td")
            
            if data_cells.count() >= 5:
                volume = data_cells.nth(2).inner_text().replace('m3', '').replace(',', '').strip()
                rate = data_cells.nth(4).inner_text().replace('%', '').strip()
                print(f"データ抽出成功: 貯水量 {volume} / 貯水率 {rate}")
            else:
                print("表の構造が変わっている可能性があります")

            browser.close()
    except Exception as e:
        print(f"エラー発生: {e}")
    
    return rate, volume

def create_image(rate, volume):
    print("--- 2. 画像の作成を開始します ---")
    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M')
    
    bg_file, font_file = "background.jpg", "font.ttf"
    if not os.path.exists(bg_file) or not os.path.exists(font_file):
        print("ファイル不足です")
        return

    img = Image.open(bg_file)
    draw = ImageDraw.Draw(img)
    f_main = ImageFont.truetype(font_file, 130)
    f_sub = ImageFont.truetype(font_file, 70)
    f_date = ImageFont.truetype(font_file, 60)
    
    line = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

    # 配置（日付、貯水率、貯水量）
    draw.text((100, 80), date_str, font=f_date, **line)
    
    draw.text((100, 300), "貯水率", font=f_sub, **line)
    draw.text((120, 380), f"{rate}%", font=f_main, **line)
    
    draw.text((100, 550), "貯水量", font=f_sub, **line)
    draw.text((120, 630), f"{volume}千m³", font=f_main, **line)
    
    img.save("result.jpg")
    print("画像の保存が完了しました")

if __name__ == "__main__":
    r, v = get_data_from_kochi()
    create_image(r, v)
