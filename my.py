import sys
import time
import os
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

# Define a local path for downloads in the GitHub Workspace
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return None

# ---------------- DRIVER ---------------- #
def create_driver():
    log("🌐 Starting browser (Headless Download Config)...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # --- CRITICAL DOWNLOAD SETTINGS ---
    prefs = {
        "download.default_directory": DOWNLOAD_DIR, # Set download path
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # Enable download in headless mode via CDP
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": DOWNLOAD_DIR
    })

    return driver

# ---------------- GET TRANSCRIPT ---------------- #
def get_transcript(youtube_url):
    driver = create_driver()
    try:
        downsub_url = f"https://downsub.com/?url={youtube_url}"
        log(f"🌐 Opening: {downsub_url}")
        driver.get(downsub_url)

        wait = WebDriverWait(driver, 45)
        
        # 1. Wait for TXT button
        smart_xpath = "//div[@id='app']//button[contains(., 'TXT')]"
        txt_button = wait.until(EC.element_to_be_clickable((By.XPATH, smart_xpath)))

        log("✅ Button found. Clicking to trigger auto-download...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", txt_button)
        time.sleep(2)
        
        # 2. Trigger the download
        driver.execute_script("arguments[0].click();", txt_button)

        log("⏳ Waiting for file to appear in downloads folder...")
        
        # 3. Watch the folder for a .txt file
        timeout = 60
        start_time = time.time()
        downloaded_file = None

        while time.time() - start_time < timeout:
            files = os.listdir(DOWNLOAD_DIR)
            # Look for .txt files that aren't temporary crdownload files
            txt_files = [f for f in files if f.endswith('.txt')]
            if txt_files:
                downloaded_file = os.path.join(DOWNLOAD_DIR, txt_files[0])
                break
            time.sleep(2)

        if not downloaded_file:
            driver.save_screenshot("debug_no_download.png")
            raise Exception("File did not download within 60 seconds.")

        log(f"⬇️ Successfully downloaded: {os.path.basename(downloaded_file)}")
        
        with open(downloaded_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        return content

    except Exception as e:
        log(f"❌ Error: {e}")
        return None
    finally:
        driver.quit()
        log("🛑 Browser closed")

# ---------------- MAIN ---------------- #
def fetch_and_store(youtube_url):
    video_id = extract_video_id(youtube_url)
    transcript_text = get_transcript(youtube_url)

    if not transcript_text:
        log("❌ Failed to capture transcript.")
        return

    # Save specifically to the root for your GitHub Artifact action
    with open("transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript_text)
    log("📄 File saved to transcript.txt")

    # Save to DB
    try:
        with closing(pymysql.connect(**DB_CONFIG)) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO wp_transcript (video_id, video_url, content)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE content = VALUES(content)
                """, (video_id, youtube_url, transcript_text))
            conn.commit()
        log("✅ DB Record Updated")
    except Exception as e:
        log(f"❌ DB error: {e}")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url)
