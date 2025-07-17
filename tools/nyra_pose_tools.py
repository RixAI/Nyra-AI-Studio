# tools/nyra_pose_tools.py
# Definitive Version 2.0: Adds a new tool to extract a FaceMesh using MediaPipe.

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import cv2
import numpy as np
import mediapipe as mp
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

def extract_facemesh(input_path: str, output_path: str) -> str:
    """
    Analyzes an input image, detects a human face, and saves the resulting
    FaceMesh visualization as a new image file for controlled editing.
    """
    print(f"\n[Tool: extract_facemesh]")
    try:
        mp_face_mesh = mp.solutions.face_mesh
        mp_drawing = mp.solutions.drawing_utils
        drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

        input_file = resolve_path_in_workspace(input_path)
        output_file = resolve_path_in_workspace(output_path)
        
        with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5) as face_mesh:
            image = cv2.imread(str(input_file))
            results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            if not results.multi_face_landmarks:
                raise ValueError("No face found in the input image.")

            annotated_image = np.zeros(image.shape, dtype=np.uint8)
            for face_landmarks in results.multi_face_landmarks:
                # Draw the face mesh connections
                mp_drawing.draw_landmarks(
                    image=annotated_image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=drawing_spec)
            
            cv2.imwrite(str(output_file), annotated_image)
        
        message = f"Successfully extracted FaceMesh to {output_file}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        error_message = f"Failed to extract FaceMesh. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

# --- TOOL REGISTRATION ---
_TOOL_FUNCTIONS = [extract_openpose_skeleton, extract_facemesh]
def get_tool_declarations():
    return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry():
    return {f.__name__: f for f in _TOOL_FUNCTIONS}