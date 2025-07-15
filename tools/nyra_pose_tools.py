# tools/nyra_pose_tools.py
# --- Path Setup for Direct Execution ---
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ---
import argparse
from PIL import Image
from controlnet_aux import OpenposeDetector
from tools._helpers import resolve_path_in_workspace
from tools import _schema_helper

def extract_openpose_skeleton(input_path: str, output_path: str) -> str:
    """
    Analyzes an input image, detects the human pose, and saves the resulting
    OpenPose skeleton as a new image file. This skeleton is used for ControlNet.
    """
    print(f"\n[Tool: extract_openpose_skeleton]")
    try:
        openpose = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
        input_file = resolve_path_in_workspace(input_path)
        output_file = resolve_path_in_workspace(output_path)
        source_image = Image.open(input_file)
        pose_skeleton_image = openpose(source_image)
        pose_skeleton_image.save(str(output_file))
        message = f"Successfully extracted OpenPose skeleton to {output_file}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        error_message = f"Failed to extract pose. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

# --- TOOL REGISTRATION ---
_TOOL_FUNCTIONS = [extract_openpose_skeleton]
def get_tool_declarations():
    return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry():
    return {f.__name__: f for f in _TOOL_FUNCTIONS}

# --- COMMAND-LINE INTERFACE ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="OpenPose Skeleton Extractor")
    parser.add_argument("--input_path", required=True)
    parser.add_argument("--output_path", required=True)
    args = parser.parse_args()
    extract_openpose_skeleton(args.input_path, args.output_path)