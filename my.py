import sys
import os
import json
from youtube_transcript_api import YouTubeTranscriptApi

def download_transcript():
    VIDEO_ID = "YED8zVXc6As" 
    OUTPUT_FILE = "transcript.txt"
    COOKIE_FILE = "cookies.json"

    print(f"Attempting to download transcript for: {VIDEO_ID}")
    
    try:
        # Load cookies manually from the file to ensure they are valid
        cookies = None
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, 'r') as f:
                cookies = json.load(f)
            print("Cookies loaded manually from file.")

        # In the absolute latest version, we use the list() method 
        # but we handle it via the class instance to avoid attribute errors
        api = YouTubeTranscriptApi()
        
        # We use a universal way to call the retrieval
        # If 'list' works but 'cookies' argument doesn't, we'll try a different route
        try:
            # Attempt 1: The standard list method (no cookies if the argument is rejected)
            transcript_list = api.list(VIDEO_ID) 
        except TypeError:
            # Attempt 2: If it fails, we use the raw fetcher which is usually more stable
            print("Standard list failed, using raw retrieval...")
            # This is a safe way to get transcripts in the newest builds
            transcript_list = YouTubeTranscriptApi.get_transcripts([VIDEO_ID], cookies=COOKIE_FILE)[0][VIDEO_ID]

        # Get the actual data
        # We try to find English, then Hindi, then whatever is available
        try:
            transcript = transcript_list.find_transcript(['en', 'hi'])
        except:
            # Just get the first available one if en/hi aren't found
            transcript = next(iter(transcript_list))

        data = transcript.fetch()
        
        # Format the text (Handling both objects and dictionaries)
        lines = []
        for entry in data:
            if hasattr(entry, 'text'):
                lines.append(entry.text)
            elif isinstance(entry, dict):
                lines.append(entry['text'])
        
        full_text = "\n".join(lines)
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"All methods failed. Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
