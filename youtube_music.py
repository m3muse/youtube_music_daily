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
DOCS_DIR = "docs"
PAGE_URL = "https://m3muse.github.io/youtube_music_daily/"

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

CARD_THEMES = [
    {"gradient": "linear-gradient(135deg, #FF6B6B, #FF8E53)", "bg": "#FFF5F5", "tag": "#FFE0E0", "tag_text": "#C0392B"},
    {"gradient": "linear-gradient(135deg, #4ECDC4, #44A08D)", "bg": "#F0FAFA", "tag": "#D5F5F2", "tag_text": "#1A7A72"},
    {"gradient": "linear-gradient(135deg, #A29BFE, #6C5CE7)", "bg": "#F5F3FF", "tag": "#E5E0FF", "tag_text": "#5A47D1"},
    {"gradient": "linear-gradient(135deg, #FFA502, #FF6348)", "bg": "#FFF8F0", "tag": "#FFE8CC", "tag_text": "#C0611A"},
    {"gradient": "linear-gradient(135deg, #74B9FF, #0984E3)", "bg": "#F0F7FF", "tag": "#D0E8FF", "tag_text": "#1565C0"},
    {"gradient": "linear-gradient(135deg, #55EFC4, #00B894)", "bg": "#F0FFF9", "tag": "#C8F7E8", "tag_text": "#006B4F"},
    {"gradient": "linear-gradient(135deg, #FDCB6E, #E17055)", "bg": "#FFFBF0", "tag": "#FDECC8", "tag_text": "#9C5A2A"},
    {"gradient": "linear-gradient(135deg, #FD79A8, #E84393)", "bg": "#FFF0F7", "tag": "#FFD0EA", "tag_text": "#A0175F"},
    {"gradient": "linear-gradient(135deg, #81ECEC, #00CEC9)", "bg": "#F0FFFE", "tag": "#C8F4F4", "tag_text": "#007A78"},
    {"gradient": "linear-gradient(135deg, #A8C0FF, #3F2B96)", "bg": "#F3F0FF", "tag": "#DDD8FF", "tag_text": "#2E1F7A"},
]


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


def build_card(index, item, region, genre, era, theme):
    title = item['snippet']['title']
    artist = item['snippet']['channelTitle']
    video_id = item['id']['videoId']
    gradient = theme['gradient']
    bg = theme['bg']
    tag_bg = theme['tag']
    tag_color = theme['tag_text']

    return f"""
    <div class="card">
      <div class="card-accent" style="background:{gradient};"></div>
      <div class="card-video">
        <iframe src="https://www.youtube.com/embed/{video_id}"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope"
                allowfullscreen></iframe>
      </div>
      <div class="card-body" style="background:{bg};">
        <div class="card-tags">
          <span class="tag" style="background:{tag_bg};color:{tag_color};">{genre}</span>
          <span class="tag" style="background:{tag_bg};color:{tag_color};">{region}</span>
          <span class="tag" style="background:{tag_bg};color:{tag_color};">{era}</span>
        </div>
        <div class="card-title">
          <span class="num" style="background:{gradient};">{index}</span>
          {title}
        </div>
        <div class="card-artist">🎤 {artist}</div>
      </div>
    </div>
    """


def build_page(label, songs):
    today = date.today().strftime('%Y년 %m월 %d일')
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][datetime.now().weekday()]

    cards_html = "".join(
        build_card(i, item, region, genre, era, CARD_THEMES[i - 1])
        for i, (item, region, genre, era) in enumerate(songs, 1)
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎵 오늘의 음악 발굴 | {today}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', 'Apple SD Gothic Neo', Arial, sans-serif;
      background: #f4f6fb;
      min-height: 100vh;
    }}
    .hero {{
      background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 50%, #ffecd2 100%);
      padding: 70px 20px 80px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}
    .hero::before {{
      content: '';
      position: absolute;
      top: -60px; left: -60px;
      width: 220px; height: 220px;
      background: rgba(255,255,255,0.18);
      border-radius: 50%;
    }}
    .hero::after {{
      content: '';
      position: absolute;
      bottom: -70px; right: -40px;
      width: 260px; height: 260px;
      background: rgba(255,255,255,0.12);
      border-radius: 50%;
    }}
    .hero-badge {{
      display: inline-block;
      background: rgba(255,255,255,0.3);
      color: white;
      font-size: 13px;
      letter-spacing: 2px;
      text-transform: uppercase;
      padding: 6px 18px;
      border-radius: 20px;
      margin-bottom: 18px;
    }}
    .hero-title {{
      font-size: 44px;
      font-weight: 800;
      color: white;
      text-shadow: 0 2px 20px rgba(0,0,0,0.12);
      margin-bottom: 10px;
      position: relative;
      z-index: 1;
    }}
    .hero-sub {{
      font-size: 18px;
      color: rgba(255,255,255,0.9);
      font-weight: 400;
      position: relative;
      z-index: 1;
    }}
    .cards-wrap {{
      max-width: 980px;
      margin: 44px auto 60px;
      padding: 0 20px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(440px, 1fr));
      gap: 28px;
    }}
    .card {{
      background: white;
      border-radius: 24px;
      overflow: hidden;
      box-shadow: 0 6px 28px rgba(0,0,0,0.07);
      transition: transform 0.25s, box-shadow 0.25s;
    }}
    .card:hover {{
      transform: translateY(-5px);
      box-shadow: 0 16px 44px rgba(0,0,0,0.13);
    }}
    .card-accent {{ height: 7px; }}
    .card-video {{
      position: relative;
      padding-top: 56.25%;
    }}
    .card-video iframe {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      border: none;
    }}
    .card-body {{ padding: 18px 20px 22px; }}
    .card-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-bottom: 13px;
    }}
    .tag {{
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
    }}
    .card-title {{
      font-size: 16px;
      font-weight: 700;
      color: #1a1a1a;
      line-height: 1.45;
      margin-bottom: 8px;
      display: flex;
      align-items: flex-start;
      gap: 10px;
    }}
    .num {{
      flex-shrink: 0;
      width: 26px; height: 26px;
      border-radius: 50%;
      color: white;
      font-size: 13px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-top: 1px;
    }}
    .card-artist {{
      font-size: 14px;
      color: #888;
      padding-left: 36px;
    }}
    .footer {{
      text-align: center;
      padding: 32px 20px;
      color: #bbb;
      font-size: 13px;
    }}
    @media (max-width: 620px) {{
      .hero-title {{ font-size: 30px; }}
      .cards-wrap {{ grid-template-columns: 1fr; padding: 0 14px; }}
    }}
  </style>
