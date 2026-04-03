import sys
import os
from youtube_transcript_api import YouTubeTranscriptApi

def download_transcript():
    VIDEO_ID = "YED8zVXc6As" 
    OUTPUT_FILE = "transcript.txt"
    COOKIE_FILE = "cookies.json"

    print(f"Attempting to download transcript for: {VIDEO_ID}")
    
    try:
        api = YouTubeTranscriptApi()
        
        # In this version, we use list() to handle authentication and finding transcripts
        if os.path.exists(COOKIE_FILE):
            print("Using list() with cookies for authentication...")
            # list() returns a TranscriptList object
            transcript_list_obj = api.list(VIDEO_ID, cookies=COOKIE_FILE)
        else:
            print("No cookies found. Proceeding without authentication...")
            transcript_list_obj = api.list(VIDEO_ID)
        
        # Find the best transcript (manually created or auto-generated)
        transcript = transcript_list_obj.find_transcript(['en', 'hi'])
        
        # Fetch the actual data (this returns the snippet objects)
        data = transcript.fetch()
        
        # Access the .text attribute
        full_text = "\n".join([snippet.text for snippet in data])
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
