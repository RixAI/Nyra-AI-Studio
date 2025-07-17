# tools/nyra_imagen_edit.py
# Definitive Version 7.0: The final, correct version. Fixes the 400 error
# for inpainting by adding the required MaskReferenceConfig. The logic is now
# fully compliant with the official API documentation.

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from typing import Optional
from enum import Enum
from google import genai
import google.auth
import google.auth.transport.requests
from google.genai.types import (Image, RawReferenceImage, MaskReferenceImage, MaskReferenceConfig, EditImageConfig, StyleReferenceImage, StyleReferenceConfig, SubjectReferenceImage, SubjectReferenceConfig, ControlReferenceImage, ControlReferenceConfig)
from tools._helpers import resolve_path_in_workspace, upload_to_gcs
from tools.models import MODELS
from tools import _schema_helper
import config

class EditMode(str, Enum):
    INSTRUCT = "instruct"; STYLE_TRANSFER = "style_transfer"; SUBJECT_CUSTOMIZATION = "subject_customization"; CONTROLLED_EDITING = "controlled_editing"; BGSWAP = "bgswap"; INPAINT = "inpaint"; OUTPAINT = "outpaint"

class ControlType(str, Enum):
    SCRIBBLE = "scribble"; CANNY = "canny"; FACE_MESH = "face_mesh"

def edit_image(model_name: str, edit_mode: EditMode, output_path: str, prompt: str, input_path: Optional[str] = None, mask_path: Optional[str] = None, subject_ref_path: Optional[str] = None, style_ref_path: Optional[str] = None, control_ref_path: Optional[str] = None, control_type: Optional[ControlType] = None, negative_prompt: Optional[str] = None) -> str:
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
            reference_images.append(RawReferenceImage(reference_image=Image(gcs_uri=gcs_uri), reference_id=0))
        
        # DEFINITIVE FIX: Logic for mask handling is now corrected.
        if mask_path:
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(mask_path), "edit_inputs/mask")
            # For inpainting/outpainting, the mask needs a specific configuration.
            mask_config = MaskReferenceConfig(mask_mode="MASK_MODE_USER_PROVIDED")
            reference_images.append(MaskReferenceImage(reference_image=Image(gcs_uri=gcs_uri), config=mask_config, reference_id=ref_id_counter))
            ref_id_counter += 1

        if subject_ref_path:
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(subject_ref_path), "edit_inputs/subject")
            reference_images.append(SubjectReferenceImage(reference_image=Image(gcs_uri=gcs_uri), reference_id=ref_id_counter))
            ref_id_counter += 1

        if style_ref_path:
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(style_ref_path), "edit_inputs/style")
            reference_images.append(StyleReferenceImage(reference_image=Image(gcs_uri=gcs_uri), reference_id=ref_id_counter))
            ref_id_counter += 1
            
        if control_ref_path:
            if not control_type: raise ValueError("`control_type` is required when using `control_ref_path`.")
            control_type_map = {
                ControlType.SCRIBBLE: "CONTROL_TYPE_SCRIBBLE", ControlType.CANNY: "CONTROL_TYPE_CANNY", ControlType.FACE_MESH: "CONTROL_TYPE_FACE_MESH"
            }
            sdk_control_type = control_type_map[control_type]
            gcs_uri = upload_to_gcs(resolve_path_in_workspace(control_ref_path), "edit_inputs/control")
            reference_images.append(ControlReferenceImage(
                reference_image=Image(gcs_uri=gcs_uri), config=ControlReferenceConfig(control_type=sdk_control_type), reference_id=ref_id_counter
            ))
            ref_id_counter += 1

        if sdk_edit_mode == "EDIT_MODE_BGSWAP" and not mask_path:
            # If BGSWAP is used without a user mask, add the auto-background mask config
            reference_images.append(MaskReferenceImage(config=MaskReferenceConfig(mask_mode="MASK_MODE_BACKGROUND"), reference_id=ref_id_counter))
            
        edit_config = EditImageConfig(edit_mode=sdk_edit_mode, negative_prompt=negative_prompt)
        
        response = gcp_client.models.edit_image(model=model_name, prompt=prompt, reference_images=reference_images, config=edit_config)
        
        edited_img = response.generated_images[0]
        local_path = resolve_path_in_workspace(output_path)
        edited_img.image.save(str(local_path))
        print(f"✅ SUCCESS: Edited image saved to {local_path}")
        return str(local_path)
    except Exception as e:
        print(f"❌ FAILED: edit_image. Error: {e}")
        return str(e)

# --- Tool Registration & CLI ---
_TOOL_FUNCTIONS = [edit_image]
def get_tool_declarations(): return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry(): return {f.__name__: f for f in _TOOL_FUNCTIONS}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Imagen 3 Unified Image Editing Tool")
    parser.add_argument("--model_name", required=True, choices=MODELS["imagen_edit"])
    parser.add_argument("--mode", required=True, type=EditMode, choices=list(EditMode))
    parser.add_argument("--output_path", required=True); parser.add_argument("--prompt", default="")
    parser.add_argument("--input_path"); parser.add_argument("--mask_path"); parser.add_argument("--subject_ref_path")
    parser.add_argument("--style_ref_path"); parser.add_argument("--control_ref_path")
    parser.add_argument("--control_type", type=ControlType, choices=list(ControlType))
    parser.add_argument("--negative_prompt")
    args = parser.parse_args()
    edit_image(**vars(args))