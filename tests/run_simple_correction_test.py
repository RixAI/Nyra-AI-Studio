# run_simple_correction_test.py
# A focused, simple test script to validate the two-part correction workflow.
# This workflow uses the drifted image for its pose and the original character
# sheet for its identity.

import os
import sys
import time

# --- Path Setup & Warning Suppression ---
import warnings
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports ---
from tools.nyra_system_tools import make_directory
from tools.nyra_imagen_gen import generate_image, AspectRatio
from tools.nyra_imagen_edit import edit_image, EditMode

# ======================================================================
# >> MASTER CONTROL PANEL FOR THE TEST <<
# ======================================================================
# --- INPUTS ---
# 1. Identity Source: The original, high-fidelity character asset.
IDENTITY_ANCHOR_PATH = "assets/characters/jax/jax_front_layout.png"

# 2. Pose Source: The 50% accurate, "drifted" image from a previous run.
#    This image has the correct pose and composition but the wrong identity.
#    (Using one of the "funny results" as the input for this test)
DRIFTED_POSE_SOURCE_PATH = "output/universal_storyboard_v3/shot_01/posed_char_drifted.png" 

# --- OUTPUTS ---
PROJECT_DIR = "output/simple_correction_test"
# The output of the core correction logic
CORRECTED_CHARACTER_PATH = f"{PROJECT_DIR}/01_character_corrected.png"
# A temporary 16:9 canvas used for aspect ratio correction
CANVAS_16_9_PATH = f"{PROJECT_DIR}/temp_16_9_canvas.png"
# The final, polished output
FINAL_16_9_IMAGE_PATH = f"{PROJECT_DIR}/02_final_image_16_9.png"
# ======================================================================

def run_correction_test():
    """Executes the focused two-part correction and outpainting test."""
    print("--- Initializing Simple Two-Part Correction Test ---")

    try:
        make_directory(PROJECT_DIR)
        
        # --- VERIFY INPUTS ---
        if not os.path.exists(IDENTITY_ANCHOR_PATH):
            raise FileNotFoundError(f"CRITICAL: Identity anchor not found at '{IDENTITY_ANCHOR_PATH}'")
        if not os.path.exists(DRIFTED_POSE_SOURCE_PATH):
            raise FileNotFoundError(f"CRITICAL: Drifted pose source not found at '{DRIFTED_POSE_SOURCE_PATH}'")

        # --- STEP 1: EXECUTE THE TWO-PART IDENTITY/POSE CORRECTION ---
        print("\n" + "="*70)
        print("--- STEP 1: Combining Identity Source + Pose Source ---")
        
        correction_prompt = "From the `subject_ref_path`, apply the character's exact identity (face, armor, colors, style). From the `input_path`, use the character's pose, composition, and camera angle. Combine them into a single, corrected character."
        
        edit_image(
            model_name='imagen-3.0-capability-001',
            edit_mode=EditMode.SUBJECT,
            prompt=correction_prompt,
            input_path=DRIFTED_POSE_SOURCE_PATH,      # The POSE source
            subject_ref_path=IDENTITY_ANCHOR_PATH,  # The IDENTITY source
            output_path=CORRECTED_CHARACTER_PATH
        )
        print(f"--- Correction complete. Intermediate file saved. ---")


        # --- STEP 2: FIX ASPECT RATIO VIA OUTPAINTING/EXPANSION ---
        print("\n" + "="*70)
        print("--- STEP 2: Expanding to 16:9 Aspect Ratio ---")
        
        # First, generate a blank 16:9 canvas to use as a style/format guide
        print(" -> Generating 16:9 canvas...")
        generate_image(
            model_name="imagen-3.0-fast-generate-001",
            prompt="a plain, neutral gray studio background, empty",
            output_path=CANVAS_16_9_PATH,
            aspect_ratio=AspectRatio.RATIO_16_9
        )

        # Now, use style transfer to "outpaint" the corrected character onto the 16:9 canvas
        print(" -> Outpainting character to new aspect ratio...")
        outpaint_prompt = "Recompose the input image onto a 16:9 canvas, matching the aspect ratio of the style reference. Intelligently extend the background where necessary."
        edit_image(
            model_name='imagen-3.0-capability-001',
            edit_mode=EditMode.STYLE,
            prompt=outpaint_prompt,
            input_path=CORRECTED_CHARACTER_PATH, # The character we just fixed
            style_ref_path=CANVAS_16_9_PATH,      # The 16:9 format guide
            output_path=FINAL_16_9_IMAGE_PATH
        )
        print(f"--- Aspect ratio corrected. ---")

    except Exception as e:
        print(f"\n--- ❌ TEST HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "="*70)
    print("--- ✅ Simple Correction Test Complete ---")
    print(f"--- Final 16:9 image available at: '{FINAL_16_9_IMAGE_PATH}' ---")

if __name__ == "__main__":
    run_correction_test()