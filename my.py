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
        
        # 1. Wait for the Copy Button (XPath provided: //*[@id='copy'])
        # This button appearing is the signal that the transcript is ready
        wait = WebDriverWait(driver, 90) # Increased to 90s for long videos
        print("Waiting for Copy button (id='copy') to be ready...")
        
        copy_btn = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="copy"]')))

        # 2. Extract Transcript from the button attribute
        # Most "Copy" buttons store the full text in 'data-clipboard-text' or 'value'
        transcript_text = ""
        max_retries = 10
        for i in range(max_retries):
            # Try to get the text directly from the button's internal data
            transcript_text = copy_btn.get_attribute("data-clipboard-text")
            
            if transcript_text and len(transcript_text) > 500:
                print(f"✅ Full transcript captured from Copy button after {i*5}s!")
                break
            else:
                print(f"   [Attempt {i+1}] Button found, but transcript data not yet attached...")
                time.sleep(5)

        if not transcript_text:
            raise Exception("Timeout: Copy button found but transcript text was empty or too short.")

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
        
        # Save file for GitHub Artifacts
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript_text)
            
        print(f"✅ Success: Stored {video_title} ({len(transcript_text)} characters)")

    except Exception as e:
        print(f"❌ Error: {e}")
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    finally:
        driver.quit()

if __name__ == "__main__":
    url_input = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url_input)
