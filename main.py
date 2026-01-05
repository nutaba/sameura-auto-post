import requests
from bs4 import BeautifulSoup

def get_data():
    print("--- データの取得を開始します ---")
    
    # 1. 早明浦ダムの貯水率を取得
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "取得失敗"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=15)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # データの入っているテーブルの「行」をすべて取得
        rows = soup.find_all('tr')
        
        # サイトの構造上、データは 5行目以降から始まります
        for row in rows:
            cols = row.find_all('td')
            # 貯水率の行は列が7つ以上あり、最後の列が貯水率(%)
            if len(cols) >= 7:
                val = cols[-1].get_text(strip=True)
                # 最初の「数値が入っている行」が最新データ
                if val and val.replace('.', '').isdigit():
                    rate = val
                    print(f"確認：最新時刻({cols[1].get_text(strip=True)})のデータを取得しました")
                    break
    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 2. 本山町の天気と気温を取得
    weather_info = "取得失敗"
    temp_max = "--"
    temp_min = "--"
    try:
        # 高知県の予報データ
        weather_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json"
        w_res = requests.get(weather_url)
        w_data = w_res.json()
        
        # 天気
        weather_info = w_data[0]['timeSeries'][0]['areas'][0]['weathers'][0].replace('\u3000', ' ')
        
        # 気温（高知市のデータで代用されることが多いですが、予報から抽出）
        # ※本山町ピンポイントの気温APIはOpenWeatherMapが最適ですが、まずは気象庁の広域データ
        temp_url = "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/390000.json"
        # 簡易的に天気のみ表示。気温取得にはOpenWeatherMapのキー作成を後ほどお勧めします。
        
    except Exception as e:
        print(f"天気データ取得エラー: {e}")

    print(f"早明浦ダム貯水率: {rate}%")
    print(f"本山町の天気: {weather_info}")
    print(f"-------------------")

if __name__ == "__main__":
    get_data()
