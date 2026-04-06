import sys
import time
import requests
import pymysql
from datetime import datetime
from contextlib import closing

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ---------------- CONFIG ---------------- #
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'your_database'
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return None


# ---------------- DRIVER ---------------- #
def create_driver():
    log("🌐 Starting browser...")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver


# ---------------- GET TRANSCRIPT ---------------- #
def get_transcript(youtube_url):

    driver = create_driver()

    try:
        downsub_url = f"https://downsub.com/?url={youtube_url}"
        log(f"🌐 Opening: {downsub_url}")

        driver.get(downsub_url)

        wait = WebDriverWait(driver, 60)

        log("⏳ Waiting for TXT button...")

        # ✅ YOUR XPATH
        txt_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//*[@id='app']/div/main/div/div[2]/div/div[1]/div[1]/div[2]/div[1]/button[2]"
            ))
        )

        log("✅ Button found, clicking...")

        driver.execute_script("arguments[0].click();", txt_button)

        time.sleep(3)

        log("🔍 Finding download link...")

        link_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@href,'.txt')]")
            )
        )

        txt_link = link_element.get_attribute("href")

        log(f"⬇️ Download link: {txt_link}")

        res = requests.get(txt_link)

        return res.text

    except Exception as e:
        log(f"❌ Error: {e}")
        driver.save_screenshot("error.png")
        return None

    finally:
        driver.quit()
        log("🛑 Browser closed")


# ---------------- MAIN ---------------- #
def fetch_and_store(youtube_url):

    video_id = extract_video_id(youtube_url)

    transcript_text = get_transcript(youtube_url)

    if not transcript_text:
        log("❌ No transcript")
        return

    log(f"📊 Length: {len(transcript_text)}")

    # Save file
    with open("transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript_text)

    log("📄 Saved transcript")

    # Save DB
    try:
        with closing(pymysql.connect(**DB_CONFIG)) as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    INSERT INTO wp_transcript (video_id, video_url, content)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE content = VALUES(content)
                """, (video_id, youtube_url, transcript_text))

            conn.commit()

        log("✅ DB saved")

    except Exception as e:
        log(f"❌ DB error: {e}")


# ---------------- ENTRY ---------------- #
if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url)
