from admin_tool import get_top_songs, download_song, update_manifest, get_canonical_title
import json
import subprocess

artist = "NewJeans"
songs_to_add = [
    "Attention", "Hype Boy", "Cookie", "Hurt", "Ditto", "OMG", "Zero", 
    "Be Who You Are", "Beautiful Restriction", "Gods", 
    "Our Night Is More Beautiful Than Your Day", "New Jeans", "Super Shy", 
    "ETA", "Cool With You", "Get Up", "ASAP", "How Sweet", 
    "Bubble Gum", "Supernatural", "Right Now", "Pit Stop"
]

print(f"Targeting {len(songs_to_add)} specific songs for {artist}...")

downloaded_songs = []

for title in songs_to_add:
    print(f"Searching for: {title}...")
    # Use yt-dlp to find the best match for this specific title
    search_query = f"ytsearch1:{artist} {title} official audio"
    cmd = ["yt-dlp", "--dump-json", "--flat-playlist", search_query]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\\n')
        if lines and lines[0]:
            data = json.loads(lines[0])
            # We use the title from the list for consistency
            data['cleaned_title'] = title 
            
            rel_path = download_song(data, artist)
            if rel_path:
                downloaded_songs.append({
                    "title": title,
                    "path": rel_path,
                    "popularity": data.get('view_count', 0)
                })
                print(f"Successfully added: {title}")
            else:
                print(f"Failed to download: {title}")
        else:
            print(f"No result found for: {title}")
    except Exception as e:
        print(f"Error processing {title}: {e}")

if downloaded_songs:
    # Use append=True to keep existing songs
    update_manifest(artist, downloaded_songs, append=True)
    print(f"Successfully processed {len(downloaded_songs)} songs for {artist}!")
else:
    print("No new songs were added.")
