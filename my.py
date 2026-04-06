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

    driver = create_driver()

    try:
        downsub_url = f"https://downsub.com/?url={youtube_url}"
        log(f"🌐 Opening: {downsub_url}")

        driver.get(downsub_url)

        wait = WebDriverWait(driver, 60)

        log("⏳ Waiting for TXT button (your XPath)...")

        # ✅ YOUR EXACT XPATH
        txt_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//*[@id='app']/div/main/div/div[2]/div/div[1]/div[1]/div[2]/div[1]/button[2]"
            ))
        )

        log("✅ Button found, clicking...")

        # 🔥 CLICK BUTTON
        driver.execute_script("arguments[0].click();", txt_button)

        time.sleep(3)

        # 🔥 AFTER CLICK → FIND DOWNLOAD LINK
        log("🔍 Looking for download link...")

        link_element = wait.until(
            EC.presence_of_element_located((
                By.XPATH, "//a[contains(@href,'.txt')]"
            ))
        )

        txt_link = link_element.get_attribute("href")

        log(f"⬇️ Download link: {txt_link}")

        # DOWNLOAD FILE
        import requests
        res = requests.get(txt_link)

        return res.text

    except Exception as e:
        log(f"❌ Error: {e}")
        driver.save_screenshot("error.png")
        return None

    finally:
        driver.quit()
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
