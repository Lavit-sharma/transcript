import os
from youtube_transcript_api import YouTubeTranscriptApi

def download_transcript():
    # --- CONFIGURATION ---
    # Replace this ID with the one you want to download
    VIDEO_ID = "dQw4w9WgXcQ" 
    OUTPUT_FILE = "transcript.txt"
    # ---------------------

    print(f"Attempting to download transcript for: {VIDEO_ID}")
    
    try:
        # Fetching transcript
        transcript_data = YouTubeTranscriptApi.get_transcript(VIDEO_ID)
        
        # Formatting: Joining all text lines with a newline
        formatted_text = "\n".join([entry['text'] for entry in transcript_data])
        
        # Saving to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(formatted_text)
            
        print(f"Success! Saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    download_transcript()
