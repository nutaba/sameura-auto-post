import requests
import re

def get_data():
    print("--- データの取得を開始します ---")
    
    # 手法変更：四国地方整備局のダム放流通知サイト（テキストデータ）を利用
    dam_url = "https://www.skr.mlit.go.jp/sameura/sameura_d.html"
    rate = "取得失敗"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=20)
        res.encoding = 'shift_jis' # このサイトもShift_JISです
        
        # ページ全体のテキストから「貯水率：○○.○％」という部分を探す
        # 正規表現を使って、数字と％の組み合わせを抽出します
        match = re.search(r'貯水率[^\d]*(\d+\.\d)[％%]', res.text)
        
        if match:
            rate = match.group(1)
            print(f"成功：四国地方整備局のサイトから {rate}% を取得しました。")
        else:
            # 別のパターン（整数など）でも試行
            match_alt = re.search(r'(\d+\.\d)[％%]', res.text)
            if match_alt:
                rate = match_alt.group(1)

    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 2. 本山町の天気を取得（こちらは成功しているのでそのまま）
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
