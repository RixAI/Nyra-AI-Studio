# tools/nyra_veo2_gen.py
# DEFINITIVE FINAL VERSION v2: Adds explicit credential scoping to fix auth issues.

import argparse
import time
from typing import Optional
from google import genai
import google.auth
import google.auth.transport.requests # <-- REQUIRED FOR THE FIX
from google.genai.types import GenerateVideosConfig, Image
from ._helpers import download_from_gcs, handle_video_operation, upload_to_gcs, resolve_path_in_workspace
from .models import MODELS
import config

def generate_veo2_video(
    model_name: str,
    output_path: str,
    prompt: Optional[str] = None,
    image_path: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    duration_seconds: Optional[int] = 5,
    aspect_ratio: Optional[str] = "16:9",
    person_generation: Optional[str] = "allow_adult",
    number_of_videos: Optional[int] = 1,
    enhance_prompt: Optional[bool] = True
) -> str:
    """Generates a video from text or image using a Veo 2 model with explicit, scoped credentials."""
    print(f"\n[Tool: generate_veo2_video] with model '{model_name}'")
    try:
        # --- START OF THE DEFINITIVE FIX ---
        creds, _ = google.auth.load_credentials_from_file(
            config.SERVICE_ACCOUNT_KEY_PATH,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        creds.refresh(google.auth.transport.requests.Request())

        gcp_client = genai.Client(
            vertexai=True,
            project=config.PROJECT_ID,
            location=config.LOCATION,
            credentials=creds
        )
        # --- END OF THE DEFINITIVE FIX ---

        output_gcs_prefix = f"video_outputs/{model_name}/{int(time.time())}"
        output_gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{output_gcs_prefix}/"
        
        config_params = {
            "output_gcs_uri": output_gcs_uri, "generate_audio": False, "duration_seconds": duration_seconds,
            "aspect_ratio": aspect_ratio, "person_generation": person_generation,
            "number_of_videos": number_of_videos, "enhance_prompt": enhance_prompt,
            "negative_prompt": negative_prompt
        }
        
        api_kwargs = {"model": model_name, "config": GenerateVideosConfig(**config_params)}
        if prompt: api_kwargs["prompt"] = prompt
        if image_path:
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(image_path), "i2v-inputs")
            api_kwargs["image"] = Image(gcs_uri=gcs_uri, mime_type="image/png")
            
        operation = gcp_client.models.generate_videos(**api_kwargs)
        gcs_uri = handle_video_operation(operation)
        return download_from_gcs(gcs_uri, output_path)
    except Exception as e:
        print(f"❌ FAILED: Veo 2 generation. Error: {e}")
        return str(e)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Veo 2 Video Generation with Full Controls")
    parser.add_argument("--model_name", required=True, choices=[m for m in MODELS["veo"] if "veo-2.0" in m])
    parser.add_argument("--output_path", required=True)
    parser.add_argument("--prompt"); parser.add_argument("--image_path")
    parser.add_argument("--negative_prompt")
    parser.add_argument("--duration_seconds", type=int, default=5, choices=range(5, 9))
    parser.add_argument("--aspect_ratio", default="16:9", choices=["16:9", "9:16"])
    parser.add_argument("--person_generation", default="allow_adult", choices=["dont_allow", "allow_adult", "allow_all"])
    parser.add_argument("--number_of_videos", type=int, default=1, choices=[1, 2])
    parser.add_argument("--enhance_prompt", type=bool, default=True)
    
    args = parser.parse_args()
    if not args.prompt and not args.image_path: parser.error("Either --prompt or --image_path is required.")
    generate_veo2_video(**vars(args))