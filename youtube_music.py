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
    # 히스토리에 없는 곡만 필터링
    fresh = [item for item in items if item['id']['videoId'] not in history]
    if fresh:
        return random.choice(fresh)
    # 모두 히스토리에 있으면 그냥 랜덤 선택
    return random.choice(items) if items else None


def format_body(label, songs):
    today = date.today().strftime('%Y년 %m월 %d일')
    lines = [
        f"{today} 오늘의 음악 발굴 - {label}",
        "=" * 55,
        "",
    ]
    for i, (item, region, genre, era) in enumerate(songs, 1):
        title = item['snippet']['title']
        channel = item['snippet']['channelTitle']
        video_id = item['id']['videoId']
        url = f"https://www.youtube.com/watch?v={video_id}"
        lines.append(f"{i}. [{genre} / {region} / {era}]")
        lines.append(f"   {title}")
        lines.append(f"   채널: {channel}")
        lines.append(f"   {url}")
        lines.append("")
    return "\n".join(lines)


def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = GMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
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
    print(f"히스토리 저장: {len(new_ids)}곡 추가")

    body = format_body(label, songs)
    today = date.today().strftime('%Y년 %m월 %d일')
    subject = f"[오늘의 음악] {today} - {label}"

    print("이메일 전송 중...")
    send_email(subject, body)
    print(f"완료! {RECIPIENT_EMAIL}로 전송됨")


if __name__ == '__main__':
    main()
