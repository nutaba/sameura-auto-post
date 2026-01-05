import requests
from bs4 import BeautifulSoup

def get_data():
    print("--- データの取得を開始します ---")
    
    # 【重要】データが直接書き込まれている「DL用URL」に変更
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamDataDl.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "取得失敗"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=15)
        res.encoding = 'shift_jis'
        
        # HTMLを解析
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.find_all('tr')
        print(f"解析中: {len(rows)}行のデータをスキャンしています...")

        # 最新のデータ（数字が入っている最初の行）を探す
        for row in rows:
            cols = row.find_all('td')
            # 貯水率は右から1番目（インデックス-1）にある
            if len(cols) >= 7:
                val = cols[-1].get_text(strip=True)
                # 数値であることを確認
                if val and val.replace('.', '').isdigit():
                    rate = val
                    print(f"成功：最新データ({rate}%)を見つけました。")
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
