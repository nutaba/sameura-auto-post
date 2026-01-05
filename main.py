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
        
        # サイト内の「すべての行(tr)」を取得
        rows = soup.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # 貯水率の行は列が7つ以上あり、最後の列が貯水率
            if len(cols) >= 7:
                val = cols[6].get_text(strip=True) # 7番目の列(インデックス6)が貯水率
                # 「-」や空文字でなく、数字が含まれているかチェック
                if val and (val.replace('.', '').isdigit()):
                    rate = val
                    date_val = cols[0].get_text(strip=True)
                    time_val = cols[1].get_text(strip=True)
                    print(f"確認：{date_val} {time_val} のデータを取得しました")
                    break # 最新の1件を見つけたら終了
                    
    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 2. 本山町の天気を取得
    weather_info = "取得失敗"
    try:
        weather_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json"
        w_res = requests.get(weather_url)
        w_data = w_res.json()
        # 高知県中部（本山町を含むエリア）の天気
        weather_info = w_data[0]['timeSeries'][0]['areas'][0]['weathers'][0]
        weather_info = weather_info.replace('\u3000', ' ') 
    except Exception as e:
        print(f"天気データ取得エラー: {e}")

    print(f"早明浦ダム貯水率: {rate}%")
    print(f"本山町の天気: {weather_info}")
    print(f"-------------------")

if __name__ == "__main__":
    get_data()
