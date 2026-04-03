import sys
from youtube_transcript_api import YouTubeTranscriptApi

def download_transcript():
    # --- CONFIGURATION ---
    VIDEO_ID = "dQw4w9WgXcQ" 
    OUTPUT_FILE = "transcript.txt"
    # ---------------------

    print(f"Attempting to download transcript for: {VIDEO_ID}")
    
    try:
        # 1. Initialize the API instance
        api = YouTubeTranscriptApi()
        
        # 2. Use the new .fetch() method
        # Note: fetch returns a list of dictionaries, just like the old method
        transcript_list = api.fetch(VIDEO_ID)
        
        # 3. Process and save
        full_text = "\n".join([entry['text'] for entry in transcript_list])
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
