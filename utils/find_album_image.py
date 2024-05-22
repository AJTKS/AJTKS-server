import os
import requests
from PIL import Image
from io import BytesIO

# Spotify API Credentials
CLIENT_ID = 'YOUR_SPOTIFY_API_KEY'
CLIENT_SECRET = 'YOUR_SPOTIFY_SECRET_KEY'

def get_spotify_token(client_id, client_secret):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })

    auth_response_data = auth_response.json()
    return auth_response_data['access_token']

def get_album_art_url(artist, track, token):
    search_url = 'https://api.spotify.com/v1/search'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    params = {
        'q': f'artist:{artist} track:{track}',
        'type': 'track',
        'limit': 1,
    }

    response = requests.get(search_url, headers=headers, params=params)
    data = response.json()
    tracks = data['tracks']['items']
    if not tracks:
        return None
    album_art_url = tracks[0]['album']['images'][0]['url']
    return album_art_url

def download_image(url, save_path):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    image.save(save_path)

def main(mp3_files_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    token = get_spotify_token(CLIENT_ID, CLIENT_SECRET)
    
    for filename in os.listdir(mp3_files_directory):
        if filename.endswith('.wav'):
            # Extract artist and track name from filename
            # Assuming filename format is "Artist - Track.mp3"
            artist, track = os.path.splitext(filename)[0].split('-', 1)
            album_art_url = get_album_art_url(artist, track, token)
            if album_art_url:
                output_image_path = os.path.join(output_directory, f"{os.path.splitext(filename)[0]}.jpg")
                download_image(album_art_url, output_image_path)
                print(f"Downloaded album art for {filename}")
            else:
                print(f"Album art not found for {filename}")

# 사용 예시
mp3_files_directory = 'YOUR_DIRECTORY'  # MP3 파일들이 있는 디렉터리 경로
output_directory = 'YOUR_DIRECTORY'  # 다운로드된 앨범 사진을 저장할 디렉터리 경로

main(mp3_files_directory, output_directory)