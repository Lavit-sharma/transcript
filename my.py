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
    'database': 'your_db_name'
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
        
        # Use the /run/ URL format you confirmed works
        encoded_yt = urllib.parse.quote(youtube_url)
        target_url = f"https://tactiq.io/tools/run/youtube_transcript?yt={encoded_yt}"
        
        print(f"Navigating to: {target_url}")
        driver.get(target_url)
        
        # 1. Wait for the page to settle
        wait = WebDriverWait(driver, 60)
        time.sleep(5) # Extra time for internal JS to finish fetching from YouTube

        # 2. Try to find the transcript text using multiple methods
        transcript_text = ""

        # Method A: Look for the specific result div
        result_selectors = [
            ".transcript-content", 
            ".rendered-transcript",
            "div[class*='Transcript_text']",
            "div[class*='Transcript_content']",
            "section pre",
            "#transcript-text"
        ]

        for selector in result_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if len(el.text) > 200:
                        transcript_text = el.text.strip()
                        print(f"✅ Found transcript using selector: {selector}")
                        break
                if transcript_text: break
            except: continue

        # Method B: If text is missing, find the 'Copy' button and extract data from it
        if not transcript_text:
            try:
                # Many scrapers find text inside the 'copy' button's data attributes if not in HTML
                copy_btn = driver.find_element(By.XPATH, "//button[contains(., 'Copy') or contains(., 'Download')]")
                # Sometimes the text is in 'data-clipboard-text' or similar
                transcript_text = copy_btn.get_attribute("data-clipboard-text") or copy_btn.get_attribute("value")
                if transcript_text: print("✅ Found transcript inside Copy button attribute.")
            except: pass

        if not transcript_text:
            raise Exception("Transcript content is still empty after 60s. Check if video has captions enabled.")

        # 3. Get Title
        try:
            video_title = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            video_title = f"YouTube Video {video_id}"

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
        
        # Write to file for Artifacts
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript_text)
            
        print(f"✅ Final Success: {video_title} saved.")

    except Exception as e:
        print(f"❌ Error: {e}")
        # Save a screenshot for you to see what the runner sees
        driver.save_screenshot("debug_screenshot.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    url_input = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url_input)
