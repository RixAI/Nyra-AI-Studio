# tools/nyra_character_tools.py
# Definitive Version 11.0: Corrects a ValueError in split_and_layout_character_sheet
# by ensuring the destination slice on the canvas matches the source image dimensions.

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import numpy as np
from pathlib import Path
from typing import List
import mediapipe as mp
from tools._helpers import resolve_path_in_workspace
from tools import _schema_helper
from tools.nyra_imagen_gen import generate_image, AspectRatio
import config

def split_and_layout_character_sheet(input_path: str, output_dir: str) -> List[str]:
    """
    Takes a single 3-view character sheet image, intelligently segments each view, and saves each one.
    """
    print(f"\n[Tool: split_and_layout_character_sheet] (True AI Vision Segmentation)")
    try:
        input_file = resolve_path_in_workspace(input_path)
        output_directory = resolve_path_in_workspace(output_dir)
        image = cv2.imread(str(input_file))
        if image is None: raise ValueError(f"Could not read image from '{input_file}'")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)
        kernel = np.ones((5,5), np.uint8)
        cleaned_mask = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=5)
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) < 1: raise ValueError("No character contours found on the sheet.")
        
        # Filter out very small noise contours
        min_area = (image.shape[0] * image.shape[1]) * 0.01 # Contour must be at least 1% of image area
        large_contours = [c for c in contours if cv2.contourArea(c) > min_area]
        if not large_contours: raise ValueError(f"Could not find any contours large enough to be a character.")
            
        sorted_contours = sorted(large_contours, key=lambda c: cv2.boundingRect(c)[0])
        output_paths = []
        view_names = ['front', 'side', 'back']
        
        for i, contour in enumerate(sorted_contours):
            x, y, w, h = cv2.boundingRect(contour)
            padding = 15
            
            # Extract the view with padding, ensuring it doesn't go out of bounds
            view = image[max(0, y-padding):min(y+h+padding, image.shape[0]), max(0, x-padding):min(x+w+padding, image.shape[1])]
            
            # DEFINITIVE FIX: Get the actual shape of the extracted (potentially clipped) view.
            view_h, view_w, _ = view.shape

            # Create a canvas based on the padded view's dimensions for a 16:9 layout
            canvas_h = view_h + 40
            canvas_w = int(canvas_h * 16 / 9)
            canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255
            
            x_offset = (canvas_w - view_w) // 2
            y_offset = (canvas_h - view_h) // 2
            
            # Place the view onto the canvas using its actual dimensions
            canvas[y_offset:y_offset+view_h, x_offset:x_offset+view_w] = view

            base_name = Path(input_file).stem
            # Use the index 'i' in case there are fewer than 3 views found
            view_name = view_names[i] if i < len(view_names) else f"view_{i+1}"
            output_filename = f"{base_name}_{view_name}_layout.png"
            final_output_path = output_directory / output_filename
            
            cv2.imwrite(str(final_output_path), canvas)
            output_paths.append(str(final_output_path))
            
        print(f"✅ SUCCESS: Successfully created {len(output_paths)} separate character view layouts.")
        return output_paths
    except Exception as e:
        error_message = f"Failed to split and layout character sheet. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return [error_message]

# (The other functions in this file remain unchanged)
def generate_character_mask(input_path: str, output_path: str) -> str:
    print(f"\n[Tool: generate_character_mask]")
    try:
        mp_selfie_segmentation = mp.solutions.selfie_segmentation
        input_file = resolve_path_in_workspace(input_path)
        output_file = resolve_path_in_workspace(output_path)
        with mp_selfie_segmentation.SelfieSegmentation(model_selection=0) as selfie_segmentation:
            image = cv2.imread(str(input_file))
            if image is None: raise ValueError(f"Could not read input image from '{input_path}'")
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = selfie_segmentation.process(rgb_image)
            mask = (results.segmentation_mask > 0.5).astype(np.uint8) * 255
            cv2.imwrite(str(output_file), mask)
        message = f"Successfully generated character mask and saved to {output_file}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        error_message = f"Failed to generate character mask. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

def create_hologram_effect(input_path: str, output_path: str) -> str: return "Not implemented for this fix."

_TOOL_FUNCTIONS = [split_and_layout_character_sheet, create_hologram_effect, generate_character_mask]
def get_tool_declarations(): return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry(): return {f.__name__: f for f in _TOOL_FUNCTIONS}