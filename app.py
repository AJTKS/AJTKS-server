import os
from supabase import create_client, Client
from supabase.client import ClientOptions
from flask import Flask, jsonify, request, render_template, url_for, redirect, send_from_directory
from dotenv import load_dotenv
from mert import get_embedding
from werkzeug.utils import secure_filename
from tasks import process_audio
from pydub import AudioSegment
from flask_cors import CORS
from youtubesearchpython import VideosSearch

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://www.example.com"])
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MP3_FILES'] = 'mp3'
app.config['ALBUM_ART_FOLDER'] = 'album_arts'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB로 파일 크기 제한

ALLOWED_EXTENSIONS = {'mp3', 'wav'}

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key,
  options=ClientOptions(
    postgrest_client_timeout=10,
    storage_client_timeout=10,
    schema="public",
  ))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    

def convert_mp3_to_wav(mp3_filepath, wav_directory):
    audio = AudioSegment.from_mp3(mp3_filepath)
    wav_filename = os.path.splitext(os.path.basename(mp3_filepath))[0] + '.wav'  # Change the extension to .wav
    wav_filepath = os.path.join(wav_directory, wav_filename)
    audio.export(wav_filepath, format='wav')
    return wav_filepath

# @celery.task
# def process_audio(file_path):
#     embedding = get_embedding(file_path)
#     response = supabase.table('MuxicRecommend').select('musicName, Singer, 1 - (Vector <=> {}) as similarity'.format(embedding)).order('similarity', desc=True).limit(3).execute()
#     if response.error:
#         return {'error': str(response.error)}
#     return response.data

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['post'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        if filename.rsplit('.', 1)[1].lower() == 'mp3':
            filepath = os.path.join(app.config['MP3_FILES'], filename)
            file.save(filepath)
            wav_filepath = convert_mp3_to_wav(filepath, app.config['UPLOAD_FOLDER'])
            task = process_audio.delay(wav_filepath)
        else:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            task = process_audio.delay(filepath)
        
        return jsonify({"task_id": task.id})

    else:
        return jsonify({"error": "File type not allowed"}), 400

@app.route('/task/<task_id>')
def get_status(task_id):
    task = process_audio.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Pending...'}

        return jsonify(response)
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'result': task.result}
        result = {"searchResult": []}
        for r in response["result"]["search_results"]:
            music_name, singer, description, distance = r["musicName"], r["singer"], r["description"], r["similarity"]
            album_art_filename = f"{singer}-{music_name}.jpg"
            album_art_path = os.path.join(app.config['ALBUM_ART_FOLDER'], album_art_filename)
            if os.path.exists(album_art_path):
                album_art_url = url_for('album_art', filename=album_art_filename)
            else:
                album_art_url = None  # or provide a default image URL
            video_search = VideosSearch(f'{singer}-{music_name} audio', limit=1)
            result["searchResult"].append({
                "musicName": music_name,
                "singer": singer,
                "description": description,
                "distance": distance,
                "albumArt": album_art_url,
                "link": video_search.result()['result'][0]['link']
            })
        result["recommendation"] = response["result"]["recommendation"]
        return jsonify(result)

    elif task.state == 'FAILURE':
        response = {'state': task.state, 'status': str(task.info)}  # 예외 정보
        return jsonify(response)

@app.route('/album_arts/<filename>')
def album_art(filename):
    return send_from_directory(app.config['ALBUM_ART_FOLDER'], filename)
    

@app.route('/status/<task_id>')
def render_status(task_id):
    return render_template('status.html', task_id=task_id)
    

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['MP3_FILES']):
        os.makedirs(app.config['MP3_FILES'])
    app.run(host='0.0.0.0', port=5000)