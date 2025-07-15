# tools/nyra_veo2_edit.py
import argparse
import time
from typing import Optional
from google import genai
from google.genai.types import GenerateVideosConfig, Video
from ._helpers import download_from_gcs, handle_video_operation, upload_to_gcs, resolve_path_in_workspace
from .models import MODELS
import config

def extend_video(model_name: str, input_path: str, output_path: str, prompt: Optional[str] = None) -> str:
    """Extends a video clip by a few seconds."""
    print(f"\n[Tool: extend_video] with model '{model_name}'")
    try:
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        gcs_uri = upload_to_gcs(resolve_path_in_workspace(input_path), "extend-inputs")
        output_gcs_prefix = f"video_outputs/{model_name}_extend/{int(time.time())}"
        output_gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{output_gcs_prefix}/"
        
        config_params = {"duration_seconds": 4, "output_gcs_uri": output_gcs_uri}
        
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
        return None

def inpaint_video(model_name: str, input_path: str, mask_path: str, output_path: str, prompt: str) -> str:
    """Inpaints a region of a video as defined by a mask video."""
    print(f"\n[Tool: inpaint_video] with model '{model_name}'")
    try:
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        input_uri = upload_to_gcs(resolve_path_in_workspace(input_path), "inpaint-inputs")
        mask_uri = upload_to_gcs(resolve_path_in_workspace(mask_path), "inpaint-masks")
        output_gcs_prefix = f"video_outputs/{model_name}_inpaint/{int(time.time())}"
        output_gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{output_gcs_prefix}/"

        config_params = {"mode": "INPAINT", "output_gcs_uri": output_gcs_uri}

        operation = gcp_client.models.generate_videos(
            model=model_name,
            prompt=prompt,
            video=Video(gcs_uri=input_uri),
            mask=Video(gcs_uri=mask_uri),
            config=GenerateVideosConfig(**config_params)
        )
        final_gcs_uri = handle_video_operation(operation)
        return download_from_gcs(final_gcs_uri, output_path)
    except Exception as e:
        print(f"❌ FAILED: inpaint_video. Error: {e}")
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Veo 2 Video Editing Tools")
    subparsers = parser.add_subparsers(dest="command", required=True)
    veo2_models = [m for m in MODELS["veo"] if "veo-2.0" in m]
    
    # Extend Video Parser
    p_extend = subparsers.add_parser("extend", help="Extend a video.")
    p_extend.add_argument("--model_name", default=veo2_models[0], choices=veo2_models)
    p_extend.add_argument("--input_path", required=True)
    p_extend.add_argument("--output_path", required=True)
    p_extend.add_argument("--prompt")
    p_extend.set_defaults(func=lambda args: extend_video(**vars(args)))

    # Inpaint Video Parser
    p_inpaint = subparsers.add_parser("inpaint", help="Inpaint a video.")
    p_inpaint.add_argument("--model_name", default=veo2_models[0], choices=veo2_models)
    p_inpaint.add_argument("--input_path", required=True)
    p_inpaint.add_argument("--mask_path", required=True)
    p_inpaint.add_argument("--output_path", required=True)
    p_inpaint.add_argument("--prompt", required=True)
    p_inpaint.set_defaults(func=lambda args: inpaint_video(**vars(args)))

    args = parser.parse_args()
    kwargs = {k: v for k, v in vars(args).items() if k not in ['func', 'command']}
    args.func(argparse.Namespace(**kwargs))