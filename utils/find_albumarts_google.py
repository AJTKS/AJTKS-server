import os
import requests
from PIL import Image, UnidentifiedImageError
from io import BytesIO

# Google Custom Search API Credentials
API_KEY = 'YOUR_GOOGLE_API_KEY'  # 생성한 Google API 키
CX = 'YOUR_CX_KEY'     # 생성한 Custom Search 엔진 ID

def get_google_album_art_urls(artist, track):
    search_url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': f'{artist} {track} album art',
        'cx': CX,
        'key': API_KEY,
        'searchType': 'image',
        'num': 10,  # 최대 5개의 결과를 가져옵니다
    }

    response = requests.get(search_url, params=params)
    data = response.json()
    if 'items' in data:
        return [item['link'] for item in data['items']]
    return []

def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        try:
            image = Image.open(BytesIO(response.content))

            # P 모드를 RGB 모드로 변환합니다.
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')

            image.save(save_path)
            return True
        except (IOError, UnidentifiedImageError):
            print(f"Unable to identify image from {url}")
    else:
        print(f"Failed to download image from {url}, status code: {response.status_code}")
    return False

def main(mp3_files_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    for filename in os.listdir(mp3_files_directory):
        if filename.endswith('.wav'):
            # Extract artist and track name from filename
            # Assuming filename format is "Artist - Track.mp3"
            try:
                artist, track = os.path.splitext(filename)[0].split('-', 1)
            except ValueError:
                print(f"Skipping file with invalid format: {filename}")
                continue
            
            album_art_urls = get_google_album_art_urls(artist, track)
            success = False
            for url in album_art_urls:
                output_image_path = os.path.join(output_directory, f"{os.path.splitext(filename)[0]}.jpg")
                if download_image(url, output_image_path):
                    print(f"Downloaded album art for {filename}")
                    success = True
                    break
            
            if not success:
                print(f"Failed to download album art for {filename}")

# 사용 예시
mp3_files_directory = 'yout_directory'  # MP3 파일들이 있는 디렉터리 경로
output_directory = 'your_directory'  # 다운로드된 앨범 사진을 저장할 디렉터리 경로

main(mp3_files_directory, output_directory)
