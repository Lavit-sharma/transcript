import sys
import youtube_transcript_api

def download_transcript():
    # --- CONFIGURATION ---
    VIDEO_ID = "dQw4w9WgXcQ" 
    OUTPUT_FILE = "transcript.txt"
    # ---------------------

    print(f"Attempting to download transcript for: {VIDEO_ID}")
    
    try:
        # Accessing the class through the module to avoid attribute errors
        # This is the safest way to call it in automation environments
        transcript_list = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(VIDEO_ID)
        
        # Extract text and join with newlines
        lines = [entry['text'] for entry in transcript_list]
        full_text = "\n".join(lines)
        
        # Write to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        # Exit with error code 1 so GitHub knows it failed
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
