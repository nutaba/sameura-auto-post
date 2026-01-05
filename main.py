import requests
from bs4 import BeautifulSoup

def get_data():
    print("--- データの取得を開始します ---")
    
    # 1. 早明浦ダムの貯水率を取得
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "取得失敗"
    try:
        # サイトが「プログラム」を拒否しないよう、ブラウザのふりをする設定を追加
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=10)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # サイト内のすべての表のセル(td)をチェック
        cells = soup.find_all('td')
        valid_numbers = []
        
        for cell in cells:
            val = cell.text.strip()
            # 「92.5」のように、小数点を含み、かつ数値として認識できるものを探す
            if val and val.replace('.', '').isdigit() and '.' in val:
                # 貯水率は通常 0.0〜100.0 の範囲
                f_val = float(val)
                if 0 <= f_val <= 100:
                    valid_numbers.append(val)
        
        # 表の中で、一番最後に登場する数値が「最新の貯水率」である可能性が高い
        if valid_numbers:
            rate = valid_numbers[-1]

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
