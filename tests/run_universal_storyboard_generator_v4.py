# run_universal_storyboard_generator_v3.py
# Definitive Version 3: Corrects the Consistency Correction Pass (Step 4)
# to use 'subject' mode with multi-reference input, as per the final correct logic.

import os
import sys
import json
import time

# --- Path Setup & Warning Suppression ---
import warnings
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports ---
from tools.nyra_system_tools import make_directory, save_text_file, list_files
from tools.nyra_imagen_gen import generate_image, AspectRatio
from tools.nyra_character_tools import split_and_layout_character_sheet
from tools.nyra_pose_tools import extract_openpose_skeleton
from tools.nyra_imagen_edit import edit_image, EditMode

# ======================================================================
# >> MASTER CONTROL PANEL <<
# ======================================================================
CHARACTER_NAME = "Jax"
SHOT_LIST_FILE = "shot_list.json"
STORYBOARD_DIR = "output/universal_storyboard_v3"
CHARACTER_ASSET_DIR = f"assets/characters/{CHARACTER_NAME.lower()}"

CORE_IDENTITY_PROMPT = f"""
A 3D Pixar-style male character named {CHARACTER_NAME}. He is a rugged, friendly space ranger...
""" # (Content is the same as before)
# ======================================================================

def create_character_assets_if_needed():
    # This function remains unchanged. It correctly generates and splits the sheet.
    front_anchor = f"{CHARACTER_ASSET_DIR}/{CHARACTER_NAME.lower()}_front_layout.png"
    side_anchor = f"{CHARACTER_ASSET_DIR}/{CHARACTER_NAME.lower()}_side_layout.png"
    back_anchor = f"{CHARACTER_ASSET_DIR}/{CHARACTER_NAME.lower()}_back_layout.png"
    if all(os.path.exists(p) for p in [front_anchor, side_anchor, back_anchor]):
        print(f"--- Found existing Digital Twin assets for '{CHARACTER_NAME}'. Skipping pre-production. ---")
        return
    print(f"--- CHARACTER PRE-PRODUCTION: Generating Digital Twin for '{CHARACTER_NAME}' ---")
    make_directory(CHARACTER_ASSET_DIR)
    master_sheet_path = f"{CHARACTER_ASSET_DIR}/master_3_view_sheet.png"
    generate_image(model_name="imagen-4.0-ultra-generate-preview-06-06", prompt=f"A 3-view character sheet of ({CORE_IDENTITY_PROMPT})...", output_path=master_sheet_path, aspect_ratio=AspectRatio.RATIO_16_9)
    split_and_layout_character_sheet(input_path=master_sheet_path, output_dir=CHARACTER_ASSET_DIR)
    os.rename(f"{CHARACTER_ASSET_DIR}/master_3_view_sheet_front_layout.png", front_anchor)
    os.rename(f"{CHARACTER_ASSET_DIR}/master_3_view_sheet_side_layout.png", side_anchor)
    os.rename(f"{CHARACTER_ASSET_DIR}/master_3_view_sheet_back_layout.png", back_anchor)
    print(f"--- Character '{CHARACTER_NAME}' is ready for production. ---")

def process_shot(shot_data: dict):
    shot_id = shot_data['shot_id']
    view_angle = shot_data['view_angle']
    shot_dir = f"{STORYBOARD_DIR}/shot_{shot_id:02d}"
    print(f"\n### PROCESSING SHOT {shot_id:02d} (View: {view_angle.upper()}) ###")
    make_directory(shot_dir)

    visual_anchor_path = f"{CHARACTER_ASSET_DIR}/{CHARACTER_NAME.lower()}_{view_angle}_layout.png"
    if not os.path.exists(visual_anchor_path):
        raise FileNotFoundError(f"CRITICAL: The required visual anchor for view '{view_angle}' was not found.")
    print(f"[INFO] > Selected visual anchor: '{visual_anchor_path}'")

    pose_ref_path = f"{shot_dir}/generated_pose_ref.png"
    skeleton_path = f"{shot_dir}/pose_skeleton.png"
    posed_drifted_path = f"{shot_dir}/posed_char_drifted.png"
    posed_corrected_path = f"{shot_dir}/posed_char_corrected.png"
    scene_bg_path = f"{shot_dir}/scene_background.png"
    final_keyframe_path = f"{shot_dir}/final_keyframe.png"

    # Steps 1, 2, 3 remain the same
    print(f"\n[SHOT {shot_id}] > 1. Generating Pose Reference...")
    generate_image(model_name="imagen-3.0-fast-generate-001", prompt=shot_data['pose_prompt'], output_path=pose_ref_path, aspect_ratio=AspectRatio.RATIO_9_16)
    print(f"\n[SHOT {shot_id}] > 2. Extracting Pose Skeleton...")
    extract_openpose_skeleton(input_path=pose_ref_path, output_path=skeleton_path)
    print(f"\n[SHOT {shot_id}] > 3. Generating Posed Character (Initial)...")
    edit_image(model_name='imagen-3.0-capability-001', edit_mode=EditMode.SCRIBBLE, prompt=f"({CORE_IDENTITY_PROMPT}) {shot_data['action_prompt']}", subject_ref_path=visual_anchor_path, scribble_ref_path=skeleton_path, output_path=posed_drifted_path)
    
    # --- DEFINITIVE FIX FOR STEP 4 ---
    print(f"\n[SHOT {shot_id}] > 4. Applying Consistency Correction Pass (Subject Mode)...")
    # This call uses 'subject' mode with two references to correct details while locking the pose.
    edit_image(
        model_name='imagen-3.0-capability-001',
        edit_mode=EditMode.SUBJECT, # Using SUBJECT mode as requested
        prompt=f"A cinematic shot of ({CORE_IDENTITY_PROMPT}). Refine the subject to match the reference, while adhering to the pose from the scribble.",
        subject_ref_path=visual_anchor_path, # The identity anchor
        scribble_ref_path=skeleton_path, # The pose anchor
        output_path=posed_corrected_path
    )
    
    # Steps 5 & 6 remain unchanged
    print(f"\n[SHOT {shot_id}] > 5. Generating Scene Background...")
    generate_image(model_name="imagen-4.0-generate-preview-06-06", prompt=shot_data['scene_prompt'], output_path=scene_bg_path, aspect_ratio=AspectRatio.RATIO_16_9)
    print(f"\n[SHOT {shot_id}] > 6. Compositing Final Keyframe...")
    edit_image(model_name='imagen-3.0-capability-001', edit_mode=EditMode.BGSWAP, prompt=shot_data['scene_prompt'], input_path=posed_corrected_path, output_path=final_keyframe_path)
    
    print(f"\n--- ✅ SHOT {shot_id:02d} KEYFRAME COMPLETE ---")

def run_universal_storyboard_generator_v3():
    """Main function to run the entire storyboard production pipeline."""
    print("--- Initializing Universal Storyboard Generator v3 ---")
    try:
        if not os.path.exists(SHOT_LIST_FILE):
            raise FileNotFoundError(f"CRITICAL: The shot list '{SHOT_LIST_FILE}' was not found.")
        with open(SHOT_LIST_FILE, 'r') as f:
            shot_list = json.load(f)
        
        create_character_assets_if_needed()
        
        for shot_data in shot_list:
            process_shot(shot_data)

    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "="*70)
    print("--- ✅ All Shots Processed. Universal Storyboard Production Complete. ---")

if __name__ == "__main__":
    run_universal_storyboard_generator_v3()