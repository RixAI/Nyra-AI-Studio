# run_pose_and_scene_change.py
# A streamlined pipeline that uses pre-existing character assets to generate
# new storyboard keyframes with different poses and scenes.

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
from tools.nyra_system_tools import make_directory, list_files
from tools.nyra_imagen_gen import generate_image, AspectRatio
from tools.nyra_pose_tools import extract_openpose_skeleton
from tools.nyra_imagen_edit import edit_image, EditMode

# ======================================================================
# >> MASTER CONTROL PANEL <<
# ======================================================================
CHARACTER_NAME = "Jax"
SHOT_LIST_FILE = "shot_list.json"
STORYBOARD_DIR = "output/pose_scene_change_storyboard"
# This pipeline ASSUMES these assets already exist.
CHARACTER_ASSET_DIR = f"assets/characters/{CHARACTER_NAME.lower()}"
# ======================================================================

def process_shot(shot_data: dict, cip_content: str):
    """
    Processes a single shot from the list, generating the final keyframe image.
    """
    shot_id = shot_data['shot_id']
    view_angle = shot_data['view_angle']
    shot_dir = f"{STORYBOARD_DIR}/shot_{shot_id:02d}"
    print("\n" + "#"*70)
    print(f"### PROCESSING SHOT {shot_id:02d} (View: {view_angle.upper()}) ###")
    print("#"*70)

    make_directory(shot_dir)

    # --- INTELLIGENT ASSET SELECTION ---
    visual_anchor_path = f"{CHARACTER_ASSET_DIR}/{CHARACTER_NAME.lower()}_{view_angle}_layout.png"
    if not os.path.exists(visual_anchor_path):
        raise FileNotFoundError(f"CRITICAL: The required visual anchor for view '{view_angle}' was not found at '{visual_anchor_path}'.")
    print(f"[INFO] > Selected visual anchor for this shot: '{visual_anchor_path}'")

    # Define paths for this shot's assets
    pose_ref_path = f"{shot_dir}/generated_pose_ref.png"
    skeleton_path = f"{shot_dir}/pose_skeleton.png"
    posed_drifted_path = f"{shot_dir}/posed_char_drifted.png"
    posed_corrected_path = f"{shot_dir}/posed_char_corrected.png"
    scene_bg_path = f"{shot_dir}/scene_background.png"
    final_keyframe_path = f"{shot_dir}/final_keyframe.png"

    # --- Full A-to-Z generation for the keyframe ---
    print(f"\n[SHOT {shot_id}] > 1. Generating Pose Reference...")
    generate_image(model_name="imagen-3.0-fast-generate-001", prompt=shot_data['pose_prompt'], output_path=pose_ref_path, aspect_ratio=AspectRatio.RATIO_9_16)
    
    print(f"\n[SHOT {shot_id}] > 2. Extracting Pose Skeleton...")
    extract_openpose_skeleton(input_path=pose_ref_path, output_path=skeleton_path)
    
    print(f"\n[SHOT {shot_id}] > 3. Generating Posed Character...")
    edit_image(model_name='imagen-3.0-capability-001', edit_mode=EditMode.SCRIBBLE, prompt=f"({cip_content}) {shot_data['action_prompt']}", subject_ref_path=visual_anchor_path, scribble_ref_path=skeleton_path, output_path=posed_drifted_path)
    
    print(f"\n[SHOT {shot_id}] > 4. Applying Multi-Reference Correction...")
    edit_image(
        model_name='imagen-3.0-capability-001',
        edit_mode=EditMode.SCRIBBLE,
        prompt=f"A cinematic shot of ({cip_content}). Refine armor and details to perfectly match the subject reference, while strictly adhering to the pose defined by the scribble.",
        input_path=posed_drifted_path,
        subject_ref_path=visual_anchor_path,
        scribble_ref_path=skeleton_path,
        output_path=posed_corrected_path
    )
    
    print(f"\n[SHOT {shot_id}] > 5. Generating Scene Background...")
    generate_image(model_name="imagen-4.0-generate-preview-06-06", prompt=shot_data['scene_prompt'], output_path=scene_bg_path, aspect_ratio=AspectRatio.RATIO_16_9)
    
    print(f"\n[SHOT {shot_id}] > 6. Compositing Final Keyframe...")
    edit_image(model_name='imagen-3.0-capability-001', edit_mode=EditMode.BGSWAP, prompt=shot_data['scene_prompt'], input_path=posed_corrected_path, output_path=final_keyframe_path)
    
    print(f"\n--- ✅ SHOT {shot_id:02d} KEYFRAME COMPLETE ---")
    print(f"--- Final image available at: {final_keyframe_path} ---")

def run_pose_and_scene_change_pipeline():
    """Main function to run the pose and scene change pipeline."""
    print("--- Initializing Pose & Scene Change Pipeline ---")
    try:
        # Verify the shot list exists
        if not os.path.exists(SHOT_LIST_FILE):
            raise FileNotFoundError(f"CRITICAL: The shot list '{SHOT_LIST_FILE}' was not found.")
        with open(SHOT_LIST_FILE, 'r') as f:
            shot_list = json.load(f)
        
        # Verify the character's Textual Anchor (CIP) exists and load it
        cip_path = f"{CHARACTER_ASSET_DIR}/{CHARACTER_NAME.lower()}_cip.txt"
        if not os.path.exists(cip_path):
            raise FileNotFoundError(f"CRITICAL: Character CIP file not found at '{cip_path}'. Please run the character creation pipeline first.")
        with open(cip_path, 'r') as f:
            cip_content = f.read()

        # Process each shot in the list
        for shot_data in shot_list:
            process_shot(shot_data, cip_content)

    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "="*70)
    print("--- ✅ All Shots Processed. Pose & Scene Change Production Complete. ---")

if __name__ == "__main__":
    run_pose_and_scene_change_pipeline()