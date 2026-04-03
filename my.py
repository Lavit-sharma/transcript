import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

def get_video_id(youtube_url):
    """Extract video ID from YouTube URL"""
    parsed = urllib.parse.urlparse(youtube_url)
    
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]
    
    if "youtube.com" in parsed.hostname:
        query = urllib.parse.parse_qs(parsed.query)
        return query.get("v", [None])[0]
    
    return None


def fetch_transcript(youtube_url):
    video_id = get_video_id(youtube_url)

    if not video_id:
        print("❌ Invalid YouTube URL")
        return None

    # Build dynamic Tactiq URL
    tactiq_url = f"https://tactiq.io/tools/run/youtube_transcript?yt={urllib.parse.quote(youtube_url)}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(tactiq_url, headers=headers)

    if response.status_code != 200:
        print("❌ Failed to fetch page")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract transcript (this may change if site structure changes)
    transcript_blocks = soup.find_all("p")

    transcript = "\n".join([p.get_text(strip=True) for p in transcript_blocks])

    return transcript


if __name__ == "__main__":
    # Example: pass URL as argument OR hardcode for testing
    if len(sys.argv) > 1:
        youtube_url = sys.argv[1]
    else:
        youtube_url = "https://www.youtube.com/watch?v=huW5sxhm3ow"

    transcript = fetch_transcript(youtube_url)

    if transcript:
        print("\n===== TRANSCRIPT =====\n")
        print(transcript)

        # Save to file (useful for GitHub Actions)
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript)

        print("\n✅ Saved to transcript.txt")
