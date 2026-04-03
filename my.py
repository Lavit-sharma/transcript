import sys
import os
from youtube_transcript_api import YouTubeTranscriptApi

def download_transcript():
    VIDEO_ID = "YED8zVXc6As" 
    OUTPUT_FILE = "transcript.txt"
    COOKIE_FILE = "cookies.json"

    print(f"Attempting to download transcript for: {VIDEO_ID}")
    
    try:
        # Step 1: Use the static list_transcripts method (the most stable entry point)
        if os.path.exists(COOKIE_FILE):
            print("Authenticating with cookies.json...")
            transcript_list = YouTubeTranscriptApi.list_transcripts(VIDEO_ID, cookies=COOKIE_FILE)
        else:
            print("No cookies found. Proceeding without authentication...")
            transcript_list = YouTubeTranscriptApi.list_transcripts(VIDEO_ID)
        
        # Step 2: Find the best transcript (English or Hindi preferred)
        transcript = transcript_list.find_transcript(['en', 'hi'])
        
        # Step 3: Fetch the data
        data = transcript.fetch()
        
        # Step 4: Handle different data return types (Object vs Dict)
        full_text = ""
        for entry in data:
            if hasattr(entry, 'text'):
                full_text += f"{entry.text}\n"
            else:
                full_text += f"{entry['text']}\n"
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
