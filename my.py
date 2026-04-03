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
        # Check if cookies exist from your GitHub Secret
        if os.path.exists(COOKIE_FILE):
            print("Using cookies.json for authentication...")
            # Use the static method directly - this is the standard way
            transcript_list = YouTubeTranscriptApi.get_transcript(VIDEO_ID, cookies=COOKIE_FILE)
        else:
            print("Warning: cookies.json not found. Requesting without authentication...")
            transcript_list = YouTubeTranscriptApi.get_transcript(VIDEO_ID)
        
        # In the static method, it usually returns a list of dictionaries
        # We handle both formats (Object vs Dict) just to be 100% safe
        full_text = ""
        for entry in transcript_list:
            if hasattr(entry, 'text'): # If it's an object
                full_text += f"{entry.text}\n"
            else: # If it's a dictionary (standard)
                full_text += f"{entry['text']}\n"
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        # Check for specific cookie issues
        if "CookiesConfig" in str(e):
             print("Check if your YOUTUBE_JSON secret is a valid JSON list.")
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
