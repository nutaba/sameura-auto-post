import requests
from bs4 import BeautifulSoup

def get_data():
    print("--- データの取得を開始します ---")
    
    # 1. 早明浦ダムの貯水率を取得（データが直接入っているURLへ変更）
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=1"
    rate = "取得失敗"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=15)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 表の行をすべて取得
        rows = soup.find_all('tr')
        print(f"解析中: {len(rows)}行のデータをスキャンしています...")
        
        # 下から順に（最新時刻から）数字が入っている行を探す
        for row in reversed(rows):
            cols = row.find_all('td')
            if len(cols) >= 7:
                val = cols[-1].get_text(strip=True)
                # 数字が含まれているか確認
                if val and any(char.isdigit() for char in val):
                    rate = val
                    print(f"成功：最新データを取得しました。")
                    break
                    
    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 2. 本山町の天気を取得
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
