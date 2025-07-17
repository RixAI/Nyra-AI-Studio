# tools/nyra_veo3_gen.py
# Definitive Version 3.0: Adds explicit credential scoping to fix auth issues.
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
from . import _schema_helper

def generate_veo3_video(
    model_name: str,
    output_path: str,
    prompt: Optional[str] = None,
    image_path: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    duration_seconds: Optional[int] = 8,
    aspect_ratio: Optional[str] = "16:9",
    generate_audio: Optional[bool] = True,
    seed: Optional[int] = None,
    enhance_prompt: Optional[bool] = True,
    person_generation: Optional[str] = "allow_adult"
) -> str:
    """Generates a video from text or an image using a Veo 3 model with explicit, scoped credentials."""
    print(f"\n[Tool: generate_veo3_video] with model '{model_name}'")
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
        
        if duration_seconds != 8:
            print(f"-> WARNING: Model {model_name} requires an 8-second duration. Overriding value.")
            duration_seconds = 8

        output_gcs_prefix = f"video_outputs/{model_name}/{int(time.time())}"
        output_gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{output_gcs_prefix}/"
        
        config_params = {"output_gcs_uri": output_gcs_uri, "duration_seconds": duration_seconds}
        if negative_prompt: config_params["negative_prompt"] = negative_prompt
        if aspect_ratio: config_params["aspect_ratio"] = aspect_ratio
        if generate_audio is not None: config_params["generate_audio"] = generate_audio
        if seed: config_params["seed"] = seed
        if enhance_prompt is not None: config_params["enhance_prompt"] = enhance_prompt
        if "fast" in model_name: config_params["person_generation"] = person_generation

        api_kwargs = {"model": model_name, "config": GenerateVideosConfig(**config_params)}
        if prompt: api_kwargs["prompt"] = prompt
        if image_path:
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(image_path), "i2v-inputs")
            api_kwargs["image"] = Image(gcs_uri=gcs_uri, mime_type="image/png")

        operation = gcp_client.models.generate_videos(**api_kwargs)
        gcs_uri = handle_video_operation(operation)
        return download_from_gcs(gcs_uri, output_path)
    except Exception as e: 
        return f"❌ FAILED: Veo 3 generation. Error: {e}"

_TOOL_FUNCTIONS = [generate_veo3_video]
def get_tool_declarations():
    return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry():
    return {f.__name__: f for f in _TOOL_FUNCTIONS}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Veo 3 Video Generation with Full Controls")
    veo3_models = [m for m in MODELS["veo"] if "veo-3.0" in m]
    parser.add_argument("--model_name", required=True, choices=veo3_models)
    parser.add_argument("--output_path", required=True)
    parser.add_argument("--prompt"); parser.add_argument("--image_path"); parser.add_argument("--negative_prompt")
    parser.add_argument("--duration_seconds", type=int, default=8)
    parser.add_argument("--aspect_ratio", choices=["16:9"], default="16:9")
    parser.add_argument("--generate_audio", type=bool, default=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--enhance_prompt", type=bool, default=True)
    parser.add_argument("--person_generation", choices=["allow_adult", "disallow"], default="allow_adult")
    args = parser.parse_args()
    if not args.prompt and not args.image_path: parser.error("Either --prompt or --image_path is required.")
    generate_veo3_video(**vars(args))