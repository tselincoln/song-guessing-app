from admin_tool import get_top_songs, download_song, update_manifest

artist = "NewJeans"
limit = 5

print(f"Bootstrapping 5 songs for {artist}...")
top_songs = get_top_songs(artist, limit=limit)

if not top_songs:
    print("No songs found.")
    exit(1)

downloaded_songs = []
for song_info in top_songs:
    title = song_info.get('title', 'Unknown')
    view_count = song_info.get('view_count', 0)
    
    rel_path = download_song(song_info, artist)
    
    if rel_path:
        downloaded_songs.append({
            "title": title,
            "path": rel_path,
            "popularity": view_count
        })

if downloaded_songs:
    update_manifest(artist, downloaded_songs)
    print(f"Successfully bootstrapped {len(downloaded_songs)} songs for {artist}!")
else:
    print("Failed to download songs.")
