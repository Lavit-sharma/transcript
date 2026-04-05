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
    'password': '', 
    'database': 'your_database'
}

def fetch_and_store(youtube_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        video_id = youtube_url.split("v=")[1].split("&")[0] if "v=" in youtube_url else youtube_url.split("/")[-1]
        target_url = f"https://tactiq.io/tools/run/youtube_transcript?yt={urllib.parse.quote(youtube_url)}"
        
        print(f"Opening: {target_url}")
        driver.get(target_url)
        
        wait = WebDriverWait(driver, 60)
        
        # 1. Wait for the page to load and look for the 'Copy' button
        # This button is clearly visible in your screenshot.
        print("Looking for Copy button...")
        copy_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Copy')]")))
        
        # 2. Extract Title
        try:
            video_title = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            video_title = f"YouTube Video {video_id}"

        # 3. GET THE TRANSCRIPT
        # We try to get it from the 'data-clipboard-text' attribute of the button first
        # This is where most 'Copy' buttons store the text they are about to copy.
        transcript_text = copy_btn.get_attribute("data-clipboard-text")

        if not transcript_text:
            print("Button attribute empty, attempting JavaScript clipboard capture...")
            # Fallback: Click the button and use JS to get the text from the result area
            # We look for the panel on the right from your screenshot
            transcript_panel = driver.find_element(By.XPATH, "//div[contains(@class, 'transcript') or contains(@style, 'overflow-y')]")
            transcript_text = driver.execute_script("return arguments[0].innerText;", transcript_panel)

        if not transcript_text or len(transcript_text) < 50:
            raise Exception("Captured transcript is too short or empty.")

        # 4. Save to Database
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO wp_transcript (video_id, video_url, title, content)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content = VALUES(content), title = VALUES(title)
            """
            cursor.execute(sql, (video_id, youtube_url, video_title, transcript_text))
        conn.commit()
        conn.close()
        
        # Save file for GitHub
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript_text)
            
        print(f"✅ Success: Transcript for '{video_title}' stored in table.")

    except Exception as e:
        print(f"❌ Error: {e}")
        # Log the page source so you can see why it failed in the GitHub logs
        print("Page Source Snippet:", driver.page_source[:500])
    finally:
        driver.quit()

if __name__ == "__main__":
    url_input = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url_input)
