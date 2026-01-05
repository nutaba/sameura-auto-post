import requests
from bs4 import BeautifulSoup

def get_data():
    print("--- データの取得を開始します ---")
    
    # 1. 早明浦ダムの貯水率を取得
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "取得失敗"
    try:
        res = requests.get(dam_url, timeout=10)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 貯水率が含まれるテーブルの行(tr)をすべて取得
        rows = soup.find_all('tr')
        for row in rows:
            # 行の中に「％」が含まれているか確認
            if "％" in row.text:
                cols = row.find_all('td')
                # 貯水率の数値は、その行の「一番最後のセル」にある
                if len(cols) > 0:
                    val = cols[-1].text.strip()
                    # 数値（小数点含む）であることを確認して採用
                    if val.replace('.', '').isdigit():
                        rate = val
                        break # 最初に見つかった（最新の）数値で確定
    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 2. 本山町の天気を取得
    weather_info = "取得失敗"
    try:
        # 高知県の予報JSON
        weather_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json"
        w_res = requests.get(weather_url)
        w_data = w_res.json()
        # 天気文を取得
        weather_info = w_data[0]['timeSeries'][0]['areas'][0]['weathers'][0]
        weather_info = weather_info.replace('\u3000', ' ') 
    except Exception as e:
        print(f"天気データ取得エラー: {e}")

    print(f"早明浦ダム貯水率: {rate}%")
    print(f"本山町の天気: {weather_info}")
    print(f"-------------------")

if __name__ == "__main__":
    get_data()
