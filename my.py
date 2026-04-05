import sys
import time
import pymysql
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Database Configuration (Update these with your actual credentials)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'your_database'
}

def get_transcript(youtube_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Navigate to the specific Tactiq tool URL for that video
        tactiq_url = f"https://tactiq.io/tools/youtube-transcript-generator?url={youtube_url}"
        driver.get(tactiq_url)
        
        # Wait for the transcript text to load
        wait = WebDriverWait(driver, 20)
        # Target the transcript container
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".transcript-content, .rendered-transcript, textarea")))
        
        return element.text.strip()
    except Exception as e:
        print(f"Error scraping: {e}")
        return None
    finally:
        driver.quit()

def save_to_db(url, text):
    if not text: return
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            sql = "INSERT INTO wp_transcript (video_url, transcript_text) VALUES (%s, %s) ON DUPLICATE KEY UPDATE transcript_text=%s"
            cursor.execute(sql, (url, text, text))
        conn.commit()
        conn.close()
        print("Successfully saved to database.")
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python my.py <youtube_url>")
    else:
        url = sys.argv[1]
        transcript = get_transcript(url)
        if transcript:
            save_to_db(url, transcript)
