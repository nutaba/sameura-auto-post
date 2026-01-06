import os
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai

def get_data_with_ai():
    print("--- 1. ブラウザでスクリーンショットを撮影中 ---")
    url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # 画面サイズを大きめに設定して表を確実に入れる
        page.set_viewport_size({"width": 1280, "height": 1000})
        page.goto(url)
        time.sleep(5) # ページが完全に表示されるまで待つ
        
        # スクリーンショットを保存
        page.screenshot(path="temp_shot.png", full_page=True)
        browser.close()

    print("--- 2. AI(Gemini)が数値を解析中 ---")
    # GitHubのSecretsに保存したキーを読み込む
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("エラー: GEMINI_API_KEY が設定されていません。")
        return "取得失敗", "取得失敗"

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 撮影した画像をAIにアップロード
    sample_file = genai.upload_file(path="temp_shot.png", display_name="Dam Table")
    
    # AIへの指示（プロンプト）
    prompt = (
        "この早明浦ダムのデータ表から、最新の数値を読み取ってください。"
        "『貯水率(%)』と『貯水量(×10^3m3)』を抜き出し、"
        "回答は必ず『率:91.1, 量:107400』のように、項目名と数値の形式だけで答えてください。"
        "表の一番上にある、数字が入っている行を優先してください。"
    )
    
    try:
        response = model.generate_content([prompt, sample_file])
        text = response.text
        print(f"AIの回答結果: {text}")

        # AIの回答から数値を切り出す処理
        # 例: "率:91.1, 量:107400" -> rate="91.1", volume="107400"
        rate = text.split("率:")[1].split(",")[0].strip()
        volume = text.split("量:")[1].strip()
        # もし単位などが混じっていたら数字以外を削る
        rate = rate.replace("%", "").replace("％", "")
        volume = volume.replace("千m3", "").replace("万m3", "").replace(",", "")
    except Exception as e:
        print(f"AI解析エラー: {e}")
        rate, volume = "取得失敗", "取得失敗"
    
    return rate, volume

def create_image(rate, volume):
    print("--- 3. 画像の作成を開始します ---")
    # 日本時間の日付
    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M')
    
    bg_file = "background.jpg"
    font_file = "font.ttf"
    
    if not os.path.exists(bg_file) or not os.path.exists(font_file):
        print("エラー: 背景画像またはフォントファイルが見つかりません。")
        return

    try:
        img = Image.open(bg_file)
        draw = ImageDraw.Draw(img)
        
        # フォントサイズ設定
        f_main = ImageFont.truetype(font_file, 130) # 数値用
        f_sub = ImageFont.truetype(font_file, 70)   # 項目名用
        f_date = ImageFont.truetype(font_file, 60)  # 日付用
        
        # 白文字に黒縁取りの設定
        line = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}

        # 文字の配置
        draw.text((100, 80), date_str, font=f_date, **line)
        
        draw.text
