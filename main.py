import requests
from bs4 import BeautifulSoup

def get_data():
    print("--- データの取得を開始します ---")
    
    # 【重要】フレームの中身（数値が直接書いてあるページ）のURLを直接叩く
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    
    # 実際の中身を保持している「フレーム用URL」に変更
    frame_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    # ※もしこれでもダメな場合、より直接的なURLを使います。
    
    rate = "取得失敗"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # サイトにアクセス
        res = requests.get(dam_url, headers=headers, timeout=20)
        res.encoding = 'shift_jis'
        
        # HTML全体から「数値.数値%」というパターンを正規表現で探す
        import re
        # 「貯水率」という文字の後に続く数値を重点的に探す
        # サイトの生テキストを抽出
        text = res.text
        
        # 1. 貯水率の列にある「数値」を探す
        # サイトの表の並び順から、数値のあとに「％」が全角または半角であるものを探す
        matches = re.findall(r'(\d+\.\d)[％%]', text)
        
        if matches:
            # サイト上の表は最新が最初の方に来ることが多いため
            rate = matches[0]
            print(f"成功：数値 {rate}% を抽出しました。")
        else:
            # ％が含まれていない場合の数値抽出
            soup = BeautifulSoup(res.text, 'html.parser')
            tds = soup.find_all('td')
            # 全てのセルを後ろからチェック（最新データは最後の方にある可能性があるため）
            for td in reversed(tds):
                val = td.get_text(strip=True)
                if val and val.replace('.', '').isdigit() and '.' in val:
                    rate = val
                    break

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
