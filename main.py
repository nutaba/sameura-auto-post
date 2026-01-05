import requests
import re

def get_data():
    print("--- データの取得を開始します ---")
    
    # 手法変更：水資源機構（JWA）のモバイル向け簡易データページ
    # ここは非常に軽く、アクセス制限も緩いため、最も確実に数値が取れます
    dam_url = "https://www.water.go.jp/yoshino/sameura/index.html"
    rate = "確認中"
    
    try:
        # ブラウザのふりをする設定を最小限に（シンプルにする方が通ることがあります）
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=15)
        
        # サイトが文字化けしないように設定
        res.encoding = 'utf-8'
        
        # ページの中から「数字.数字%」または「数字%」というパターンを探す
        # 貯水率は現在 90% 以上なので、その数値を狙います
        matches = re.findall(r'(\d+\.\d)％|(\d+)％', res.text)
        
        if matches:
            # 見つかった数値の中から空でないものを採用
            for m in matches[0]:
                if m:
                    rate = m
                    print(f"成功：水資源機構のサイトから {rate}% を取得しました。")
                    break
        
        # もし上記でダメなら、より直接的なテキスト解析
        if rate == "確認中":
            # 「貯水率」という文字の後の数字を力技で探す
            text_around = re.search(r'貯水率[^\d]*(\d+\.?\d?)', res.text)
            if text_around:
                rate = text_around.group(1)

    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 2. 本山町の天気を取得（気象庁）
    weather_info = "取得失敗"
    try:
        weather_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json"
        w_res = requests.get(weather_url)
        w_data = w_res.json()
        weather_info = w_data[0]['timeSeries'][0]['areas'][0]['weathers'][0]
        weather_info = weather_info.replace('\u3000', ' ') 
    except Exception as e:
        print(f"天気データ取得エラー: {e}")

    print(f"-------------------")
    print(f"早明浦ダム貯水率: {rate}%")
    print(f"本山町の天気: {weather_info}")
    print(f"-------------------")

if __name__ == "__main__":
    get_data()
