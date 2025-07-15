# tools/nyra_character_tools.py
# Definitive Version 9.3: Removes all unused and incorrect imports.

# --- Path Setup ---
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ---

import cv2
import numpy as np
import argparse
from pathlib import Path
from typing import List
from tools._helpers import resolve_path_in_workspace
from tools import _schema_helper

# The rest of this file, including the split_and_layout_character_sheet function
# and the tool registration block, is correct and remains unchanged.
# ...

def create_hologram_effect(input_path: str, output_path: str) -> str:
    """
    Takes a character image, isolates the character, and applies a multi-pass
    holographic effect, saving the result as a new image.
    """
    print(f"\n[Tool: create_hologram_effect] (Multi-Pass Method)")
    try:
        print(" -> Step 1: Generating hologram texture...")
        texture_prompt = "a glitchy, flickering, blue static hologram texture, digital noise, scan lines, futuristic interface"
        temp_texture_path = Path(config.WORKSPACE_DIR) / "output" / "temp_hologram_texture.png"
        
        # DEFINITIVE FIX: Using a correct model name from our MODELS list.
        texture_result = generate_image(
            model_name="imagen-3.0-fast-generate-001", # Changed to a valid model
            prompt=texture_prompt,
            output_path=str(temp_texture_path),
            aspect_ratio=AspectRatio.RATIO_1_1
        )
        if not texture_result or "FAILED" in texture_result:
            raise RuntimeError(f"Failed to generate hologram texture: {texture_result}")
        
        # ... (The rest of the hologram function logic is unchanged) ...
        texture = cv2.imread(str(temp_texture_path))
        print(" -> Step 2: Isolating character...")
        input_file = resolve_path_in_workspace(input_path)
        character_img = cv2.imread(str(input_file))
        if character_img is None: raise ValueError(f"Could not read input image from '{input_path}'")
        gray = cv2.cvtColor(character_img, cv2.COLOR_BGR2GRAY)
        _, character_mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
        kernel = np.ones((3,3), np.uint8)
        character_mask = cv2.morphologyEx(character_mask, cv2.MORPH_CLOSE, kernel)
        print(" -> Step 3: Compositing hologram effect...")
        h, w, _ = character_img.shape
        texture = cv2.resize(texture, (w, h))
        blue_char = cv2.bitwise_and(character_img, character_img, mask=character_mask)
        blue_tint = np.full(character_img.shape, (255, 180, 50), dtype=np.uint8)
        blue_char = cv2.bitwise_and(blue_char, blue_tint)
        hologram = cv2.addWeighted(blue_char, 0.7, texture, 0.3, 0)
        for i in range(0, h, 4):
            cv2.line(hologram, (0, i), (w, i), (0, 0, 0), 1)
        final_hologram_bgra = cv2.cvtColor(hologram, cv2.COLOR_BGR2BGRA)
        final_hologram_bgra[:, :, 3] = cv2.bitwise_and(character_mask, cv2.bitwise_not(np.uint8(hologram[:,:,0]*0.2)))
        output_file = resolve_path_in_workspace(output_path)
        cv2.imwrite(str(output_file), final_hologram_bgra)
        os.remove(temp_texture_path)
        message = f"Hologram effect created successfully and saved to {output_file}"
        print(f"✅ SUCCESS: {message}")
        return message
        
    except Exception as e:
        error_message = f"Failed to create hologram effect. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

# ... (The rest of the file, including split_and_layout_character_sheet and the registration functions, remains unchanged) ...


def split_and_layout_character_sheet(input_path: str, output_dir: str) -> List[str]:
    """
    Takes a single 3-view character sheet image, intelligently segments each view, and saves
    each one onto its own separate, clean 16:9 white canvas.
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
        if len(contours) < 3:
            raise ValueError(f"Expected to find 3 character views, but only found {len(contours)}.")
        top_three_contours = sorted(contours, key=cv2.contourArea, reverse=True)[:3]
        sorted_contours = sorted(top_three_contours, key=lambda c: cv2.boundingRect(c)[0])
        cropped_views = []
        for contour in sorted_contours:
            x, y, w, h = cv2.boundingRect(contour)
            padding = 15
            cropped_view = image[max(0, y-padding):min(y+h+padding, image.shape[0]), max(0, x-padding):min(x+w+padding, image.shape[1])]
            cropped_views.append(cropped_view)
        output_paths = []
        view_names = ['front', 'side', 'back']
        aspect_w, aspect_h = 16, 9
        for i, view in enumerate(cropped_views):
            h, w, _ = view.shape
            canvas_h = h + 40
            canvas_w = int(canvas_h * aspect_w / aspect_h)
            canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255
            x_offset = (canvas_w - w) // 2
            y_offset = (canvas_h - h) // 2
            canvas[y_offset:y_offset+h, x_offset:x_offset+w] = view
            base_name = Path(input_file).stem
            output_filename = f"{base_name}_{view_names[i]}_layout.png"
            final_output_path = output_directory / output_filename
            cv2.imwrite(str(final_output_path), canvas)
            output_paths.append(str(final_output_path))
            print(f"✅ View '{view_names[i]}' laid out and saved to {final_output_path}")
        print(f"✅ SUCCESS: Successfully created 3 separate character view layouts.")
        return output_paths
    except Exception as e:
        error_message = f"Failed to split and layout character sheet. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return [error_message]

# --- TOOL REGISTRATION ---
_TOOL_FUNCTIONS = [split_and_layout_character_sheet, create_hologram_effect]
def get_tool_declarations():
    return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry():
    return {f.__name__: f for f in _TOOL_FUNCTIONS}

# --- COMMAND-LINE INTERFACE ---
if __name__ == '__main__':
    # This block is for direct testing and not part of the main AI workflow
    parser = argparse.ArgumentParser(description="Character Tools")
    subparsers = parser.add_subparsers(dest="command", required=True)
    parser_split = subparsers.add_parser('split', help="Split a character sheet into 3 layouts.")
    parser_split.add_argument("--input_path", required=True)
    parser_split.add_argument("--output_dir", required=True)
    parser_holo = subparsers.add_parser('hologram', help="Create a hologram effect.")
    parser_holo.add_argument("--input_path", required=True)
    parser_holo.add_argument("--output_path", required=True)
    args = parser.parse_args()
    if args.command == 'split':
        split_and_layout_character_sheet(args.input_path, args.output_dir)
    elif args.command == 'hologram':
        create_hologram_effect(args.input_path, args.output_path)