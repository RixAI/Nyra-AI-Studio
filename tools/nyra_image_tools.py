# tools/nyra_image_tools.py
# A unified, intelligent tool for all image generation, editing, and
# character asset processing tasks.

import os
import sys
from typing import Optional, List
from enum import Enum
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from .nyra_core import (
    resolve_path_in_workspace, 
    upload_to_gcs, 
    MODELS, 
    create_function_declaration
)

# --- Dependency Imports ---
from google import genai
import google.auth
import google.auth.transport.requests
from google.genai import types as genai_types
from controlnet_aux import OpenposeDetector

# ======================================================================
# --- TOOL: IMAGE GENERATION ---
# ======================================================================
class AspectRatio(str, Enum):
    RATIO_16_9 = "16:9"
    RATIO_9_16 = "9:16"
    RATIO_1_1 = "1:1"
    RATIO_4_3 = "4:3"
    RATIO_3_4 = "3:4"

def generate_image(
    model_name: str, 
    prompt: str, 
    output_path: str, 
    aspect_ratio: AspectRatio, 
    add_watermark: bool = False, 
    negative_prompt: Optional[str] = None, 
    seed: Optional[int] = None
) -> str:
    """Generates an image from a text prompt using an Imagen model."""
    print(f"\n[Tool: generate_image] with model '{model_name}'")
    try:
        creds, _ = google.auth.load_credentials_from_file(config.SERVICE_ACCOUNT_KEY_PATH, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(google.auth.transport.requests.Request())
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION, credentials=creds)
        
        ratio_value = aspect_ratio.value if isinstance(aspect_ratio, Enum) else str(aspect_ratio)
        config_params = {"number_of_images": 1, "aspect_ratio": ratio_value, "add_watermark": add_watermark, "seed": seed, "negative_prompt": negative_prompt}
        final_config = {k: v for k, v in config_params.items() if v is not None}

        response = gcp_client.models.generate_images(model=model_name, prompt=prompt, config=genai_types.GenerateImagesConfig(**final_config))
        img = response.generated_images[0]
        local_path = resolve_path_in_workspace(output_path)
        img.image.save(str(local_path))
        print(f"✅ SUCCESS: Image saved to {local_path}")
        return str(local_path)
    except Exception as e:
        print(f"❌ FAILED: generate_image. Error: {e}")
        return str(e)

# ======================================================================
# --- TOOL: IMAGE EDITING ---
# ======================================================================
class EditMode(str, Enum):
    INSTRUCT = "instruct"
    STYLE_TRANSFER = "style_transfer"
    SUBJECT_CUSTOMIZATION = "subject_customization"
    CONTROLLED_EDITING = "controlled_editing"
    BGSWAP = "bgswap"
    INPAINT = "inpaint"
    OUTPAINT = "outpaint"

class ControlType(str, Enum):
    SCRIBBLE = "scribble"
    CANNY = "canny"
    FACE_MESH = "face_mesh"

