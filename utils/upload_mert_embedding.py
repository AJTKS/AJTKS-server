# from transformers import Wav2Vec2Processor
from transformers import Wav2Vec2FeatureExtractor
from transformers import AutoModel
import torch
from torch import nn
import torchaudio
import torchaudio.transforms as T
import os
from supabase import create_client, Client
from supabase.client import ClientOptions
import glob
from tqdm import tqdm

import dotenv

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key,
  options=ClientOptions(
    postgrest_client_timeout=10,
    storage_client_timeout=10,
    schema="public",
  ))

# loading our model weights
model = AutoModel.from_pretrained("m-a-p/MERT-v1-330M", trust_remote_code=True)
# loading the corresponding preprocessor config
processor = Wav2Vec2FeatureExtractor.from_pretrained("m-a-p/MERT-v1-330M",trust_remote_code=True)
device = "cuda" if torch.cuda.is_available() else "cpu"

model = model.to(device)
model.eval()

def cosine_similarity(matrix1, matrix2):
    # 벡터를 L2 norm으로 정규화
    matrix1_norm = matrix1 / matrix1.norm(dim=1, keepdim=True)
    matrix2_norm = matrix2 / matrix2.norm(dim=1, keepdim=True)
    
    # 정규화된 벡터들의 내적을 통해 코사인 유사도 계산
    similarity = torch.mm(matrix1_norm, matrix2_norm.t())  # Transpose the second matrix
    return similarity


def load_audio(audio_path, target_sr=16000, duration_sec=100):
    y, sr = torchaudio.load(audio_path)
    # 최대 샘플 수 계산
    max_samples = int(target_sr * duration_sec)
    
    # 리샘플러 초기화
    resampler = torchaudio.transforms.Resample(sr, target_sr)
    
    # 리샘플링
    y = resampler(y)
    
    # 오디오 길이 제한
    if y.shape[1] > max_samples:
        y = y[:, :max_samples]

    return y, target_sr

def encode_audio(x):
    xs = []
    for sub_x in x:
        all_inputs = [processor(sub_x[ix * processor.sampling_rate:min(
            (ix + 60) * processor.sampling_rate, len(sub_x))],
                                          sampling_rate=processor.sampling_rate,
                                          return_tensors="pt").to(device) for ix in
                      range(0, len(sub_x) // (processor.sampling_rate * 60) + 1, 60)]
        aggoutputs = torch.zeros(1, 25, 1024).to(device)
        for inputs in all_inputs:
            input_tensor = torch.squeeze(inputs.input_values, dim=0)
            with torch.no_grad():
                outputs = model(input_tensor, output_hidden_states=True)
            all_layer_hidden_states = torch.stack(outputs.hidden_states).squeeze()
            sub_x = all_layer_hidden_states.mean(-2).unsqueeze(0)
            sub_x = sub_x.mean(-2)
            aggoutputs += sub_x
        aggoutputs /= len(all_inputs)
        # sub_x = mu_mert_agg(aggoutputs).squeeze()
        xs.append(aggoutputs[0].mean(dim=0))
    x = torch.stack(xs, dim=0)
    return x

def get_embedding(audio_path):
    audio, _ = load_audio(audio_path)
    feature = encode_audio([audio]).cpu().detach().numpy()
    return feature

wav_dir = 'your_wav_directory'
audio_files = glob.glob(os.path.join(wav_dir, '*.wav'))
# AJTKS 테이블의 최대 ID 값 찾기
max_id_record = supabase.table('YOUR_TABLE').select('id').order('id', desc=True).limit(1).execute().data
if max_id_record:
    x = max_id_record[0]['id'] + 1
else:
    x = 1  # 테이블이 비어있는 경우 시작 ID를 1로 설정

for audio in tqdm(audio_files):
    embedding = get_embedding(audio)
    file_name = os.path.basename(audio).replace('.wav', '')
    print(f"Processing {file_name}")
    singer = file_name.split("-")[0]
    music_name = file_name.split("-")[1]
    data, count = supabase.table('YOUR_TABLE').insert({"id": x, "musicName": music_name, "singer": singer, "embedding": embedding[0].tolist()}).execute()
    x += 1
