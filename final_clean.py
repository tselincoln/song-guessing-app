import json
from pathlib import Path

p = Path.home() / "song-guessing-app" / "frontend" / "public" / "songs.json"
if not p.exists():
    exit(1)

with open(p, 'r') as f:
    data = json.load(f)

if "NewJeans" in data["artists"]:
    songs = data["artists"]["NewJeans"]["songs"]
    unique_songs = {}
    
    for s in songs:
        # More aggressive cleaning for the key
        title = s["title"]
        key = title.lower().replace("newjeans - ", "").replace(" - newjeans", "").strip()
        
        if key not in unique_songs or s["popularity"] > unique_songs[key]["popularity"]:
            # Update the title to a clean version
            if "NewJeans - " in title: title = title.replace("NewJeans - ", "")
            if " [Audio]" in title: title = title.replace(" [Audio]", "")
            
            unique_songs[key] = {**s, "title": title}
            
    data["artists"]["NewJeans"]["songs"] = list(unique_songs.values())

with open(p, 'w') as f:
    json.dump(data, f, indent=2)
print("Fixed final duplicate!")
