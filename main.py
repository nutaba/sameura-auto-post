import requests
from PIL import Image, ImageDraw, ImageFont

def get_data():
    # 今回はテスト用に仮の数値を入れます
    rate = "92.5" 
    weather = "晴れ"
    return rate, weather

def create_image(rate, weather):
    try:
        # 1. 背景画像を読み込む
        img = Image.open("background.jpg")
        draw = ImageDraw.Draw(img)
        
        # 2. フォントを設定 (サイズは画像に合わせて調整してください)
        # font.ttf がアップロードされている必要があります
        font_main = ImageFont.truetype("font.ttf", 120)
        font_sub = ImageFont.truetype("font.ttf", 80)
        
        # 3. 文字を書き込む (位置は x, y で指定)
        draw.text((100, 300), f"早明浦ダム貯水率", font=font_sub, fill="white")
        draw.text((100, 450), f"{rate}%", font=font_main, fill="white")
        draw.text((100, 700), f"本山町の天気: {weather}", font=font_sub, fill="white")
        
        # 4. 結果を保存
        img.save("result.jpg")
        print("成功：result.jpg を作成しました！")
        
    except Exception as e:
        print(f"画像作成エラー: {e}")

if __name__ == "__main__":
    r, w = get_data()
    create_image(r, w)
