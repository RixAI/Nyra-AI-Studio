# run_character_pose_generation.py
# Definitive Version 3.0: Re-architected with the `pathlib` library for
# robust, platform-agnostic file and path handling to fix the FileNotFoundError.

import os
import sys
import random
import time
import shutil
from pathlib import Path # Import the Path object

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from tools.nyra_comfyui_caller import execute_comfyui_workflow
from tools.nyra_system_tools import make_directory

# ======================================================================
# >> CONTROL PANEL <<
# ======================================================================
GENERATION_SETTINGS = {
    "character_ref_image": "output/pixar_test_v2/alina_raw_sheet_front_layout.png",
    "pose_skeleton_image": "output/pixar_test_v2/pose_skeleton.png",
    
    "positive_prompt": "A photorealistic 3D cartoon character, Alina, wearing a sleek flight suit, smiling, giving a thumbs-up, plain white background",
    "negative_prompt": "ugly, deformed, blurry, text, watermark, signature",

    "width": 512,
    "height": 768,
    
    "seed": random.randint(0, 9999999999),
    "steps": 25,
    "cfg": 7.5,
    
    "output_filename_prefix": "Alina_Thumbs_Up",
    "final_output_path": "output/character_renders/Alina_Thumbs_Up_v1.png"
}
# ======================================================================

def run_generation():
    """Executes the generation and moves the file to the final path."""
    print("--- Initializing Controllable Character Pose Generation ---")

    # --- Use pathlib for robust path handling ---
    workspace_dir = Path(config.WORKSPACE_DIR)
    workflow_json_path = workspace_dir / "ComfyUI" / "workflow_api.json"
    final_output_path = workspace_dir / GENERATION_SETTINGS["final_output_path"]
    
    # Create the final output directory if it doesn't exist
    final_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not workflow_json_path.exists():
        print(f"\nFATAL ERROR: ComfyUI workflow JSON not found at '{workflow_json_path}'")
        return

    # --- Execute the ComfyUI workflow ---
    execute_comfyui_workflow(
        workflow_api_json_path=str(workflow_json_path),
        character_ref_path=str(workspace_dir / GENERATION_SETTINGS["character_ref_image"]),
        pose_skeleton_path=str(workspace_dir / GENERATION_SETTINGS["pose_skeleton_image"]),
        positive_prompt=GENERATION_SETTINGS["positive_prompt"],
        negative_prompt=GENERATION_SETTINGS["negative_prompt"],
        output_path_prefix=GENERATION_SETTINGS["output_filename_prefix"],
        width=GENERATION_SETTINGS["width"],
        height=GENERATION_SETTINGS["height"],
        seed=GENERATION_SETTINGS["seed"],
        steps=GENERATION_SETTINGS["steps"],
        cfg=GENERATION_SETTINGS["cfg"]
    )
    
    # --- Move the file to its final destination ---
    print("\n--- Moving file to final destination ---")
    time.sleep(2) # Give a moment for the file to be fully written
    
    comfyui_output_dir = workspace_dir / "ComfyUI" / "output"
    
    # Find the most recently created file with the correct prefix
    generated_files = list(comfyui_output_dir.glob(f'{GENERATION_SETTINGS["output_filename_prefix"]}*.png'))
    if not generated_files:
        print("\n❌ FAILED: Could not find the output image from ComfyUI to move it.")
        return
        
    source_file = max(generated_files, key=lambda f: f.stat().st_ctime)
    
    print(f"-> Moving '{source_file.name}' to '{final_output_path}'")
    shutil.move(source_file, final_output_path)
    print(f"✅ SUCCESS: File moved successfully.")
    
    print("\n--- Generation Complete ---")

if __name__ == "__main__":
    run_generation()