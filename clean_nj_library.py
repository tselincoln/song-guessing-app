import json
from pathlib import Path

p = Path.home() / "song-guessing-app" / "frontend" / "public" / "songs.json"
if not p.exists():
    print("Manifest not found")
    exit(1)

with open(p, 'r') as f:
    data = json.load(f)

# Manual Mapping for NewJeans
mapping = {
    "NewJeans": {
        "Super Shy": "Super Shy",
        "Get Up": "Get Up",
        "Attention": "Attention",
        "Hype Boy": "Hype Boy",
        "Supernatural": "Supernatural",
        "New Jeans": "New Jeans"
    }
}

def clean_nj_title(title):
    title_lower = title.lower()
    if "super shy" in title_lower: return "Super Shy"
    if "get up" in title_lower: return "Get Up"
    if "attention" in title_lower: return "Attention"
    if "hype boy" in title_lower: return "Hype Boy"
    if "supernatural" in title_lower: return "Supernatural"
    if "new jeans" in title_lower: return "New Jeans"
    return title

if "NewJeans" in data["artists"]:
    original_songs = data["artists"]["NewJeans"]["songs"]
    unique_songs = {}

    for song in original_songs:
        clean_t = clean_nj_title(song["title"])
        # If we have multiple versions of the same song, keep the one with the highest popularity
        if clean_t not in unique_songs or song["popularity"] > unique_songs[clean_t]["popularity"]:
            unique_songs[clean_t] = song
            # Update the title to the clean version
            song["title"] = clean_t

    data["artists"]["NewJeans"]["songs"] = list(unique_songs.values())

with open(p, 'w') as f:
    json.dump(data, f, indent=2)
print("Successfully cleaned and deduped NewJeans songs!")
