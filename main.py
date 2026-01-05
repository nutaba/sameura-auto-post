import requests
import re

def get_data():
    print("--- データの取得を開始します ---")
    
    # 1. 早明浦ダムの貯水率を取得
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "取得失敗"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=15)
        res.encoding = 'shift_jis'
        
        # HTML全体から「数字.数字」の直後に「％」または「%」がある箇所をすべて探す
        # 例：92.5％ や 92.5%
        matches = re.findall(r'(\d+\.\d)[％%]', res.text)
        
        if matches:
            # サイトの表では最新のデータが最初の方に出ることが多いため、最初のマッチを採用
            rate = matches[0]
        else:
            # 整数（例：100%）の場合も考慮
            matches_int = re.findall(r'(\d+)[％%]', res.text)
            if matches_int:
                rate = matches_int[0]

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
