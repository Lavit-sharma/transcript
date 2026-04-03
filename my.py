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
        # 1. Check for cookies to bypass YouTube IP block
        if os.path.exists(COOKIE_FILE):
            print("Using cookies.json for authentication...")
            # Using the most stable static method
            transcript_list = YouTubeTranscriptApi.get_transcript(VIDEO_ID, cookies=COOKIE_FILE)
        else:
            print("Warning: cookies.json not found. Requesting without authentication...")
            transcript_list = YouTubeTranscriptApi.get_transcript(VIDEO_ID)
        
        # 2. Handle both Dictionary (v1.2.1) and Object (v1.2.4+) return types
        full_text = ""
        for entry in transcript_list:
            if hasattr(entry, 'text'):  # New Object format (.text)
                full_text += f"{entry.text}\n"
            elif isinstance(entry, dict): # Old Dictionary format (['text'])
                full_text += f"{entry['text']}\n"
        
        # 3. Save the result
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Primary method failed: {str(e)}")
        # FALLBACK: If the static method fails, try the Instance method (fetch)
        try:
            print("Attempting fallback fetch method...")
            api = YouTubeTranscriptApi()
            # If cookies are required for fetch in your specific version
            t_list = api.fetch(VIDEO_ID, cookies=COOKIE_FILE) if os.path.exists(COOKIE_FILE) else api.fetch(VIDEO_ID)
            f_text = "\n".join([getattr(x, 'text', x.get('text')) for x in t_list])
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(f_text)
            print("Success on fallback!")
        except Exception as e2:
            print(f"Final Failure: {str(e2)}")
            sys.exit(1)

if __name__ == "__main__":
    download_transcript()
