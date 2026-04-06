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
    log("🌐 Starting browser (Visible Mode)...")
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-popup-blocking") 
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    return driver

# ---------------- GET TRANSCRIPT ---------------- #
def get_transcript(youtube_url):
    driver = create_driver()
    main_window = driver.current_window_handle # Remember the original tab

    try:
        downsub_url = f"https://downsub.com/?url={youtube_url}"
        log(f"🌐 Opening: {downsub_url}")
        driver.get(downsub_url)

        wait = WebDriverWait(driver, 30)
        
        # 1. Wait for TXT button
        smart_xpath = "//div[@id='app']//button[contains(., 'TXT')]"
        txt_button = wait.until(EC.element_to_be_clickable((By.XPATH, smart_xpath)))

        log("✅ Button found. Clicking...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", txt_button)
        time.sleep(1)
        
        # 2. Click the button
        driver.execute_script("arguments[0].click();", txt_button)

        # 3. HANDLE POPUPS: If a new tab opened, switch back to the main one immediately
        time.sleep(2)
        if len(driver.window_handles) > 1:
            log("⚠️ Popup detected. Closing ad tabs...")
            for handle in driver.window_handles:
                if handle != main_window:
                    driver.switch_to.window(handle)
                    driver.close()
            driver.switch_to.window(main_window)

        # 4. Wait for the actual download link
        log("🔍 Waiting for download link to appear...")
        
        # We use a loop to wait, as it might take a few seconds to generate
        link_xpath = "//a[contains(@href,'.txt')]"
        link_element = None
        
        for i in range(10): # Try for 20 seconds
            links = driver.find_elements(By.XPATH, link_xpath)
            if links:
                link_element = links[0]
                break
            time.sleep(2)

        if not link_element:
            raise Exception("Timed out waiting for .txt link to generate.")

        txt_link = link_element.get_attribute("href")
        log(f"⬇️ Found link: {txt_link}")

        # Download
        res = requests.get(txt_link)
        res.raise_for_status()
        return res.text

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
        log("❌ Failed to get transcript.")
        return

    with open("transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript_text)

    try:
        with closing(pymysql.connect(**DB_CONFIG)) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO wp_transcript (video_id, video_url, content)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE content = VALUES(content)
                """, (video_id, youtube_url, transcript_text))
            conn.commit()
        log("✅ DB Updated")
    except Exception as e:
        log(f"❌ DB error: {e}")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url)
