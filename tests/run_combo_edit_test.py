# tests/run_combo_edit_test.py
# Definitive Version 4.0: Fixes a NameError by defining the
# HISTORICAL_FIGURE_NAME variable.

import os
import sys
from pathlib import Path

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports ---
from tools.nyra_system_tools import make_directory
from tools.nyra_imagen_edit import edit_image, EditMode, ControlType
from tools.models import MODELS

# ======================================================================
# >> TEST ASSETS & PARAMETERS (UPDATED) <<
# ======================================================================
# DEFINITIVE FIX: Added the missing variable definition.
HISTORICAL_FIGURE_NAME = "Ashoka"
# This path now points to the existing Ashoka asset you provided.
CHARACTER_REFERENCE_PATH = "output/ashoka_test/character_assets/ashoka_character_sheet_front_layout.png"
# This test still uses a pre-made skeleton image as the pose control.
POSE_SKELETON_PATH = "assets/poses/standing_hero_pose_skeleton.png"
# Output path is updated for the correct character.
FINAL_OUTPUT_PATH = "output/combo_edit_test/ashoka_hero_pose.png"
# Prompt is updated for the correct character.
PROMPT = "A cinematic, photorealistic portrait of Emperor Ashoka in a heroic standing pose, looking towards the horizon."
# ======================================================================

def run_combo_edit_test():
    """
    Initializes and runs the definitive combined reference editing test
    using the specified Ashoka character asset.
    """
    project_dir = Path(config.WORKSPACE_DIR) / "output/combo_edit_test"
    print(f"--- Initializing Combined Reference Editing Test for '{HISTORICAL_FIGURE_NAME}' ---")
    
    try:
        make_directory(str(project_dir))
        
        # Verify input assets exist
        if not (Path(config.WORKSPACE_DIR) / CHARACTER_REFERENCE_PATH).exists():
            print(f"FATAL ERROR: Prerequisite character file not found at '{CHARACTER_REFERENCE_PATH}'")
            return
        if not (Path(config.WORKSPACE_DIR) / POSE_SKELETON_PATH).exists():
            print(f"FATAL ERROR: Prerequisite pose skeleton file not found at '{POSE_SKELETON_PATH}'")
            return

        # --- Execute The Test ---
        edit_image(
            model_name=MODELS["imagen_edit"][0],
            edit_mode=EditMode.SUBJECT_CUSTOMIZATION,
            output_path=FINAL_OUTPUT_PATH,
            prompt=PROMPT,
            # This provides the character's identity
            subject_ref_path=CHARACTER_REFERENCE_PATH,
            # This provides the character's pose
            control_ref_path=POSE_SKELETON_PATH,
            control_type=ControlType.SCRIBBLE
        )

    except Exception as e:
        print(f"\n--- ❌ TEST FAILED ---")
        print(f"An error occurred: {e}")
        return

    print("\n" + "="*80)
    print("--- ✅ Combined Reference Editing Test Complete ---")
    print(f"--- Review the output file at: {FINAL_OUTPUT_PATH} ---")

if __name__ == "__main__":
    run_combo_edit_test()