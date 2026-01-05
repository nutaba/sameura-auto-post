import requests
from bs4 import BeautifulSoup
import re

def get_data():
    print("--- データの取得を開始します ---")
    
    # 1. 早明浦ダムの貯水率を取得
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    try:
        res = requests.get(dam_url, timeout=10)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # ページ内の「％」という文字が入っているセルを探す
        rate = "取得失敗"
        cells = soup.find_all('td')
        for i, cell in enumerate(cells):
            if "％" in cell.text:
                # 貯水率の数値はその前のセル、または同じ行の最後にあることが多い
                # サイトの表の並びに合わせて調整
                val = cell.text.replace('％', '').strip()
                if val:
                    rate = val
                    break
        
        # もし上記で見つからない場合、数字＋％のパターンで探す
        if rate == "取得失敗":
            match = re.search(r'(\d+\.\d)％', res.text)
            if match:
                rate = match.group(1)
    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")
        rate = "エラー"

    # 2. 本山町の天気を取得（気象庁の予報JSONを利用）
    # 高知県(390000)の予報データ
    weather_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json"
    try:
        w_res = requests.get(weather_url)
        w_data = w_res.json()
        # 本山町が含まれる「中部」の予報（インデックス0番付近）
        forecast = w_data[0]['timeSeries'][0]['areas'][0]
        weather_text = forecast['weathers'][0] # 今日の天気
        # 気温（今日の最高気温などは別の場所にあるため、まずは天気のみ）
        weather_info = weather_text.replace('\u3000', ' ') # 全角スペースを半角に
    except Exception as e:
        print(f"天気データ取得エラー: {e}")
        weather_info = "取得失敗"

    print(f"早明浦ダム貯水率: {rate}%")
    print(f"本山町の天気: {weather_info}")
    print(f"-------------------")

if __name__ == "__main__":
    get_data()
