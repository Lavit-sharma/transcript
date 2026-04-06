import sys
import time
import pymysql
import urllib.parse
from contextlib import closing
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


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


def fetch_and_store(youtube_url):

    video_id = extract_video_id(youtube_url)
    if not video_id:
        log("❌ Invalid URL")
        return

    chrome_options = Options()

    # ✅ FIXED PATH
    chrome_options.binary_location = "/usr/bin/google-chrome-stable"

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--window-size=1920,1080")

    log("🚀 Starting Chrome...")

    # ✅ FIXED DRIVER PATH
    service = Service("/usr/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        target_url = f"https://tactiq.io/tools/run/youtube_transcript?yt={urllib.parse.quote(youtube_url)}"

        log(f"🌐 Opening: {target_url}")
        driver.get(target_url)

        time.sleep(5)

        transcript_text = ""
        attempt = 0

        while True:
            attempt += 1
            log(f"🔄 Attempt {attempt}")

            transcript_text = driver.execute_script("""
                let btn = document.querySelector('#copy');
                if (!btn) return '';

                let txt = btn.getAttribute('data-clipboard-text');
                if (txt && txt.length > 500) return txt;

                return '';
            """)

            length = len(transcript_text) if transcript_text else 0
            log(f"📊 Length: {length}")

            if transcript_text and length > 500:
                log("✅ Transcript captured")
                break

            time.sleep(4)

        # Save file
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript_text)

        log("📄 Transcript saved")

        # Save DB
        with closing(pymysql.connect(**DB_CONFIG)) as conn:
            with conn.cursor() as cursor:

                sql = """
                INSERT INTO wp_transcript (video_id, video_url, title, content, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    content = VALUES(content)
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
        log(f"❌ ERROR: {e}")
        driver.save_screenshot("error.png")

    finally:
        driver.quit()
        log("🛑 Closed browser")


if __name__ == "__main__":
    url_input = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url_input)
