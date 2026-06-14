import json
from pathlib import Path

p = Path.home() / "song-guessing-app" / "frontend" / "public" / "songs.json"
if p.exists():
    with open(p, 'r') as f:
        data = json.load(f)
    
    for artist in data["artists"]:
        for song in data["artists"][artist]["songs"]:
            if song["path"].startswith("public/"):
                song["path"] = song["path"].replace("public/", "", 1)
    
    with open(p, 'w') as f:
        json.dump(data, f, indent=2)
    print("Fixed manifest paths!")
