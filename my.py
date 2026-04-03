import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_youtube_transcript(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Run without a window
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"Opening URL: {url}")
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # 1. Click "More" in the description to reveal the transcript button
        expand_button = wait.until(EC.element_to_be_clickable((By.ID, "expand")))
        expand_button.click()
        time.sleep(2)

        # 2. Click "Show transcript" button
        # This button is usually inside the primary info renderer
        transcript_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Show transcript']")))
        transcript_button.click()
        print("Transcript window opened.")
        time.sleep(3)

        # 3. Scrape all transcript lines
        segments = driver.find_elements(By.CSS_SELECTOR, "ytd-transcript-segment-renderer")
        
        transcript_text = ""
        for segment in segments:
            text = segment.find_element(By.CLASS_NAME, "segment-text").text
            transcript_text += text + "\n"

        if transcript_text:
            with open("transcript.txt", "w", encoding="utf-8") as f:
                f.write(transcript_text)
            print("Success! Transcript saved.")
        else:
            print("Failed to find transcript segments.")

    except Exception as e:
        print(f"Error: {e}")
        driver.save_screenshot("error_screenshot.png") # Debugging
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    target_url = "https://www.youtube.com/watch?v=YED8zVXc6As"
    scrape_youtube_transcript(target_url)
