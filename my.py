import sys
import requests
import pymysql
from bs4 import BeautifulSoup
from datetime import datetime
from contextlib import closing


# ---------------- CONFIG ---------------- #
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'your_database',
    'cursorclass': pymysql.cursors.DictCursor
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be" in url:
        return url.split("/")[-1]
    return None


# ---------------- FETCH TRANSCRIPT ---------------- #
def get_transcript(youtube_url):
    log("🌐 Fetching transcript from DownSub...")

    downsub_url = f"https://downsub.com/?url={youtube_url}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(downsub_url, headers=headers, timeout=30)
        soup = BeautifulSoup(res.text, "html.parser")

        links = soup.find_all("a")

        subtitle_link = None

        for link in links:
            href = link.get("href", "")
            if ".txt" in href:
                subtitle_link = href
                break

        if not subtitle_link:
            log("❌ No transcript link found")
            return None

        log(f"✅ Found transcript link")

        txt_res = requests.get(subtitle_link, timeout=30)
        return txt_res.text

    except Exception as e:
        log(f"❌ Error fetching transcript: {e}")
        return None


# ---------------- MAIN ---------------- #
def fetch_and_store(youtube_url):

    video_id = extract_video_id(youtube_url)
    if not video_id:
        log("❌ Invalid URL")
        return

    transcript_text = get_transcript(youtube_url)

    if not transcript_text or len(transcript_text) < 50:
        log("❌ Transcript empty or too short")
        return

    log(f"📊 Transcript length: {len(transcript_text)}")

    # Save file
    with open("transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript_text)

    log("📄 Transcript saved to file")

    # Save DB
    log("💾 Saving to DB...")

    try:
        with closing(pymysql.connect(**DB_CONFIG)) as conn:
            with conn.cursor() as cursor:

                sql = """
                INSERT INTO wp_transcript (video_id, video_url, title, content, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE content = VALUES(content)
                """

                cursor.execute(sql, (
                    video_id,
                    youtube_url,
                    f"YouTube Video {video_id}",
                    transcript_text
                ))

            conn.commit()

        log("✅ DB saved")

    except Exception as e:
        log(f"❌ DB Error: {e}")


# ---------------- ENTRY ---------------- #
if __name__ == "__main__":
    url_input = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url_input)
