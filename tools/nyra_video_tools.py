# tools/nyra_video_tools.py
# A unified, intelligent tool for all Veo 2 and Veo 3 video generation
# and editing tasks.

import os
import sys
import time
from typing import Optional

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from .nyra_core import (
    resolve_path_in_workspace, 
    upload_to_gcs, 
    download_from_gcs, 
    handle_video_operation, 
    MODELS, 
    create_function_declaration
)

# --- Dependency Imports ---
from google import genai
import google.auth
import google.auth.transport.requests
from google.genai.types import GenerateVideosConfig, Image, Video

# ======================================================================
# --- TOOL: VEO 3 GENERATION ---
# ======================================================================
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
    """Generates a video from text or an image using a Veo 3 model."""
    print(f"\n[Tool: generate_veo3_video] with model '{model_name}'")
    try:
        creds, _ = google.auth.load_credentials_from_file(config.SERVICE_ACCOUNT_KEY_PATH, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(google.auth.transport.requests.Request())
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION, credentials=creds)
        
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

# ======================================================================
# --- TOOL: VEO 2 GENERATION ---
# ======================================================================
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
    """Generates a video from text or image using a Veo 2 model."""
    print(f"\n[Tool: generate_veo2_video] with model '{model_name}'")
    try:
        creds, _ = google.auth.load_credentials_from_file(config.SERVICE_ACCOUNT_KEY_PATH, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(google.auth.transport.requests.Request())
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION, credentials=creds)

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

# ======================================================================
# --- TOOLS: VEO 2 EDITING ---
# ======================================================================
def extend_video(model_name: str, input_path: str, output_path: str, prompt: Optional[str] = None) -> str:
    """Extends a video clip by a few seconds using a Veo 2 model."""
    print(f"\n[Tool: extend_video] with model '{model_name}'")
    try:
        creds, _ = google.auth.load_credentials_from_file(config.SERVICE_ACCOUNT_KEY_PATH, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(google.auth.transport.requests.Request())
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION, credentials=creds)

        gcs_uri = upload_to_gcs(resolve_path_in_workspace(input_path), "extend-inputs")
        output_gcs_prefix = f"video_outputs/{model_name}_extend/{int(time.time())}"
        output_gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{output_gcs_prefix}/"
        
        config_params = {"duration_seconds": 5, "output_gcs_uri": output_gcs_uri}
        
        operation = gcp_client.models.generate_videos(
            model=model_name,
            prompt=prompt or "",
            video=Video(uri=gcs_uri),
            config=GenerateVideosConfig(**config_params)
        )
        final_gcs_uri = handle_video_operation(operation)
        return download_from_gcs(final_gcs_uri, output_path)
    except Exception as e:
        print(f"❌ FAILED: extend_video. Error: {e}")
        return str(e)

def inpaint_video(model_name: str, input_path: str, mask_path: str, output_path: str, prompt: str) -> str:
    """Inpaints a region of a video as defined by a mask video using a Veo 2 model."""
    print(f"\n[Tool: inpaint_video] with model '{model_name}'")
    try:
        creds, _ = google.auth.load_credentials_from_file(config.SERVICE_ACCOUNT_KEY_PATH, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(google.auth.transport.requests.Request())
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION, credentials=creds)
        
        input_uri = upload_to_gcs(resolve_path_in_workspace(input_path), "inpaint-inputs")
        mask_uri = upload_to_gcs(resolve_path_in_workspace(mask_path), "inpaint-masks")
        output_gcs_prefix = f"video_outputs/{model_name}_inpaint/{int(time.time())}"
        output_gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{output_gcs_prefix}/"

        config_params = {"mode": "INPAINT", "output_gcs_uri": output_gcs_uri}

        operation = gcp_client.models.generate_videos(
            model=model_name,
            prompt=prompt,
            video=Video(uri=input_uri),
            mask=Video(uri=mask_uri),
            config=GenerateVideosConfig(**config_params)
        )
        final_gcs_uri = handle_video_operation(operation)
        return download_from_gcs(final_gcs_uri, output_path)
    except Exception as e:
        print(f"❌ FAILED: inpaint_video. Error: {e}")
        return str(e)

# ======================================================================
# --- TOOL REGISTRATION ---
# ======================================================================
_TOOL_FUNCTIONS = [
    generate_veo3_video,
    generate_veo2_video,
    extend_video,
    inpaint_video
]
def get_tool_declarations(): return [create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry(): return {f.__name__: f for f in _TOOL_FUNCTIONS}
# End of file: tools/nyra_video_tools.py