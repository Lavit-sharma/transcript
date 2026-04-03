import os
from youtube_transcript_api import YouTubeTranscriptApi

def download_transcript():
    # --- CONFIGURATION ---
    VIDEO_ID = "dQw4w9WgXcQ" 
    OUTPUT_FILE = "transcript.txt"
    # ---------------------

    print(f"Attempting to download transcript for: {VIDEO_ID}")
    
    try:
        # Use the class method directly
        transcript_data = YouTubeTranscriptApi.get_transcript(VIDEO_ID)
        
        # Join lines
        formatted_text = "\n".join([entry['text'] for entry in transcript_data])
        
        # Write file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(formatted_text)
            
        print(f"Success! Saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        # Exit with error so GitHub Actions knows it failed
        exit(1) 

if __name__ == "__main__":
    download_transcript()
