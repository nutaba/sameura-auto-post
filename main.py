import requests
from bs4 import BeautifulSoup

def get_data():
    print("--- データの取得を開始します ---")
    
    # 手法変更：Yahoo!天気のダム情報ページ（早明浦ダム）
    dam_url = "https://weather.yahoo.co.jp/weather/dam/8/39103.html"
    rate = "取得失敗"
    
    try:
        # ブラウザのふりをする設定
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        res = requests.get(dam_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Yahoo!天気の貯水率が入っている場所を探す
        # <dl class="dam_data"> の中の <span> を探します
        dam_data = soup.find('dl', class_='dam_data')
        if dam_data:
            spans = dam_data.find_all('span')
            for span in spans:
                text = span.get_text()
                # 「92.5」のような数値と「%」が含まれる部分を探す
                if "%" in text or "％" in text:
                    rate = text.replace('%', '').replace('％', '').strip()
                    print(f"成功：Yahoo!天気から {rate}% を取得しました。")
                    break
    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 2. 本山町の天気を取得（気象庁）
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
