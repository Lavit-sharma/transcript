import sys
import time
import pymysql
import urllib.parse
from contextlib import closing
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# ---------------- CONFIG ---------------- #
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'your_database',
    'cursorclass': pymysql.cursors.DictCursor
}


# ---------------- LOGGER ---------------- #
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ---------------- HELPERS ---------------- #
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be" in url:
        return url.split("/")[-1]
    return None


# ---------------- MAIN ---------------- #
def fetch_and_store(youtube_url):

    video_id = extract_video_id(youtube_url)
    if not video_id:
        log("❌ Invalid YouTube URL")
        return

    chrome_options = Options()

    # ⚠️ KEEP HEADLESS OFF FOR DEBUG
    # chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    log("🚀 Starting Chrome...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        target_url = f"https://tactiq.io/tools/run/youtube_transcript?yt={urllib.parse.quote(youtube_url)}"

        log(f"🌐 Opening URL: {target_url}")
        driver.get(target_url)

        time.sleep(5)

        log(f"📄 Page Title: {driver.title}")
        log(f"🔗 Current URL: {driver.current_url}")

        # Screenshot for debugging
        driver.save_screenshot("debug_start.png")
        log("📸 Screenshot saved: debug_start.png")

        attempt = 0

        while True:
            attempt += 1

            log(f"🔄 Attempt #{attempt}")

            try:
                button_exists = driver.execute_script(
                    "return !!document.querySelector('#copy')"
                )
                log(f"🔘 Copy Button Exists: {button_exists}")

                transcript_text = driver.execute_script("""
                    let btn = document.querySelector('#copy');
                    if (!btn) return '';

                    let txt = btn.getAttribute('data-clipboard-text');
                    if (txt && txt.length > 0) return txt;

                    let fallback = btn.innerText || '';
                    return fallback;
                """)

                length = len(transcript_text) if transcript_text else 0
                log(f"📊 Transcript Length: {length}")

                # Scroll to trigger lazy loading
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                if transcript_text and length > 500:
                    log("✅ SUCCESS: Transcript captured!")
                    break

            except Exception as js_error:
                log(f"❌ JS Error: {js_error}")

            # Save periodic debug
            if attempt % 5 == 0:
                filename = f"debug_{attempt}.png"
                driver.save_screenshot(filename)
                log(f"📸 Screenshot saved: {filename}")

            time.sleep(4)

        # ---------------- GET TITLE ---------------- #
        try:
            video_title = driver.execute_script("""
                let h1 = document.querySelector('h1');
                return h1 ? h1.innerText : '';
            """).strip()

            if not video_title:
                video_title = f"YouTube Video {video_id}"

        except:
            video_title = f"YouTube Video {video_id}"

        log(f"🎬 Video Title: {video_title}")

        # ---------------- SAVE TO DB ---------------- #
        log("💾 Saving to database...")

        with closing(pymysql.connect(**DB_CONFIG)) as conn:
            with conn.cursor() as cursor:

                sql = """
                INSERT INTO wp_transcript (video_id, video_url, title, content, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    content = VALUES(content),
                    title = VALUES(title),
                    updated_at = NOW()
                """

                cursor.execute(sql, (
                    video_id,
                    youtube_url,
                    video_title,
                    transcript_text
                ))

            conn.commit()

        log("✅ Database saved successfully")

        # Save transcript file
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript_text)

        log("📄 Transcript file saved")

    except Exception as e:
        log(f"❌ CRITICAL ERROR: {e}")

        with open("debug_error.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        driver.save_screenshot("debug_error.png")
        log("📸 Error screenshot + HTML saved")

    finally:
        driver.quit()
        log("🛑 Browser closed")


# ---------------- ENTRY ---------------- #
if __name__ == "__main__":
    url_input = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url_input)
