import sys
import os
from youtube_transcript_api import YouTubeTranscriptApi

def download_transcript():
    # --- CONFIGURATION ---
    VIDEO_ID = "YED8zVXc6As" 
    OUTPUT_FILE = "transcript.txt"
    COOKIE_FILE = "cookies.json"
    # ---------------------

    print(f"Attempting to download transcript for: {VIDEO_ID}")
    
    try:
        api = YouTubeTranscriptApi()
        
        # Check if the secret was successfully turned into a file
        if os.path.exists(COOKIE_FILE):
            print("Successfully loaded cookies from GitHub Secrets.")
            transcript_list = api.fetch(VIDEO_ID, cookies=COOKIE_FILE)
        else:
            print("Warning: cookies.json not found. Request might be blocked by YouTube.")
            transcript_list = api.fetch(VIDEO_ID)
        
        # Extracting text from the new 2026 object format
        full_text = "\n".join([snippet.text for snippet in transcript_list])
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
