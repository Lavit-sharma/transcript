import time
import pymysql
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database_name'
}

def get_transcript_from_tactiq(video_url):
    """Uses Selenium to fetch transcript from Tactiq's dynamic page."""
    # Setup headless browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Construct the Tactiq URL (assuming the pattern: tactiq.io/tools/youtube-transcript-generator?url=VIDEO_URL)
    tactiq_url = f"https://tactiq.io/tools/youtube-transcript-generator?url={video_url}"
    
    try:
        driver.get(tactiq_url)
        
        # Wait for the transcript container to appear (adjust selector if Tactiq changed it)
        # Often the transcript is inside a div or textarea after processing
        wait = WebDriverWait(driver, 15)
        transcript_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.transcript-content, .rendered-transcript"))) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # Extract text - adjust the class based on Tactiq's current UI
        transcript_text = transcript_element.text.strip()
        
        return transcript_text
    except Exception as e:
        print(f"Error fetching transcript for {video_url}: {e}")
        return None
    finally:
        driver.quit()

def store_in_db(video_id, title, transcript):
    """Stores the transcript into wp_transcript table."""
    if not transcript:
        return

    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO wp_transcript (video_id, video_title, transcript_text)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE transcript_text = VALUES(transcript_text)
            """
            cursor.execute(sql, (video_id, title, transcript))
        connection.commit()
        print(f"Successfully stored: {title}")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        connection.close()

def process_video(video_id, title):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"Processing: {title}...")
    
    transcript = get_transcript_from_tactiq(video_url)
    
    if transcript:
        store_in_db(video_id, title, transcript)
    else:
        print(f"Failed to retrieve transcript for {video_id}")

# Example Usage
if __name__ == "__main__":
    # Replace with your logic to get video list
    sample_video_id = "EXAMPLE_ID"
    sample_title = "Example Video Title"
    
    process_video(sample_video_id, sample_title)
