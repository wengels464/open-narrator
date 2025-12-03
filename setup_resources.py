import os
import requests
import json

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_PATH, 'assets', 'models')
VOICES_DIR = os.path.join(BASE_PATH, 'assets', 'voices')

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

def download_file(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded {dest_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(VOICES_DIR, exist_ok=True)

    if not os.path.exists(os.path.join(MODELS_DIR, 'kokoro-v1.0.onnx')):
        download_file(MODEL_URL, os.path.join(MODELS_DIR, 'kokoro-v1.0.onnx'))
    else:
        print("Model already exists.")

    if not os.path.exists(os.path.join(VOICES_DIR, 'voices-v1.0.bin')):
        download_file(VOICES_URL, os.path.join(VOICES_DIR, 'voices-v1.0.bin'))
    else:
        print("Voices file already exists.")

if __name__ == "__main__":
    main()
