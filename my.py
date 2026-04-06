import sys
import time
import pymysql
import urllib.parse
from contextlib import closing

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


# ---------------- HELPERS ---------------- #
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be" in url:
        return url.split("/")[-1]
    else:
        return None


# ---------------- MAIN ---------------- #
def fetch_and_store(youtube_url):

    video_id = extract_video_id(youtube_url)
    if not video_id:
        print("❌ Invalid URL")
        return

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")   # remove if blocked
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        target_url = f"https://tactiq.io/tools/run/youtube_transcript?yt={urllib.parse.quote(youtube_url)}"
        print(f"🌐 Opening: {target_url}")

        driver.get(target_url)

        print("⏳ Waiting indefinitely for transcript...")

        transcript_text = ""

        # 🔥 INFINITE LOOP (no timeout)
        attempt = 0
        while True:
            attempt += 1

            try:
                transcript_text = driver.execute_script("""
                    let btn = document.querySelector('#copy');
                    if (!btn) return '';

                    return btn.getAttribute('data-clipboard-text') || 
                           btn.value || 
                           btn.innerText || '';
                """)
            except:
                transcript_text = ""

            # ✅ SUCCESS CONDITION
            if transcript_text and len(transcript_text) > 500:
                print(f"✅ Transcript captured after {attempt} checks")
                break

            print(f"🔄 Waiting... attempt {attempt} (still loading)")
            time.sleep(3)

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

        # ---------------- SAVE TO DB ---------------- #
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

        # ---------------- SAVE FILE ---------------- #
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript_text)

        print(f"🎉 SUCCESS: {video_title}")
        print(f"📊 Length: {len(transcript_text)} chars")

    except Exception as e:
        print(f"❌ ERROR: {e}")

        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

    finally:
        driver.quit()


# ---------------- ENTRY ---------------- #
if __name__ == "__main__":
    url_input = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url_input)
