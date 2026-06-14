from admin_tool import get_top_songs, download_song, update_manifest, clean_title

artist = "NewJeans"
limit = 10

print(f"Expanding library to {limit} CLEAN songs for {artist}...")
top_songs = get_top_songs(artist, limit=limit)

if not top_songs:
    print("No songs found.")
    exit(1)

downloaded_songs = []
for song_info in top_songs:
    title = song_info.get('title', 'Unknown')
    clean_t = clean_title(title)
    view_count = song_info.get('view_count', 0)
    
    rel_path = download_song(song_info, artist)
    
    if rel_path:
        downloaded_songs.append({
            "title": clean_t,
            "path": rel_path,
            "popularity": view_count
        })

if downloaded_songs:
    update_manifest(artist, downloaded_songs)
    print(f"Successfully expanded to {len(downloaded_songs)} clean songs for {artist}!")
else:
    print("Failed to download songs.")
