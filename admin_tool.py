import os
import json
import subprocess
import re
from pathlib import Path

# Configuration
PROJECT_ROOT = Path.home() / "song-guessing-app"
ASSETS_DIR = PROJECT_ROOT / "public" / "assets" / "songs"
MANIFEST_PATH = PROJECT_ROOT / "songs.json"

def slugify(text):
    """Convert text to a filesystem-friendly slug."""
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')

def get_top_songs(artist_name, limit=10):
    """Search YouTube for the top songs of an artist using yt-dlp."""
    print(f"Searching for top songs by {artist_name}...")
    
    # Use yt-dlp to get metadata of the top results for the search query
    # search: "ytsearchN:query"
    search_query = f"ytsearch{limit}:{artist_name} official audio"
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--flat-playlist",
        search_query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # yt-dlp --dump-json prints one JSON object per line
        lines = result.stdout.strip().split('\n')
        songs_data = []
        for line in lines:
            if line:
                songs_data.append(json.loads(line))
        return songs_data
    except subprocess.CalledProcessError as e:
        print(f"Error searching YouTube: {e}")
        return []

def download_song(song_info, artist_name):
    """Download the audio of a song and convert to MP3."""
    song_title = song_info.get('title', 'Unknown Song')
    video_url = f"https://www.youtube.com/watch?v={song_info.get('id')}"
    
    artist_slug = slugify(artist_name)
    song_slug = slugify(song_title)
    
    # Create artist directory
    artist_dir = ASSETS_DIR / artist_slug
    artist_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{song_slug}.mp3"
    filepath = artist_dir / filename
    
    print(f"Downloading: {song_title}...")
    
    # yt-dlp command for audio extraction to mp3
    cmd = [
        "yt-dlp",
        "-x", # extract audio
        "--audio-format", "mp3",
        "--audio-quality", "0", # best quality
        "-o", str(filepath) + ".%(ext)s", # yt-dlp handles extension
        video_url
    ]
    
    # Fix: yt-dlp might save as .mp3 but sometimes appends .mp3.mp3 if not careful
    # Actually, with --audio-format mp3 and -o path.mp3, it often outputs path.mp3.
    # We will use a temporary name and rename it to be sure.
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Handle the potential double extension or wrong extension from yt-dlp's post-processor
        # Look for the actual file created in that dir
        created_files = list(artist_dir.glob(f"{song_slug}*"))
        if created_files:
            final_file = created_files[0]
            if final_file.suffix != ".mp3":
                final_file.rename(filepath)
            return str(filepath.relative_to(PROJECT_ROOT))
    except subprocess.CalledProcessError as e:
        print(f"Failed to download {song_title}: {e}")
        return None

def update_manifest(artist_name, song_details):
    """Update the songs.json manifest file."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"artists": {}}
    else:
        data = {"artists": {}}
    
    if artist_name not in data["artists"]:
        data["artists"][artist_name] = {"songs": []}
    
    # Remove duplicates if any
    existing_titles = [s["title"] for s in data["artists"][artist_name]["songs"]]
    
    for song in song_details:
        if song["title"] not in existing_titles:
            data["artists"][artist_name]["songs"].append(song)
    
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    print("--- Song Guessing App: Admin Artist Tool ---")
    while True:
        artist_name = input("\nEnter artist name to add (or 'exit' to quit): ").strip()
        if artist_name.lower() == 'exit':
            break
        
        if not artist_name:
            continue
            
        top_songs = get_top_songs(artist_name)
        if not top_songs:
            print("No songs found for this artist.")
            continue
            
        downloaded_songs = []
        for song_info in top_songs:
            title = song_info.get('title', 'Unknown')
            view_count = song_info.get('view_count', 0)
            
            # Download and get the relative path
            rel_path = download_song(song_info, artist_name)
            
            if rel_path:
                downloaded_songs.append({
                    "title": title,
                    "path": rel_path,
                    "popularity": view_count
                })
        
        if downloaded_songs:
            update_manifest(artist_name, downloaded_songs)
            print(f"Successfully added {len(downloaded_songs)} songs for {artist_name}!")
        else:
            print("Failed to download any songs.")

if __name__ == "__main__":
    main()
