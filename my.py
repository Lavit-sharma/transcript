import sys
from youtube_transcript_api import YouTubeTranscriptApi

def download_transcript():
    # --- CONFIGURATION ---
    VIDEO_ID = "YED8zVXc6As" 
    OUTPUT_FILE = "transcript.txt"
    # ---------------------

    print(f"Attempting to download transcript for: {VIDEO_ID}")
    
    try:
        # 1. Initialize API
        api = YouTubeTranscriptApi()
        
        # 2. Fetch the transcript (Returns a list of FetchedTranscriptSnippet objects)
        transcript_list = api.fetch(VIDEO_ID)
        
        # 3. FIX: Access as object attributes (.text) instead of dict keys (['text'])
        # The new objects have .text, .start, and .duration attributes
        full_text = "\n".join([snippet.text for snippet in transcript_list])
        
        # 4. Save to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Success! Transcript saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_transcript()
