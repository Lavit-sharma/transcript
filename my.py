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

# --- Database Config (Update with your Hostinger/Server details) ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '', 
    'database': 'your_database_name'
}

def fetch_and_store(youtube_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # 1. Extract Video ID and Build URL
        video_id = youtube_url.split("v=")[1].split("&")[0] if "v=" in youtube_url else youtube_url.split("/")[-1]
        target_url = f"https://tactiq.io/tools/run/youtube_transcript?yt={urllib.parse.quote(youtube_url)}"
        
        print(f"Opening Target URL: {target_url}")
        driver.get(target_url)
        
        # 2. Wait for the specific Transcript Container
        wait = WebDriverWait(driver, 60)
        print("Waiting for transcript container (XPath: //*[@id='transcript'])...")
        
        container = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="transcript"]')))
        
        # 3. Capture Title and Content
        try:
            video_title = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            video_title = f"YouTube Video {video_id}"

        # Using innerText to ensure we get exactly what is visible in the UI
        transcript_text = driver.execute_script("return arguments[0].innerText;", container)

        if not transcript_text or len(transcript_text) < 50:
            raise Exception("Captured transcript is too short. It might not have loaded fully.")

        # 4. Save to MySQL Table
        print("Connecting to database...")
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # Table Structure: video_id, video_url, title, content
            sql = """
            INSERT INTO wp_transcript (video_id, video_url, title, content)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                content = VALUES(content), 
                title = VALUES(title)
            """
            cursor.execute(sql, (video_id, youtube_url, video_title, transcript_text))
        conn.commit()
        conn.close()
        
        # 5. Save local file for GitHub Artifacts
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript_text)
            
        print(f"✅ Success: Transcript for '{video_title}' stored in database.")

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        # Log a snippet of the page for debugging if it fails
        print("HTML Snippet around ID 'transcript':")
        try:
            print(driver.find_element(By.TAG_NAME, "body").text[:500])
        except:
            pass
    finally:
        driver.quit()

if __name__ == "__main__":
    url_input = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url_input)
