import requests
from bs4 import BeautifulSoup

def get_data():
    print("--- データの取得を開始します ---")
    
    # 早明浦ダムのデータページ
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "取得失敗"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=20)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # サイト内の「すべての行(tr)」を取得
        rows = soup.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # 貯水率の行は通常、列が7つ以上あります
            if len(cols) >= 7:
                # 7番目の列（インデックス6）が「貯水率」です
                val = cols[6].get_text(strip=True)
                
                # ハイフン(-)や空欄を除外し、数値(例: 92.5)が入っているか確認
                if val and val.replace('.', '').isdigit():
                    # さらに「流域平均雨量（1番目の数値列）」と間違えないよう、
                    # 時刻（2番目の列）がちゃんと入っているか確認
                    time_val = cols[1].get_text(strip=True)
                    if ":" in time_val:
                        rate = val
                        print(f"成功：{cols[0].get_text(strip=True)} {time_val} のデータを取得")
                        break # 最新の1件を見つけたら終了

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
