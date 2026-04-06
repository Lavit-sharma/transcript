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

# ---------------- DRIVER (NON-HEADLESS) ---------------- #
def create_driver():
    log("🌐 Starting browser in VISIBLE mode...")
    options = Options()
    
    # --- DISABLED HEADLESS ---
    # options.add_argument("--headless=new") # Commented out so you can see the window
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # --- POPUP & AD HANDLING ---
    options.add_argument("--disable-popup-blocking") 
    options.add_argument("--start-maximized") # Opens window at full size
    
    # --- ANTI-BOT BYPASS ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    # This prevents websites from detecting Selenium via the 'webdriver' property
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver

# ---------------- GET TRANSCRIPT ---------------- #
def get_transcript(youtube_url):
    driver = create_driver()
    try:
        downsub_url = f"https://downsub.com/?url={youtube_url}"
        log(f"🌐 Opening: {downsub_url}")
        driver.get(downsub_url)

        # Wait for the page to load the dynamic content
        wait = WebDriverWait(driver, 60)
        log("⏳ Waiting for the 'TXT' button to appear...")

        # The "Smart Path" we verified earlier
        smart_xpath = "//div[@id='app']//button[contains(., 'TXT')]"
        
        txt_button = wait.until(EC.element_to_be_clickable((By.XPATH, smart_xpath)))

        log("✅ Button visible! Scrolling and preparing to click...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", txt_button)
        time.sleep(2) # Time for you to see what's happening

        log("🖱️ Clicking TXT button now...")
        driver.execute_script("arguments[0].click();", txt_button)

        log("🔍 Waiting for the .txt download link to appear...")
        # After the TXT button click, a link with .txt in href is generated below it
        link_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'.txt')]"))
        )

        txt_link = link_element.get_attribute("href")
        log(f"⬇️ Found download link: {txt_link}")
        
        # Give you a moment to see the link before it closes
        time.sleep(3)

        # Download content
        res = requests.get(txt_link)
        res.raise_for_status()
        return res.text

    except Exception as e:
        log(f"❌ Error encountered: {e}")
        time.sleep(5) # Keeps window open longer so you can read the site error
        return None
    finally:
        driver.quit()
        log("🛑 Browser closed")

# ---------------- MAIN ---------------- #
def fetch_and_store(youtube_url):
    video_id = extract_video_id(youtube_url)
    transcript_text = get_transcript(youtube_url)

    if not transcript_text:
        log("❌ Script failed to retrieve transcript.")
        return

    log(f"📊 Length: {len(transcript_text)}")

    # Save locally
    with open("transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript_text)
    log("📄 File saved to transcript.txt")

    # Save to Database
    try:
        with closing(pymysql.connect(**DB_CONFIG)) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO wp_transcript (video_id, video_url, content)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE content = VALUES(content)
                """, (video_id, youtube_url, transcript_text))
            conn.commit()
        log("✅ Database updated successfully")
    except Exception as e:
        log(f"❌ DB storage error: {e}")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url)
