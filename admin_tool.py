import os
import json
import subprocess
import re
import shutil
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

def clean_title(title, artist_name=""):
    """Remove YouTube fluff and artist name from song titles for a clean display."""
    cleaned = title
    
    # 1. Strip translated artist names often put in brackets
    cleaned = re.sub(r'\((?:뉴진스|ニュージーンズ)\)', '', cleaned, flags=re.IGNORECASE)
    
    # 2. General bracket fluff removal
    bracket_patterns = [
        r'[([「【<].*?(?:official|audio|video|mv|lyric|performance|dance|ver\.|part\.|topic).*?[)\]」】>]'
    ]
    for p in bracket_patterns:
        cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE)
        
    # 3. Loose fluff removal (Expanded to catch "Performance Video")
    loose_fluff = [
        r'official mv', r'official video', r'official audio', 
        r'lyrics', r'lyric video', r'music video', r'audio clip',
        r'performance ver\.?\d*', r'part\.?\d*', r'performance video', 
        r'performance', r'dance practice', r'special video'
    ]
    for fluff in loose_fluff:
        cleaned = re.sub(rf'(?i)\b{fluff}\b', '', cleaned)

    # 4. Strip the artist name (Made dash/separator optional)
    if artist_name:
        artist_pattern = re.escape(artist_name)
        cleaned = re.sub(rf'(?i)^{artist_pattern}\s*[-:\|]?\s*', '', cleaned)
        cleaned = re.sub(rf'(?i)\s*[-:\|]?\s*{artist_pattern}$', '', cleaned)

    # 5. Clean up dangling characters, all quotes, and whitespace
    cleaned = re.sub(r'[\'\"‘’“”「」]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(" -|:")
    
    return cleaned

def get_canonical_title(title, artist_name=""):
    """Generate a highly simplified string for aggressive deduplication."""
    canonical = title.lower()
    # Strip features/collaborations
    canonical = re.split(r'\b(?:ft\.?|feat\.?|featuring)\b', canonical)[0]
    # Remove all non-alphanumeric characters
    canonical = re.sub(r'[^a-z0-9]', '', canonical)
    
    # FINAL SAFETY NET: Strip the artist name completely from the canonical ID
    if artist_name:
        artist_canonical = re.sub(r'[^a-z0-9]', '', artist_name.lower())
        if artist_canonical:
            # Only remove if it doesn't leave the string entirely empty
            # (e.g. if the song is literally named after the artist)
            temp = canonical.replace(artist_canonical, '')
            if temp != "":
                canonical = temp
                
    return canonical

def is_playlist(title):
    """Detect if a result is likely a playlist or album."""
    blacklist = ['playlist', 'full album', 'all songs', 'compilation', 'mix']
    return any(word in title.lower() for word in blacklist)

def get_top_songs(artist_name, limit=10):
    """Search YouTube for the top songs of an artist using yt-dlp, ensuring uniqueness."""
    print(f"Searching for unique clean songs by {artist_name}...")
    
    search_query = f"ytsearch{limit * 5}:{artist_name} official audio"
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
        seen_canonical_titles = set()
        
        for line in lines:
            if line:
                data = json.loads(line)
                raw_title = data.get('title', '')
                
                # Clean the display title
                display_title = clean_title(raw_title, artist_name)
                # Generate strict canonical ID
                canonical = get_canonical_title(display_title, artist_name)
                
                if not is_playlist(raw_title) and canonical not in seen_canonical_titles and canonical != "":
                    # Store the cleaned title so we don't have to clean it again
                    data['cleaned_title'] = display_title 
                    songs_data.append(data)
                    seen_canonical_titles.add(canonical)
                
                if len(songs_data) >= limit:
                    break
        return songs_data
    except subprocess.CalledProcessError as e:
        print(f"Error searching YouTube: {e}")
        return []

def download_song(song_info, artist_name):
    """Download the audio of a song and convert to MP3."""
    song_title = song_info.get('cleaned_title', 'Unknown Song')
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
            shutil.copy(actual_file, dest)
            
        # Clean up temp
        actual_file.unlink()
        
        return f"assets/songs/{artist_slug}/{filename}"
    except Exception as e:
        print(f"Failed to download {song_title}: {e}")
        return None

def update_manifest(artist_name, song_details, append=False):
    """Update the songs.json manifest file. If append=True, adds to existing list instead of replacing."""
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
        
        if append:
            # Only add songs that aren't already in the list (by title)
            existing_titles = {s['title'] for s in data["artists"][artist_name]["songs"]}
            for s in song_details:
                if s['title'] not in existing_titles:
                    data["artists"][artist_name]["songs"].append(s)
        else:
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
            title = song_info.get('cleaned_title', 'Unknown')
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
