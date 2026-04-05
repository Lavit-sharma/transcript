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

def get_clean_id(arg):
    """Extracts ID from URL or returns the string if it's already an ID."""
    if "v=" in arg:
        return arg.split("v=")[1].split("&")[0]
    elif "youtu.be/" in arg:
        return arg.split("/")[-1]
    return arg

def fetch_and_store(video_id):
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    # Tactiq requires a double-encoded or very specific URL format
    encoded_url = urllib.parse.quote(youtube_url, safe='')
    tactiq_url = f"https://tactiq.io/tools/youtube-transcript-generator?url={encoded_url}"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Add a user agent to prevent being blocked
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        print(f"Opening: {tactiq_url}")
        driver.get(tactiq_url)
        
        # Increased wait and multiple selector check
        wait = WebDriverWait(driver, 45) 
        
        # 1. Try to get Title
        try:
            title_el = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            video_title = title_el.text.strip()
        except:
            video_title = f"YouTube Video {video_id}"

        # 2. Try multiple selectors for the transcript content
        selectors = [
            "div.transcript-content", 
            ".rendered-transcript", 
            "#transcript-text",
            "div[class*='Transcript_container']",
            "section div p" # Fallback to any paragraph inside a div
        ]
        
        transcript_content = ""
        for selector in selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if len(element.text) > 100: # Ensure it's not just a 'loading' tag
                    transcript_content = element.text.strip()
                    break
            except:
                continue

        if not transcript_content:
            raise Exception("Could not find transcript content on page.")

        # 3. Store in MySQL
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO wp_transcript (video_id, video_url, title, content)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content = VALUES(content), title = VALUES(title)
            """
            cursor.execute(sql, (video_id, youtube_url, video_title, transcript_content))
        conn.commit()
        conn.close()
        
        # Save to file so GitHub Artifacts finds it
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript_content)
            
        print(f"✅ Successfully saved: {video_title}")

    except Exception as e:
        print(f"❌ Error: {e}")
        # Save page source for debugging if it fails
        with open("error_page.html", "w") as f:
            f.write(
