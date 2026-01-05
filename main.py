import requests
import re

def get_data():
    print("--- データの取得を開始します ---")
    
    # 手法変更：ダム便覧（日本ダム協会）の早明浦ダムページ
    # ここは非常にシンプルなHTML構造なので、取得確率が格段に上がります
    dam_url = "http://www.damnet.ne.jp/cgi-bin/binranA/AllSt.cgi?en=2397"
    rate = "確認中"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(dam_url, headers=headers, timeout=15)
        res.encoding = 'euc-jp' # このサイトの文字コード
        
        # ページの中から「数字.数字%」というパターンをすべて探す
        # 貯水率は 0.0% 〜 100.0% の範囲なので、そのパターンの数値を探します
        matches = re.findall(r'(\d{1,3}\.\d)％', res.text)
        
        if matches:
            # 見つかった数値の中で、貯水率と思われるものを採用
            rate = matches[0]
            print(f"成功：ダム便覧から {rate}% を取得しました。")
        else:
            # ％が半角の場合も考慮
            matches_alt = re.findall(r'(\d{1,3}\.\d)%', res.text)
            if matches_alt:
                rate = matches_alt[0]
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
