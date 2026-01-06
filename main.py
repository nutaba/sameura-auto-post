import os
import time
import re
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import google.generativeai as genai
from instagrapi import Client

DAM_URL = "https://suibo-kouho.suibou.pref.kochi.lg.jp/suibou/graph/model_dam_8.html?unq=12473017225"
MOTOYAMA_LAT = 33.75
MOTOYAMA_LON = 133.5833

WMO_MAP = {
    0: "快晴", 1: "晴れ", 2: "薄曇り", 3: "くもり",
    45: "霧", 48: "霧", 51: "霧雨", 53: "霧雨", 55: "霧雨",
    61: "小雨", 63: "雨", 65: "大雨", 71: "小雪", 73: "雪", 75: "大雪",
    80: "にわか雨", 81: "にわか雨", 95: "雷雨",
}

def get_weather_motoyama():
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": MOTOYAMA_LAT, "longitude": MOTOYAMA_LON, "current": "temperature_2m,weather_code", "timezone": "Asia/Tokyo"}
        r = requests.get(url, params=params, timeout=20)
        data = r.json()
        current = data.get("current", {})
        cond = WMO_MAP.get(int(current.get("weather_code", 99)), "不明")
        temp = current.get("temperature_2m", "--")
        return f"本山町 {cond} {temp}℃"
    except:
        return "本山町 天気取得失敗"

def get_sameura_rate_with_ai():
    rate = "--"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return rate

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(DAM_URL, wait_until="networkidle")
            time.sleep(8)
            page.screenshot(path="temp_shot.png")
            browser.close()

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        img_file = genai.upload_file(path="temp_shot.png")
        prompt = "この早明浦ダムの図解から『貯水率(利水容量)』の数値を抜き出し、『率:数値』の形式で回答してください。"
        response = model.generate_content([prompt, img_file])
        match = re.search(r'率[:：]\s*([\d.]+)', response.text)
        if match: rate = match.group(1)
    except Exception as e:
        print(f"AI解析エラー: {e}")
    return rate

def create_image(rate, weather):
    jst = timezone(timedelta(hours=9), 'JST')
    date_str = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M')
    img = Image.open("background.jpg")
    draw = ImageDraw.Draw(img)
    font = "font.ttf"
    f_date = ImageFont.truetype(font, 60)
    f_weather = ImageFont.truetype(font, 52)
    f_sub = ImageFont.truetype(font, 70)
    f_main = ImageFont.truetype(font, 130)
    line = {"fill": "white", "stroke_width": 10, "stroke_fill": "black"}
    draw.text((100, 80), date_str, font=f_date, **line)
    draw.text((100, 155), weather, font=f_weather, **line)
    draw.text((100, 300), "早明浦ダム 貯水率", font=f_sub, **line)
    draw.text((120, 380), f"{rate}%", font=f_main, **line)
    img.save("result.jpg")

def post_to_instagram_story():
    user = os.environ.get("INSTAGRAM_USERNAME")
    pw = os.environ.get("INSTAGRAM_PASSWORD")
    if not user or not pw: return
    try:
        cl = Client()
        cl.login(user, pw)
        cl.photo_upload_to_story("result.jpg")
        print("Instagram投稿成功")
    except Exception as e:
        print(f"Instagram投稿失敗: {e}")

if __name__ == "__main__":
    w = get_weather_motoyama()
    r = get_sameura_rate_with_ai()
    create_image(r, w)
    post_to_instagram_story()
