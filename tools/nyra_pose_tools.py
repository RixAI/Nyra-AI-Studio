# tools/nyra_pose_tools.py
# A unified tool for pose and facial mesh extraction.

import os
import sys
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .nyra_core import resolve_path_in_workspace, create_function_declaration

# --- Dependency Imports ---
from controlnet_aux import OpenposeDetector

def extract_openpose_skeleton(input_path: str, output_path: str) -> str:
    """
    Analyzes an input image, detects human pose, and saves the OpenPose skeleton.
    """
    print(f"\n[Tool: extract_openpose_skeleton]")
    try:
        openpose = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
        source_image = Image.open(resolve_path_in_workspace(input_path))
        pose_skeleton_image = openpose(source_image)
        output_file = resolve_path_in_workspace(output_path)
        pose_skeleton_image.save(str(output_file))
        message = f"Successfully extracted OpenPose skeleton to {output_file}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        error_message = f"Failed to extract pose. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

def extract_facemesh(input_path: str, output_path: str) -> str:
    """
    Analyzes an input image, detects a human face, and saves the FaceMesh.
    """
    print(f"\n[Tool: extract_facemesh]")
    try:
        # Full function logic from the original, working file goes here.
        pass
    except Exception as e:
        error_message = f"Failed to extract FaceMesh. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

# --- Tool Registration ---
_TOOL_FUNCTIONS = [extract_openpose_skeleton, extract_facemesh]
def get_tool_declarations(): return [create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry(): return {f.__name__: f for f in _TOOL_FUNCTIONS}