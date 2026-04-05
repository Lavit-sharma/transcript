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
        # Extract ID for the database
        video_id = youtube_url.split("v=")[1].split("&")[0] if "v=" in youtube_url else youtube_url.split("/")[-1]
        
        # Build the exact Tactiq 'run' URL as you provided
        encoded_yt = urllib.parse.quote(youtube_url)
        target_url = f"https://tactiq.io/tools/run/youtube_transcript?yt={encoded_yt}"
        
        print(f"Navigating to: {target_url}")
        driver.get(target_url)
        
        # The /run/ page usually has a different loading state.
        # We wait for the transcript text to appear in the specific results area.
        wait = WebDriverWait(driver, 60)

        # Updated Selectors based on the /run/ page structure
        # 1. Grab Title
        try:
            title_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1, .video-title, [class*='title']")))
            video_title = title_el.text.strip()
        except:
            video_title = f"YouTube Video {video_id}"

        # 2. Grab Transcript Content
        # Tactiq's tool pages often use these specific classes for the output
        selectors = [
            ".transcript-content", 
            ".rendered-transcript",
            "div[class*='transcript_text']",
            "div[class*='Transcript_content']",
            "#transcript-text",
            "pre" # Sometimes raw transcripts are wrapped in pre tags
        ]
        
        transcript_text = ""
        for selector in selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if len(element.text) > 100:
                    transcript_text = element.text.strip()
                    break
            except:
                continue

        if not transcript_text:
            raise Exception("Transcript content not found. The page may still be loading or blocked.")

        # 3. Save to Database
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
        
        # Write to file for GitHub Actions artifact
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript_text)
            
        print(f"✅ Success: Stored transcript for {video_id}")

    except Exception as e:
        print(f"❌ Error: {e}")
        # Save HTML for debugging if it fails again
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    finally:
        driver.quit()

if __name__ == "__main__":
    url_to_process = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url_to_process)
