import os
import json
import subprocess
import re
from pathlib import Path

# Configuration
PROJECT_ROOT = Path.home() / "song-guessing-app"
ASSETS_DIR = PROJECT_ROOT / "public" / "assets" / "songs"
FRONTEND_ASSETS_DIR = PROJECT_ROOT / "frontend" / "public" / "assets" / "songs"
MANIFEST_PATH = PROJECT_ROOT / "songs.json"
FRONTEND_MANIFEST_PATH = PROJECT_ROOT / "frontend" / "public" / "songs.json"

def slugify(text):
    """Convert text to a filesystem-friendly slug."""
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')

def clean_title(title):
    """Remove YouTube fluff from song titles."""
    # Patterns to remove
    patterns = [
        r'\(Official\s*MV\)', r'\[Official\s*MV\]',
        r'\(Official\s*Audio\)', r'\[Official\s*Audio\]',
        r'\(Lyrics\)', r'\[Lyrics\]',
        r'\(Color\s*Coded\s*Lyrics\)', r'\[Color\s*Coded\s*Lyrics\]',
        r'\(뉴진스\s*.*?\)', r'\[뉴진스\s*.*?\]',
        r'\(Official\s*Video\)', r'\[Official\s*Video\]',
        r'\(Lyric\s*Video\)', r'\[Lyric\s*Video\]',
        r'\(Topic\)', r'\[Topic\]'
    ]
    cleaned = title
    for p in patterns:
        cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE)
    
    # Remove trailing/leading spaces and weird characters
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def is_playlist(title):
    """Detect if a result is likely a playlist or album."""
    blacklist = ['playlist', 'full album', 'all songs', 'compilation', 'mix']
    return any(word in title.lower() for word in blacklist)

def get_top_songs(artist_name, limit=10):
    """Search YouTube for the top songs of an artist using yt-dlp."""
    print(f"Searching for clean songs by {artist_name}...")
    
    # specifically search for "official audio" to avoid playlists
    search_query = f"ytsearch{limit * 2}:{artist_name} official audio"
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--flat-playlist",
        search_query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        songs_data = []
        for line in lines:
            if line:
                data = json.loads(line)
                title = data.get('title', '')
                if not is_playlist(title):
                    songs_data.append(data)
                if len(songs_data) >= limit:
                    break
        return songs_data
    except subprocess.CalledProcessError as e:
        print(f"Error searching YouTube: {e}")
        return []

def download_song(song_info, artist_name):
    """Download the audio of a song and convert to MP3."""
    raw_title = song_info.get('title', 'Unknown Song')
    song_title = clean_title(raw_title)
    video_url = f"https://www.youtube.com/watch?v={song_info.get('id')}"
    
    artist_slug = slugify(artist_name)
    song_slug = slugify(song_title)
    
    # We want to save to BOTH root and frontend for consistency
    paths = [ASSETS_DIR / artist_slug, FRONTEND_ASSETS_DIR / artist_slug]
    
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)
    
    filename = f"{song_slug}.mp3"
    
    print(f"Downloading: {song_title}...")
    
    # Use a temp file to ensure we don't end up with .mp3.mp3
    temp_output = f"{PROJECT_ROOT}/temp_{song_slug}"
    
    cmd = [
        "yt-dlp",
        "-x", 
        "--audio-format", "mp3",
        "--audio-quality", "0", 
        "-o", temp_output, 
        video_url
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Find the resulting file (yt-dlp adds extension)
        actual_file = list(PROJECT_ROOT.glob(f"temp_{song_slug}*"))[0]
        
        # Move to both locations
        for p in paths:
            dest = p / filename
            import shutil
            shutil.copy(actual_file, dest)
            
        # Clean up temp
        actual_file.unlink()
        
        return f"assets/songs/{artist_slug}/{filename}"
    except Exception as e:
        print(f"Failed to download {song_title}: {e}")
        return None

def update_manifest(artist_name, song_details):
    """Update the songs.json manifest file."""
    manifests = [MANIFEST_PATH, FRONTEND_MANIFEST_PATH]
    
    for path in manifests:
        if not path.exists():
            data = {"artists": {}}
        else:
            with open(path, 'r') as f:
                try: data = json.load(f)
                except: data = {"artists": {}}
        
        if artist_name not in data["artists"]:
            data["artists"][artist_name] = {"songs": []}
        
        # Clear existing songs for this artist to avoid mixing old messy ones
        data["artists"][artist_name]["songs"] = song_details
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

def main():
    print("--- Song Guessing App: Pro Artist Tool ---")
    while True:
        artist_name = input("\nEnter artist name to add (or 'exit' to quit): ").strip()
        if artist_name.lower() == 'exit':
            break
        
        if not artist_name:
            continue
            
        top_songs = get_top_songs(artist_name)
        if not top_songs:
            print("No clean songs found for this artist.")
            continue
            
        downloaded_songs = []
        for song_info in top_songs:
            title = clean_title(song_info.get('title', 'Unknown'))
            view_count = song_info.get('view_count', 0)
            
            rel_path = download_song(song_info, artist_name)
            
            if rel_path:
                downloaded_songs.append({
                    "title": title,
                    "path": rel_path,
                    "popularity": view_count
                })
        
        if downloaded_songs:
            update_manifest(artist_name, downloaded_songs)
            print(f"Successfully added {len(downloaded_songs)} clean songs for {artist_name}!")
        else:
            print("Failed to download any clean songs.")

if __name__ == "__main__":
    main()
