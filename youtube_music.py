import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API')
GMAIL = os.getenv('GMAIL')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')


def get_trending_music(region_code, max_results=10):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    response = youtube.videos().list(
        part='snippet',
        chart='mostPopular',
        videoCategoryId='10',
        maxResults=max_results,
        regionCode=region_code
    ).execute()
    return response.get('items', [])


def format_section(items, label):
    lines = [f"{label} 인기 음악 Top {len(items)}", "=" * 50]
    for i, item in enumerate(items, 1):
        title = item['snippet']['title']
        channel = item['snippet']['channelTitle']
        video_id = item['id']
        url = f"https://www.youtube.com/watch?v={video_id}"
        lines.append(f"{i}. {title}")
        lines.append(f"   아티스트: {channel}")
        lines.append(f"   링크: {url}")
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
    today = date.today().strftime('%Y년 %m월 %d일')

    print("한국 인기 음악 가져오는 중...")
    kr_items = get_trending_music('KR')

    print("글로벌 인기 음악 가져오는 중...")
    global_items = get_trending_music('US')

    kr_section = format_section(kr_items, '🇰🇷 한국')
    global_section = format_section(global_items, '🌍 글로벌')

    body = f"{today} YouTube 알고리즘 인기 음악\n\n{kr_section}\n\n{global_section}"
    subject = f"[YouTube 인기 음악] {today}"

    print("이메일 전송 중...")
    send_email(subject, body)
    print(f"완료! {RECIPIENT_EMAIL}로 전송됨")


if __name__ == '__main__':
    main()
