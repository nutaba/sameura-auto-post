import requests
from bs4 import BeautifulSoup

def get_data():
    # 1. 早明浦ダムの貯水率を取得
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    res = requests.get(dam_url)
    res.encoding = 'shift_jis'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # テーブルから「92.3」などの数値を探す（最新の行）
    rows = soup.find_all('tr')
    rate = "取得失敗"
    for row in rows:
        if "％" in row.text or "%" in row.text:
            cols = row.find_all('td')
            if len(cols) > 0 and cols[-1].text.strip().replace('.','').isdigit():
                rate = cols[-1].text.strip()
                break

    # 2. 本山町の天気を取得（気象庁のデータなどを簡易的に表示）
    # ※本来はAPIを使いますが、まずは動くか確認用のプリント
    print(f"--- 現在のデータ ---")
    print(f"早明浦ダム貯水率: {rate}%")
    print(f"本山町の天気: 取得準備中")
    print(f"-------------------")

if __name__ == "__main__":
    get_data()