</head>
<body>
  <div class="hero">
    <div class="hero-badge">{weekday_kr}요일 · {today}</div>
    <h1 class="hero-title">🎵 오늘의 음악 발굴</h1>
    <p class="hero-sub">{label} — 세계 각지의 숨겨진 음악</p>
  </div>

  <div class="cards-wrap">
    {cards_html}
  </div>

  <div class="footer">매일 오전 9시, 새로운 음악을 발굴합니다</div>
</body>
</html>"""


def save_page(html):
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(html)


def build_email(label, songs, today):
    song_list = "".join(
        f'<tr><td style="padding:10px 0;border-bottom:1px solid #f0f0f0;">'
        f'<span style="color:#999;font-size:12px;">{genre} · {region} · {era}</span><br>'
        f'<span style="font-weight:600;color:#333;">{item["snippet"]["title"]}</span>'
        f'</td></tr>'
        for item, region, genre, era in songs
    )

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:20px 0;background:#f4f6fb;font-family:Arial,sans-serif;">
<table width="560" cellpadding="0" cellspacing="0"
       style="margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
  <tr>
    <td style="padding:36px 32px 28px;background:linear-gradient(135deg,#ff9a9e,#fad0c4,#ffecd2);text-align:center;">
      <p style="margin:0 0 6px;color:rgba(255,255,255,0.85);font-size:13px;letter-spacing:2px;">DAILY MUSIC DISCOVERY</p>
      <h1 style="margin:0 0 6px;color:white;font-size:26px;font-weight:800;">🎵 오늘의 음악 발굴</h1>
      <p style="margin:0;color:rgba(255,255,255,0.9);font-size:15px;">{today} · {label}</p>
    </td>
  </tr>
  <tr>
    <td style="padding:24px 32px;">
      <table width="100%" cellpadding="0" cellspacing="0">{song_list}</table>
    </td>
  </tr>
  <tr>
    <td style="padding:8px 32px 36px;text-align:center;">
      <a href="{PAGE_URL}"
         style="display:inline-block;background:linear-gradient(135deg,#ff9a9e,#ff6b6b);
                color:white;text-decoration:none;padding:14px 36px;border-radius:30px;
                font-size:16px;font-weight:700;box-shadow:0 4px 16px rgba(255,107,107,0.35);">
        ▶ &nbsp;지금 바로 듣기
      </a>
    </td>
  </tr>
  <tr>
    <td style="padding:16px;text-align:center;background:#fafafa;">
      <p style="margin:0;color:#ccc;font-size:12px;">매일 오전 9시, 세계 각지의 숨겨진 음악을 발굴합니다</p>
    </td>
  </tr>
</table>
</body></html>"""


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
    print(f"히스토리 로드: {len(history)}곡")

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

    page_html = build_page(label, songs)
    save_page(page_html)
    print("페이지 생성 완료: docs/index.html")

    today = date.today().strftime('%Y년 %m월 %d일')
    email_html = build_email(label, songs, today)
    subject = f"🎵 오늘의 음악 발굴 | {today} - {label}"

    print("이메일 전송 중...")
    send_email(subject, email_html)
    print(f"완료! {RECIPIENT_EMAIL}로 전송됨")


if __name__ == '__main__':
    main()
