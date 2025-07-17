# run_canvas_workflow.py
# The definitive workflow that uses the canvas-layout assets from the character
# tool and then uses inpainting to generate the final scene.

import os
import sys
from pathlib import Path
import cv2
import numpy as np

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports ---
from tools.nyra_system_tools import make_directory
from tools.nyra_imagen_gen import generate_image, AspectRatio
from tools.nyra_character_tools import split_and_layout_character_sheet
from tools.nyra_imagen_edit import edit_image, EditMode

# ======================================================================
# >> CANVAS WORKFLOW CONTROL PANEL <<
# ======================================================================
HISTORICAL_FIGURE_NAME = "Shivaji"
CHARACTER_DESCRIPTION = "A realistic, powerful portrait of Chhatrapati Shivaji Maharaj, the 17th-century Maratha king. He has a sharp, determined gaze, a traditional mustache, and wears a 'mandil' turban and royal attire."
SCENE_PROMPT = "The rugged, windswept ramparts of Raigad Fort at dawn. The sky is a mix of orange and purple. In the distance, the Sahyadri mountains are visible through the morning mist."
PROJECT_DIR = Path(config.WORKSPACE_DIR) / f"output/{HISTORICAL_FIGURE_NAME.lower()}_canvas_workflow"
# ======================================================================

def create_inverse_mask(image_path: Path, mask_output_path: Path):
    """Creates a mask where the subject is black and the background is white."""
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    # Threshold to get a binary image: >250 becomes white (255), everything else black (0)
    _, binary_mask = cv2.threshold(img, 250, 255, cv2.THRESH_BINARY)
    # The background is now white (255), which is the area to inpaint.
    # The character is black (0), the area to keep.
    cv2.imwrite(str(mask_output_path), binary_mask)
    print(f" -> Inverse mask created at '{mask_output_path}'")


def run_canvas_based_pipeline():
    """
    Executes the corrected pipeline using character layouts and inpainting.
    """
    print(f"--- Initializing Canvas-Based Workflow for '{HISTORICAL_FIGURE_NAME}' ---")
    
    try:
        make_directory(str(PROJECT_DIR))

        # --- PHASE 1: Generate Character Sheet & Layouts ---
        print("\n--- PHASE 1: Generating Character Digital Twin ---")
        char_sheet_path = PROJECT_DIR / "character_sheet.png"
        generate_image(
            model_name="imagen-4.0-ultra-generate-preview-06-06",
            prompt=f"A 3-view character sheet of ({CHARACTER_DESCRIPTION}). The image must contain three separate, full-body figures (front, side, and back) on a plain white background.",
            output_path=str(char_sheet_path),
            aspect_ratio=AspectRatio.RATIO_16_9
        )
        # This tool creates the final 16:9 layout assets
        split_and_layout_character_sheet(input_path=str(char_sheet_path), output_dir=str(PROJECT_DIR))
        
        # This is our key asset: the character already on a 16:9 canvas
        character_layout_path = PROJECT_DIR / "character_sheet_front_layout.png"
        if not character_layout_path.exists(): raise RuntimeError("Failed to generate character layout asset.")

        # --- PHASE 2: Generate Inverse Mask for Inpainting ---
        print("\n--- PHASE 2: Generating Inpainting Mask ---")
        inpainting_mask_path = PROJECT_DIR / "inpainting_mask.png"
        create_inverse_mask(character_layout_path, inpainting_mask_path)

        # --- PHASE 3: Generate Scene via Inpainting ---
        print("\n--- PHASE 3: Executing Inpainting with Cloud API ---")
        final_image_path = PROJECT_DIR / "final_scene.png"
        
        edit_image(
            model_name='imagen-3.0-capability-001',
            edit_mode=EditMode.INPAINT,
            prompt=SCENE_PROMPT,
            input_path=str(character_layout_path), # The image with the character on a white 16:9 canvas
            mask_path=str(inpainting_mask_path),    # The mask defining the white background to be filled
            output_path=str(final_image_path)
        )
        if not final_image_path.exists(): raise RuntimeError("Inpainting failed to produce an image.")

    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "="*80)
    print("--- ✅ Canvas-Based History Workflow Complete ---")
    print(f"--- Final composited image available at: {final_image_path} ---")

if __name__ == "__main__":
    run_canvas_based_pipeline()