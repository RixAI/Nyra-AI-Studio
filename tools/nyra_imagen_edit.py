# tools/nyra_imagen_edit.py
# Definitive Version 2.0: Upgraded to the self-registering module standard.
# --- Path Setup for Direct Execution ---
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ---
import argparse
from typing import Optional
from enum import Enum
from google import genai
from google.genai.types import (Image, RawReferenceImage, MaskReferenceImage, MaskReferenceConfig, EditImageConfig, StyleReferenceImage, StyleReferenceConfig, SubjectReferenceImage, SubjectReferenceConfig, ControlReferenceImage, ControlReferenceConfig)
from tools._helpers import resolve_path_in_workspace, upload_to_gcs
from tools.models import MODELS
from tools import _schema_helper
import config
class EditMode(str, Enum):
    SUBJECT = "subject"; STYLE = "style"; SCRIBBLE = "scribble"; BGSWAP = "bgswap"; INPAINT = "inpaint"

def edit_image(edit_mode: EditMode, output_path: str, prompt: str = "", negative_prompt: Optional[str] = None, input_path: Optional[str] = None, style_ref_path: Optional[str] = None, subject_ref_path: Optional[str] = None, scribble_ref_path: Optional[str] = None, mask_path: Optional[str] = None) -> str:
    """A unified multi-tool for advanced image editing, with enforced modes."""
    try:
        mode_enum = EditMode(edit_mode)
        print(f"\n[Tool: edit_image] with mode '{mode_enum.value}'")
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        mode_map = {
            EditMode.SUBJECT: "EDIT_MODE_DEFAULT", EditMode.STYLE: "EDIT_MODE_DEFAULT",
            EditMode.SCRIBBLE: "EDIT_MODE_CONTROLLED_EDITING", EditMode.BGSWAP: "EDIT_MODE_BGSWAP",
            EditMode.INPAINT: "EDIT_MODE_INPAINT_INSERTION"
        }
        sdk_edit_mode = mode_map[mode_enum]
        reference_images = []
        path_map = {"input": input_path, "style": style_ref_path, "subject": subject_ref_path, "scribble": scribble_ref_path, "mask": mask_path}
        for ref_type, path in path_map.items():
            if path:
                resolved_path = resolve_path_in_workspace(path)
                if not os.path.exists(resolved_path): raise FileNotFoundError(f"Prerequisite file not found: {path}")
                gcs_uri = upload_to_gcs(resolved_path, f"edit_inputs/{ref_type}")
                image_obj = Image(gcs_uri=gcs_uri)
                if ref_type == "input": reference_images.append(RawReferenceImage(reference_image=image_obj, reference_id=0))
                elif ref_type == "style": reference_images.append(StyleReferenceImage(reference_image=image_obj, reference_id=1, config=StyleReferenceConfig(style_description="the provided style")))
                elif ref_type == "subject": reference_images.append(SubjectReferenceImage(reference_image=image_obj, reference_id=1, config=SubjectReferenceConfig(subject_type="SUBJECT_TYPE_PERSON")))
                elif ref_type == "scribble": reference_images.append(ControlReferenceImage(reference_image=image_obj, config=ControlReferenceConfig(control_type="CONTROL_TYPE_SCRIBBLE"), reference_id=2))
                elif ref_type == "mask": reference_images.append(MaskReferenceImage(reference_image=image_obj, reference_id=1))
        if sdk_edit_mode == "EDIT_MODE_BGSWAP":
            reference_images.append(MaskReferenceImage(config=MaskReferenceConfig(mask_mode="MASK_MODE_BACKGROUND"), reference_id=1))
        edit_config = EditImageConfig(edit_mode=sdk_edit_mode, negative_prompt=negative_prompt)
        response = gcp_client.models.edit_image(model=MODELS["imagen_edit"][0], prompt=prompt, reference_images=reference_images, config=edit_config)
        edited_img = response.generated_images[0]
        local_path = resolve_path_in_workspace(output_path)
        edited_img.image.save(str(local_path))
        print(f"✅ SUCCESS: Edited image saved to {local_path}")
        return str(local_path)
    except Exception as e:
        print(f"❌ FAILED: edit_image. Error: {e}")
        return str(e)

# --- TOOL REGISTRATION ---
_TOOL_FUNCTIONS = [edit_image]
def get_tool_declarations():
    return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry():
    return {f.__name__: f for f in _TOOL_FUNCTIONS}

# --- COMMAND-LINE INTERFACE ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Imagen Unified Image Editing Tool")
    parser.add_argument("--mode", required=True, type=EditMode, choices=list(EditMode))
    parser.add_argument("--output_path", required=True); parser.add_argument("--prompt", default=""); parser.add_argument("--input_path")
    parser.add_argument("--style_ref_path"); parser.add_argument("--subject_ref_path"); parser.add_argument("--scribble_ref_path")
    parser.add_argument("--mask_path"); parser.add_argument("--negative_prompt")
    args = parser.parse_args()
    edit_image(**vars(args))