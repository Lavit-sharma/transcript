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
        # 1. Initialize API with cookies (Modern 2026 way)
        if os.path.exists(COOKIE_FILE):
            print("Cookies found. Initializing API with authentication...")
            # THE FIX: Cookies go inside the parenthesis here
            api = YouTubeTranscriptApi(cookies=COOKIE_FILE)
        else:
            print("No cookies found. Proceeding without authentication...")
            api = YouTubeTranscriptApi()
        
        # 2. Fetch the transcript using the instance
        # THE FIX: No cookies argument here anymore
        transcript_list = api.fetch(VIDEO_ID)
        
        # 3. Extract text from the snippet objects
        # The objects have a .text attribute
        full_text = "\n".join([snippet.text for snippet in transcript_list])
        
        # 4. Save to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {str(e)}")
        # Quick debug: list what the object can actually do
        try:
            temp_api = YouTubeTranscriptApi()
            print(f"Available methods: {dir(temp_api)}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
