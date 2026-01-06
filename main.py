def get_data():
    print("--- データの取得を開始します ---")
    
    dam_url = "https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=1368080700010&KIND=3&PAGE=0"
    rate = "--"
    
    try:
        res = requests.get(dam_url, timeout=15)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # すべての行(tr)を取得
        rows = soup.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # 貯水率の列（7番目）が存在するか確認
            if len(cols) >= 7:
                val = cols[6].get_text(strip=True)
                # 数字が入っているかチェック（ハイフンや空欄を飛ばす）
                # val.replace('.', '', 1).isdigit() は「91.1」のような小数に対応
                if val and val != "-" and val.replace('.', '', 1).isdigit():
                    rate = val
                    print(f"成功：{cols[0].get_text(strip=True)} {cols[1].get_text(strip=True)} のデータを採用しました。")
                    break # 数字が見つかったらそこで終了（最新を採用）
    except Exception as e:
        print(f"ダムデータ取得エラー: {e}")

    # 日付と天気の取得（ここは変更なし）
    jst = timezone(timedelta(hours=+9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日')

    weather = "確認中"
    try:
        w_res = requests.get("https://www.jma.go.jp/bosai/forecast/data/forecast/390000.json", timeout=10)
        weather = w_res.json()[0]['timeSeries'][0]['areas'][0]['weathers'][0].replace('\u3000', ' ')
    except: pass

    return rate, weather, date_str
