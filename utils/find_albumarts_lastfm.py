import os
import requests
from PIL import Image
from io import BytesIO

# Last.fm API Credentials
LASTFM_API_KEY = 'your_api_kry'

def get_lastfm_album_art_url(artist, track):
    search_url = 'http://ws.audioscrobbler.com/2.0/'
    params = {
        'method': 'track.search',
        'track': track,
        'artist': artist,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': 1,
    }

    response = requests.get(search_url, params=params)
    data = response.json()
    if 'results' in data and 'trackmatches' in data['results']:
        tracks = data['results']['trackmatches']['track']
        if isinstance(tracks, list) and len(tracks) > 0:
            album_art_url = tracks[0]['image'][-1]['#text']                                                                                                                                                                                                     
            return album_art_url
    return None

def download_image(url, save_path):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))

    # RGBA 모드를 RGB 모드로 변환합니다.
    if image.mode == 'RGBA':
        image = image.convert('RGB')

    image.save(save_path)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           

def main(mp3_files_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)                                                                
    
    for filename in os.listdir(mp3_files_directory):
        if filename.endswith('.wav'):
            # Extract artist and track name from filename
            # Assuming filename format is "Artist - Track.mp3"
            artist, track = os.path.splitext(filename)[0].split('-', 1)
            album_art_url = get_lastfm_album_art_url(artist, track)
            if album_art_url:
                output_image_path = os.path.join(output_directory, f"{os.path.splitext(filename)[0]}.jpg")
                download_image(album_art_url, output_image_path)
                print(f"Downloaded album art for {filename}")
            else:
                print(f"Album art not found for {filename}")

# 사용 예시
mp3_files_directory = 'your_directory'  # MP3 파일들이 있는 디렉터리 경로
output_directory = 'your_directory'  # 다운로드된 앨범 사진을 저장할 디렉터리 경로

main(mp3_files_directory, output_directory)