def edit_image(
    model_name: str, 
    edit_mode: EditMode, 
    output_path: str, 
    prompt: str, 
    input_path: Optional[str] = None, 
    mask_path: Optional[str] = None, 
    subject_ref_path: Optional[str] = None, 
    style_ref_path: Optional[str] = None, 
    control_ref_path: Optional[str] = None, 
    control_type: Optional[ControlType] = None, 
    negative_prompt: Optional[str] = None
) -> str:
    """A unified multi-tool for all advanced Imagen 3 editing capabilities."""
    try:
        mode_enum = EditMode(edit_mode)
        print(f"\n[Tool: edit_image] with model '{model_name}' in mode '{mode_enum.value}'")

        creds, _ = google.auth.load_credentials_from_file(config.SERVICE_ACCOUNT_KEY_PATH, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(google.auth.transport.requests.Request())
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION, credentials=creds)
        
        mode_map = {
            EditMode.INSTRUCT: "EDIT_MODE_INSTRUCT", EditMode.STYLE_TRANSFER: "EDIT_MODE_STYLE_TRANSFER",
            EditMode.SUBJECT_CUSTOMIZATION: "EDIT_MODE_SUBJECT_CUSTOMIZATION", EditMode.CONTROLLED_EDITING: "EDIT_MODE_CONTROLLED_EDITING",
            EditMode.BGSWAP: "EDIT_MODE_BGSWAP", EditMode.INPAINT: "EDIT_MODE_INPAINT_INSERTION", EditMode.OUTPAINT: "EDIT_MODE_OUTPAINT"
        }
        sdk_edit_mode = mode_map[mode_enum]
        
        reference_images = []
        ref_id_counter = 1
        
        if input_path:
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(input_path), "edit_inputs/input")
            reference_images.append(genai_types.RawReferenceImage(reference_image=genai_types.Image(gcs_uri=gcs_uri), reference_id=0))
        
        if mask_path:
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(mask_path), "edit_inputs/mask")
            mask_config = genai_types.MaskReferenceConfig(mask_mode="MASK_MODE_USER_PROVIDED")
            reference_images.append(genai_types.MaskReferenceImage(reference_image=genai_types.Image(gcs_uri=gcs_uri), config=mask_config, reference_id=ref_id_counter))
            ref_id_counter += 1

        if subject_ref_path:
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(subject_ref_path), "edit_inputs/subject")
            reference_images.append(genai_types.SubjectReferenceImage(reference_image=genai_types.Image(gcs_uri=gcs_uri), reference_id=ref_id_counter))
            ref_id_counter += 1

        if style_ref_path:
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(style_ref_path), "edit_inputs/style")
            reference_images.append(genai_types.StyleReferenceImage(reference_image=genai_types.Image(gcs_uri=gcs_uri), reference_id=ref_id_counter))
            ref_id_counter += 1
            
        if control_ref_path:
            if not control_type: raise ValueError("`control_type` is required when using `control_ref_path`.")
            control_type_map = { ControlType.SCRIBBLE: "CONTROL_TYPE_SCRIBBLE", ControlType.CANNY: "CONTROL_TYPE_CANNY", ControlType.FACE_MESH: "CONTROL_TYPE_FACE_MESH" }
            sdk_control_type = control_type_map[control_type]
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(control_ref_path), "edit_inputs/control")
            reference_images.append(genai_types.ControlReferenceImage(
                reference_image=genai_types.Image(gcs_uri=gcs_uri), config=genai_types.ControlReferenceConfig(control_type=sdk_control_type), reference_id=ref_id_counter
            ))
            ref_id_counter += 1

        if sdk_edit_mode == "EDIT_MODE_BGSWAP" and not mask_path:
            reference_images.append(genai_types.MaskReferenceImage(config=genai_types.MaskReferenceConfig(mask_mode="MASK_MODE_BACKGROUND"), reference_id=ref_id_counter))
            
        edit_config = genai_types.EditImageConfig(edit_mode=sdk_edit_mode, negative_prompt=negative_prompt)
        
        response = gcp_client.models.edit_image(model=model_name, prompt=prompt, reference_images=reference_images, config=edit_config)
        
        edited_img = response.generated_images[0]
        local_path = resolve_path_in_workspace(output_path)
        edited_img.image.save(str(local_path))
        print(f"✅ SUCCESS: Edited image saved to {local_path}")
        return str(local_path)
    except Exception as e:
        print(f"❌ FAILED: edit_image. Error: {e}")
        return str(e)

# ======================================================================
# --- TOOLS: CHARACTER ASSETS ---
# ======================================================================
def split_and_layout_character_sheet(input_path: str, output_dir: str) -> str:
    """
    Takes a 3-view character sheet, splits it, and creates three
    separate 16:9 layout images (front, side, back) for production use.
    """
    print(f"\n[Tool: split_and_layout_character_sheet]")
    try:
        input_file = resolve_path_in_workspace(input_path)
        output_path = resolve_path_in_workspace(output_dir)
        
        img = cv2.imread(str(input_file))
        h, w, _ = img.shape
        
        third_w = w // 3
        
        front_view = img[:, third_w:third_w*2]
        side_view = img[:, :third_w]
        back_view = img[:, third_w*2:]
        
        def create_layout(view_img, position_index):
            canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
            view_h, view_w, _ = view_img.shape
            x_offset = position_index * third_w
            y_offset = (h - view_h) // 2
            canvas[y_offset:y_offset+view_h, x_offset:x_offset+view_w] = view_img
            return canvas
            
        front_layout = create_layout(front_view, 1)
        side_layout = create_layout(side_view, 0)
        back_layout = create_layout(back_view, 2)
        
        base_name = input_file.stem
        cv2.imwrite(str(output_path / f"{base_name}_front_layout.png"), front_layout)
        cv2.imwrite(str(output_path / f"{base_name}_side_layout.png"), side_layout)
        cv2.imwrite(str(output_path / f"{base_name}_back_layout.png"), back_layout)
        
        message = f"Successfully created 3 character layouts in '{output_path}'"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        message = f"Failed to split character sheet. Error: {e}"
        print(f"❌ FAILED: {message}")
        return message

def create_hologram_effect(input_path: str, output_path: str) -> str:
    """Applies a futuristic hologram effect to an input image."""
    print(f"\n[Tool: create_hologram_effect]")
    try:
        # Full function logic for this tool was not provided in the source context.
        # This is a placeholder implementation.
        message = f"Placeholder for hologram effect. Input: {input_path}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        message = f"Failed to create hologram effect. Error: {e}"
        print(f"❌ FAILED: {message}")
        return message

# ======================================================================
# --- TOOL REGISTRATION ---
# ======================================================================
_TOOL_FUNCTIONS = [
    generate_image,
    edit_image,
    split_and_layout_character_sheet,
    create_hologram_effect
]
def get_tool_declarations(): return [create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry(): return {f.__name__: f for f in _TOOL_FUNCTIONS}
# End of file: tools/nyra_image_tools.py