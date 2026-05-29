import json
import os
import random
import smtplib
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API')
GMAIL = os.getenv('GMAIL')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

HISTORY_FILE = "history.json"
MAX_HISTORY = 500

ALL_GENRES = [
    "Jazz", "Funk", "Soul", "R&B", "Neo-Soul", "Disco", "Reggae", "Ska", "Dub",
    "Blues", "Indie Rock", "Indie Pop", "Ballad", "Folk", "Country", "Electronica",
    "City Pop", "Bossa Nova", "Salsa", "Cumbia", "Tango", "Samba", "Bolero",
    "Afrobeat", "Highlife", "Ethiojazz", "Mbalax", "Soukous", "Afrofusion",
    "Chanson", "Fado", "Flamenco", "Balkan Brass", "Rebetiko", "Nordic Folk",
    "Bollywood", "Ghazal", "Gamelan", "Kayokyoku", "Enka", "Luk Thung",
    "Calypso", "Film OST", "World Fusion", "Arabic Jazz", "Oud music",
    "Gnawa", "Rai", "Tropicalia", "Forró", "Son Cubano", "Vallenato",
    "Post-Rock", "Ambient", "Psychedelic", "Surf Rock", "Rocksteady",
    "Hip-Hop", "World Music",
]

ERAS = ["1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]

WEEKLY_REGIONS = {
    0: {"label": "아프리카", "regions": ["Nigeria", "Ethiopia", "Mali", "Senegal", "Ghana", "Congo", "Kenya", "Cameroon", "Tanzania", "Mozambique", "Zimbabwe", "Ivory Coast"]},
    1: {"label": "중남미", "regions": ["Brazil", "Cuba", "Colombia", "Argentina", "Peru", "Venezuela", "Chile", "Mexico", "Bolivia", "Puerto Rico", "Panama", "Haiti"]},
    2: {"label": "아시아", "regions": ["Japan", "India", "Indonesia", "Vietnam", "Thailand", "Philippines", "Pakistan", "Bangladesh", "Myanmar", "Sri Lanka", "Nepal"]},
    3: {"label": "유럽", "regions": ["France", "Portugal", "Norway", "Serbia", "Greece", "Iceland", "Turkey", "Spain", "Bulgaria", "Finland", "Romania", "Hungary"]},
    4: {"label": "미국·영국·카리브", "regions": ["USA", "UK", "Jamaica", "Trinidad", "Barbados", "New Orleans", "Detroit", "Chicago"]},
    5: {"label": "한국·동아시아", "regions": ["Korea", "Japan", "Taiwan", "Hong Kong", "China", "Okinawa"]},
    6: {"label": "중동·중앙아시아", "regions": ["Morocco", "Lebanon", "Iran", "Cape Verde", "Algeria", "Syria", "Uzbekistan", "Georgia", "Armenia", "Tunisia", "Egypt", "Iraq"]},
}


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_history(history, new_ids):
    updated = list(history) + list(new_ids)
    updated = updated[-MAX_HISTORY:]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(updated, f)


def get_daily_combinations():
    weekday = datetime.now().weekday()
    theme = WEEKLY_REGIONS[weekday]
    genres = random.sample(ALL_GENRES, 10)
    combos = []
    for genre in genres:
        region = random.choice(theme["regions"])
        era = random.choice(ERAS)
        combos.append((region, genre, era))
    return theme["label"], combos


def search_one_song(youtube, region, genre, era, history):
    query = f"{genre} {region} music {era}"
    response = youtube.search().list(
        part='snippet',
        q=query,
        type='video',
        videoCategoryId='10',
        maxResults=10,
        order='relevance',
    ).execute()
    items = response.get('items', [])
    fresh = [item for item in items if item['id']['videoId'] not in history]
    if fresh:
        return random.choice(fresh)
    return random.choice(items) if items else None


def build_song_card(index, item, region, genre, era):
    title = item['snippet']['title']
    artist = item['snippet']['channelTitle']
    video_id = item['id']['videoId']
    url = f"https://www.youtube.com/watch?v={video_id}"
    thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

    return f"""
    <tr>
      <td style="padding:20px 24px;border-bottom:1px solid #2a2a2a;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="color:#666;font-size:12px;font-weight:bold;padding-bottom:10px;">
              #{index} &nbsp;
              <span style="background:#2a2a2a;color:#999;padding:3px 8px;border-radius:4px;margin-right:4px;">{genre}</span>
              <span style="background:#2a2a2a;color:#999;padding:3px 8px;border-radius:4px;margin-right:4px;">{region}</span>
              <span style="background:#2a2a2a;color:#999;padding:3px 8px;border-radius:4px;">{era}</span>
            </td>
          </tr>
          <tr>
            <td>
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td width="180" valign="top" style="padding-right:16px;">
                    <a href="{url}" target="_blank" style="display:block;">
                      <img src="{thumbnail}" width="180" height="101"
                           style="display:block;border-radius:8px;border:0;" alt="{title}">
                    </a>
                    <a href="{url}" target="_blank"
                       style="display:block;margin-top:8px;background:#ff0000;color:#fff;
                              text-align:center;padding:7px 0;border-radius:6px;
                              text-decoration:none;font-size:13px;font-weight:bold;">
                      ▶ &nbsp;YouTube 재생
                    </a>
                  </td>
                  <td valign="top">
                    <p style="margin:0 0 6px;font-size:16px;font-weight:bold;color:#ffffff;line-height:1.4;">{title}</p>
                    <p style="margin:0;font-size:14px;color:#aaaaaa;">{artist}</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    """


def build_html(label, songs):
    today = date.today().strftime('%Y년 %m월 %d일')
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][datetime.now().weekday()]

    cards = "".join(
        build_song_card(i, item, region, genre, era)
        for i, (item, region, genre, era) in enumerate(songs, 1)
    )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:20px 0;background:#0a0a0a;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="600" cellpadding="0" cellspacing="0"
         style="margin:0 auto;background:#161616;border-radius:12px;overflow:hidden;">

    <!-- 헤더 -->
    <tr>
      <td style="padding:32px 24px 24px;background:linear-gradient(135deg,#1a1a2e,#16213e);text-align:center;">
        <p style="margin:0 0 6px;color:#888;font-size:13px;letter-spacing:2px;">DAILY MUSIC DISCOVERY</p>
        <h1 style="margin:0 0 8px;color:#ffffff;font-size:26px;">🎵 오늘의 음악 발굴</h1>
        <p style="margin:0;color:#aaaaaa;font-size:14px;">{today} ({weekday_kr}요일) &nbsp;·&nbsp; {label}</p>
      </td>
    </tr>

    <!-- 곡 목록 -->
    {cards}

    <!-- 푸터 -->
    <tr>
      <td style="padding:20px 24px;text-align:center;background:#111;">
        <p style="margin:0;color:#555;font-size:12px;">매일 오전 9시, 세계 각지의 숨겨진 음악을 발굴합니다</p>
      </td>
    </tr>

  </table>
</body>
</html>"""


def send_email(subject, html_body):
    msg = MIMEMultipart('alternative')
    msg['From'] = GMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL, GMAIL_PASSWORD)
        server.sendmail(GMAIL, RECIPIENT_EMAIL, msg.as_string())


def main():
    history = load_history()
    print(f"히스토리 로드: {len(history)}곡 기록됨")

    label, combos = get_daily_combinations()
    print(f"오늘의 테마: {label}")

    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    songs = []
    for region, genre, era in combos:
        print(f"  검색 중: {genre} / {region} / {era}")
        item = search_one_song(youtube, region, genre, era, history)
        if item:
            songs.append((item, region, genre, era))

    new_ids = [item['id']['videoId'] for item, _, _, _ in songs]
    save_history(history, new_ids)

    html = build_html(label, songs)
    today = date.today().strftime('%Y년 %m월 %d일')
    subject = f"🎵 오늘의 음악 발굴 | {today} - {label}"

    print("이메일 전송 중...")
    send_email(subject, html)
    print(f"완료! {RECIPIENT_EMAIL}로 전송됨")


if __name__ == '__main__':
    main()
