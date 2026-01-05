import requests
from bs4 import BeautifulSoup

def get_data():
    print("--- データの取得を開始します ---")
    
    # URLを直接データが入っている別のものに変更
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "取得失敗"
    
    try:
        # ブラウザのふりをする設定（ヘッダー）を大幅に強化
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        }
        
        # サイトにアクセス
        res = requests.get(dam_url, headers=headers, timeout=20)
        res.encoding = 'shift_jis'
        
        # HTMLを解析
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # サイト内の「文字」をすべて取得して、力技で数値を探す
        text = soup.get_text()
        
        # 貯水率の表の中にある数値パターン（例: 92.5）を探す
        import re
        # 数値（小数点あり）の後に続く ％ または % を探す
        matches = re.findall(r'(\d+\.\d)[％%]', text)
        
        if matches:
            # 最初に見つかった（最新の）数値を採用
            rate = matches[0]
            print(f"成功：数値 {rate}% を抽出しました。")
        else:
            # 整数（例: 100%）の場合も考慮
            matches_int = re.findall(r'(\d+)[％%]', text)
            if matches_int:
                rate = matches_int[0]
                print(f"成功：数値 {rate}% を抽出しました。")

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
