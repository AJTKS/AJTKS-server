import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image, UnidentifiedImageError
import io

def extract_album_art(mp3_file_path, output_image_path):
    # MP3 파일에서 ID3 태그를 읽습니다.
    audio = MP3(mp3_file_path, ID3=ID3)

    # APIC 프레임 (앨범 커버 이미지)이 있는지 확인합니다.
    for tag in audio.tags.values():
        if isinstance(tag, APIC):
            album_art = tag.data
            break
    else:
        raise ValueError(f"앨범 사진을 찾을 수 없습니다: {mp3_file_path}")

    # 앨범 사진을 이미지 파일로 저장합니다.
    try:
        image = Image.open(io.BytesIO(album_art))
        
        # 'P' 모드일 경우 RGB 모드로 변환
        if image.mode in ['P', 'RGBA']:
            image = image.convert('RGB')
        
        image.save(output_image_path)
    except UnidentifiedImageError:
        print(f"이미지 파일을 인식할 수 없습니다: {mp3_file_path}")

def extract_album_art_from_directory(directory_path, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    for filename in os.listdir(directory_path):
        if filename.endswith('.mp3'):
            mp3_file_path = os.path.join(directory_path, filename)
            output_image_path = os.path.join(output_directory, f"{os.path.splitext(filename)[0]}.jpg")
            try:
                extract_album_art(mp3_file_path, output_image_path)
                print(f"Extracted album art from {mp3_file_path} to {output_image_path}")
            except ValueError as e:
                print(e)

# 사용 예시
directory_path = 'YOUR_DIRECTORY'  # MP3 파일들이 있는 디렉터리 경로
output_directory = 'YOUR_DIRECTORY'  # 추출된 앨범 사진을 저장할 디렉터리 경로

extract_album_art_from_directory(directory_path, output_directory)