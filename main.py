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
        
        # サイト内の「すべての行(tr)」を調べます
        rows = soup.find_all('tr')
        for row in rows:
            text = row.get_text()
            # 「貯水率」という文字と「％」が含まれる行を探す
            if "％" in text and ("貯水率" in text or "貯水量" in text):
                cols = row.find_all('td')
                for col in cols:
                    val = col.get_text(strip=True)
                    # 小数点を含み、かつ数値であるものを探す（例：92.5）
                    if val.replace('.', '').isdigit() and "." in val:
                        rate = val
                        # 最初に見つかった（最新の）数値で確定してループを抜ける
                        break
                if rate != "取得失敗":
                    break
    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 2. 本山町の天気を取得
    weather_info = "取得失敗"
    try:
        weather_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json"
        w_res = requests.get(weather_url)
        w_data = w_res.json()
        # 天気情報を取得
        weather_info = w_data[0]['timeSeries'][0]['areas'][0]['weathers'][0]
        weather_info = weather_info.replace('\u3000', ' ') 
    except Exception as e:
        print(f"天気データ取得エラー: {e}")

    print(f"早明浦ダム貯水率: {rate}%")
    print(f"本山町の天気: {weather_info}")
    print(f"-------------------")

if __name__ == "__main__":
    get_data()
