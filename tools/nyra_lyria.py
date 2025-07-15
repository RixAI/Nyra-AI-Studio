# tools/nyra_lyria.py
import argparse
import base64
import requests
import time
import google.auth
import google.auth.transport.requests
from ._helpers import resolve_path_in_workspace
from .models import MODELS
import config

def generate_music(prompt: str, output_path: str, duration_seconds: int = 20):
    """Generates music via a direct REST call."""
    print(f"\n[Tool: generate_music]")
    try:
        creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(google.auth.transport.requests.Request())
        
        api_endpoint = f"https://{config.LOCATION}-aiplatform.googleapis.com/v1/projects/{config.PROJECT_ID}/locations/{config.LOCATION}/publishers/google/models/{MODELS['lyria'][0]}:predict"
        headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
        
        payload = {
            "instances": [{"prompt": f"{prompt}, instrumental", "duration_seconds": duration_seconds, "seed": int(time.time())}],
            "parameters": {"sample_count": 1}
        }
        
        print(f" -> Sending REST request to Lyria API for prompt: '{prompt}'")
        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        response_data = response.json()
        if 'predictions' not in response_data or not response_data['predictions']:
            raise ValueError("API response did not contain predictions.")

        b64_content = response_data['predictions'][0]['bytesBase64Encoded']
        audio_bytes = base64.b64decode(b64_content)
        
        local_path = resolve_path_in_workspace(output_path)
        local_path.write_bytes(audio_bytes)

        print(f"✅ SUCCESS: Music saved to {local_path}")
        return str(local_path)
    except Exception as e:
        print(f"❌ FAILED: generate_music. Error: {e}")
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Lyria Music Generation")
    parser.add_argument("--prompt", required=True, help="Text prompt for music generation.")
    parser.add_argument("--output_path", required=True, help="Local path to save the MP3 file.")
    parser.add_argument("--duration", type=int, default=20, help="Duration of the music in seconds.")
    args = parser.parse_args()
    generate_music(args.prompt, args.output_path, args.duration)