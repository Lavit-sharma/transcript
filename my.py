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
        # 1. Initialize API with cookies if they exist
        if os.path.exists(COOKIE_FILE):
            print("Initializing API with cookies from GitHub Secrets...")
            # In the latest version, cookies go here in the constructor
            api = YouTubeTranscriptApi(cookies=COOKIE_FILE)
        else:
            print("Warning: cookies.json not found. Requesting without authentication...")
            api = YouTubeTranscriptApi()
        
        # 2. Fetch the transcript (no arguments needed here except the ID)
        transcript_list = api.fetch(VIDEO_ID)
        
        # 3. Process the objects using the .text attribute
        full_text = "\n".join([snippet.text for snippet in transcript_list])
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
