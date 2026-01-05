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
        
        # サイト内の「すべてのテーブル」を探す
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                # 貯水率の行は、通常6つ以上の列（日付、時刻、雨量など）がある
                if len(cols) >= 6:
                    # 一番最後の列（貯水率）を取り出す
                    val = cols[-1].text.strip()
                    # もし数値（小数点含む）であれば、それが貯水率
                    if val.replace('.', '').replace('-', '').isdigit():
                        rate = val
                        break # 最新の1件が見つかれば終了
            if rate != "取得失敗": break
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

    print(f"早明浦ダム貯水率: {rate}%")
    print(f"本山町の天気: {weather_info}")
    print(f"-------------------")

if __name__ == "__main__":
    get_data()
