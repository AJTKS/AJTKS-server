# from transformers import Wav2Vec2Processor
from transformers import Wav2Vec2FeatureExtractor
from transformers import AutoModel
import torch
from torch import nn
import torchaudio
import torchaudio.transforms as T

# loading our model weights
model = AutoModel.from_pretrained("m-a-p/MERT-v1-330M", trust_remote_code=True)
# loading the corresponding preprocessor config
processor = Wav2Vec2FeatureExtractor.from_pretrained("m-a-p/MERT-v1-330M",trust_remote_code=True)
device = "cuda" if torch.cuda.is_available() else "cpu"

model = model.to(device)
model.eval()

# def cosine_similarity(matrix1, matrix2):
#     # 벡터를 L2 norm으로 정규화
#     matrix1_norm = matrix1 / matrix1.norm(dim=1, keepdim=True)
#     matrix2_norm = matrix2 / matrix2.norm(dim=1, keepdim=True)
    
#     # 정규화된 벡터들의 내적을 통해 코사인 유사도 계산
#     similarity = torch.mm(matrix1_norm, matrix2_norm.t())  # Transpose the second matrix
#     return similarity


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
