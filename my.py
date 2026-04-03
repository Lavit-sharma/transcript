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
        # Check if cookies exist
        if os.path.exists(COOKIE_FILE):
            print("Cookies file found. Attempting authenticated request...")
            # Use the most stable method for v1.2.1
            transcript_list = YouTubeTranscriptApi.get_transcript(VIDEO_ID, cookies=COOKIE_FILE)
        else:
            print("No cookies.json found. This will likely fail on GitHub.")
            transcript_list = YouTubeTranscriptApi.get_transcript(VIDEO_ID)

        # Process the transcript (v1.2.1 returns a list of dictionaries)
        full_text = "\n".join([entry['text'] for entry in transcript_list])
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Failed to retrieve transcript: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
