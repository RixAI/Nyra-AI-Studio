# tools/nyra_imagen_gen.py
# Definitive Version 7.0: Reverted to the simple, stable genai.Client method
# as documented in the project guides. All incorrect ControlNet logic has been removed.

# --- Path Setup ---
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ---

import argparse
from typing import Optional
from enum import Enum
from google import genai
import google.genai.types as genai_types
from tools._helpers import resolve_path_in_workspace
from tools.models import MODELS
from tools import _schema_helper
import config

class AspectRatio(str, Enum):
    RATIO_16_9 = "16:9"; RATIO_9_16 = "9:16"; RATIO_1_1 = "1:1"; RATIO_4_3 = "4:3"; RATIO_3_4 = "3:4"

def generate_image(model_name: str, prompt: str, output_path: str, aspect_ratio: AspectRatio, add_watermark: bool = False, negative_prompt: Optional[str] = None, seed: Optional[int] = None):
    """
    Generates an image from a text prompt using the stable genai.Client.
    """
    print(f"\n[Tool: generate_image] with model '{model_name}'")
    try:
        # DEFINITIVE FIX: Use the simple and correct genai.Client as per the documentation.
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        
        if isinstance(aspect_ratio, Enum):
            ratio_value = aspect_ratio.value
        else:
            ratio_value = str(aspect_ratio)

        config_params = {
            "number_of_images": 1,
            "aspect_ratio": ratio_value,
            "add_watermark": add_watermark,
            "seed": seed,
            "negative_prompt": negative_prompt
        }
        
        # Use a dictionary to filter out None values to keep the call clean
        final_config = {k: v for k, v in config_params.items() if v is not None}

        response = gcp_client.models.generate_images(
            model=model_name,
            prompt=prompt,
            config=genai_types.GenerateImagesConfig(**final_config)
        )
        
        img = response.generated_images[0]
        local_path = resolve_path_in_workspace(output_path)
        img.image.save(str(local_path))
        
        print(f"✅ SUCCESS: Image saved directly to {local_path}")
        return str(local_path)
    except Exception as e:
        print(f"❌ FAILED: generate_image. Error: {e}")
        return None

# --- TOOL REGISTRATION AND CLI ---
# (The 'controlnet_skeleton_path' argument is removed from the tool signature and CLI)
_TOOL_FUNCTIONS = [generate_image]
def get_tool_declarations():
    return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry():
    return {f.__name__: f for f in _TOOL_FUNCTIONS}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Imagen Text-to-Image Generation")
    parser.add_argument("--model_name", required=True, choices=MODELS["imagen_gen"])
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output_path", required=True)
    parser.add_argument("--aspect_ratio", default=AspectRatio.RATIO_16_9, type=AspectRatio, choices=list(AspectRatio))
    parser.add_argument("--add_watermark", action='store_true')
    parser.add_argument("--negative_prompt")
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    generate_image(**vars(args))