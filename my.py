import sys
import time
import pymysql
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Database Config ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Update with your password
    'database': 'your_db_name' # Update with your DB name
}

def fetch_and_store(video_id):
    # 1. Construct URLs
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    encoded_url = urllib.parse.quote(youtube_url, safe='')
    tactiq_url = f"https://tactiq.io/tools/youtube-transcript-generator?url={encoded_url}"
    
    # 2. Setup Selenium (Headless for GitHub Actions/Servers)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        print(f"Opening Tactiq for Video ID: {video_id}...")
        driver.get(tactiq_url)
        
        # Wait up to 30 seconds for the transcript content to actually appear
        wait = WebDriverWait(driver, 30)
        
        # Capture Video Title (usually the H1 on the page)
        title_el = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        video_title = title_el.text.strip()

        # Capture Transcript Content (targeting the specific transcript box)
        content_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.transcript-content, .rendered-transcript, #transcript-text")))
        transcript_content = content_el.text.strip()

        # 3. Store in MySQL Table
        if transcript_content:
            conn = pymysql.connect(**DB_CONFIG)
            with conn.cursor() as cursor:
                # Column mapping: video_id, video_url, title, content
                sql = """
                INSERT INTO wp_transcript (video_id, video_url, title, content)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    content = VALUES(content),
                    title = VALUES(title)
                """
                cursor.execute(sql, (video_id, youtube_url, video_title, transcript_content))
            conn.commit()
            conn.close()
            print(f"✅ Successfully saved: {video_title}")
        else:
            print("❌ Transcript was empty.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Usage: python my.py huW5sxhm3ow
    if len(sys.argv) > 1:
        v_id = sys.argv[1]
        fetch_and_store(v_id)
    else:
        print("Please provide a Video ID. Example: python my.py huW5sxhm3ow")
