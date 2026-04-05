import sys
import os
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
    download_dir = os.getcwd() # Download to the current folder
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Set Download Preferences for Headless Chrome
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Enable download in headless mode (Special command for Chrome)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": download_dir
    })

    try:
        video_id = youtube_url.split("v=")[1].split("&")[0] if "v=" in youtube_url else youtube_url.split("/")[-1]
        target_url = f"https://tactiq.io/tools/run/youtube_transcript?yt={urllib.parse.quote(youtube_url)}"
        
        print(f"Navigating to: {target_url}")
        driver.get(target_url)
        
        wait = WebDriverWait(driver, 60)
        
        # 1. Click the Download Button
        # We look for a button that contains 'Download'
        print("Looking for Download button...")
        download_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Download')]")))
        download_btn.click()
        print("Download clicked. Waiting for file...")

        # 2. Wait for the file to appear in the directory
        # Tactiq usually downloads a .txt or .docx file
        timeout = 30
        start_time = time.time()
        downloaded_file = None
        
        while time.time() - start_time < timeout:
            files = [f for f in os.listdir(download_dir) if f.endswith(('.txt', '.docx'))]
            if files:
                downloaded_file = files[0]
                break
            time.sleep(2)

        if not downloaded_file:
            raise Exception("File was not downloaded within the timeout period.")

        print(f"✅ File detected: {downloaded_file}")

        # 3. Read the content from the downloaded file
        # If it's a .txt file:
        with open(downloaded_file, 'r', encoding='utf-8') as f:
            transcript_text = f.read().strip()

        # 4. Get Title for DB
        try:
            video_title = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            video_title = downloaded_file.replace(".txt", "")

        # 5. Store in MySQL
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
        
        # Keep a copy as 'transcript.txt' for the GitHub Artifact step
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript_text)
            
        print(f"✅ Successfully stored '{video_title}' from downloaded file.")

    except Exception as e:
        print(f"❌ Error: {e}")
        driver.save_screenshot("error_shot.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    url_input = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=huW5sxhm3ow"
    fetch_and_store(url_input)
