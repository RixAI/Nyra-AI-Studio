# run_cloud_swap_opposite.py
# A script to test the "opposite" workflow as requested.
# It uses the original character as the main input and the posed character
# as the subject reference.

import os
import sys
from pathlib import Path

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports ---
from tools.nyra_system_tools import make_directory
from tools.nyra_imagen_edit import edit_image, EditMode

# ======================================================================
# >> SWAP JOB CONTROL PANEL <<
# ======================================================================
OPPOSITE_SWAP_JOBS = [
    {
        "job_name": "Opposite_Swap_Test_01",
        "identity_source_image": "assets/characters/jax/jax_back_layout.png",
        "pose_source_image": "output/universal_storyboard_v3/shot_01/posed_char_corrected.png",
    },
    {
        "job_name": "Opposite_Swap_Test_02",
        "identity_source_image": "assets/characters/jax/jax_side_layout.png",
        "pose_source_image": "output/universal_storyboard_v3/shot_02/posed_char_corrected.png",
    },
    {
        "job_name": "Opposite_Swap_Test_03",
        "identity_source_image": "assets/characters/jax/jax_front_layout.png",
        "pose_source_image": "output/universal_storyboard_v3/shot_03/posed_char_corrected.png",
    },
]

# --- STATIC ASSETS ---
CIP_FILE_PATH = "assets/characters/jax/jax_cip.txt"
PROJECT_DIR = "output/cloud_swap_opposite"
# ======================================================================

def run_cloud_swap_opposite():
    """Executes the specified "opposite" jobs using the cloud-based edit_image tool."""
    print("--- Initializing Cloud-Based Opposite Swap Workflow ---")
    
    try:
        make_directory(PROJECT_DIR)

        # --- Load Core Identity Prompt ---
        cip_path = Path(config.WORKSPACE_DIR) / CIP_FILE_PATH
        if not cip_path.exists():
            raise FileNotFoundError(f"CRITICAL: Core Identity Prompt file not found at '{cip_path}'")
        character_identity_prompt = cip_path.read_text(encoding='utf-8').strip()
        print(f"[INFO] > Loaded Character Identity Prompt.")

        # --- Process Each Job ---
        for job in OPPOSITE_SWAP_JOBS:
            print("\n" + "#"*70)
            print(f"### PROCESSING JOB: {job['job_name']} ###")
            
            identity_source_path = Path(config.WORKSPACE_DIR) / job['identity_source_image']
            pose_source_path = Path(config.WORKSPACE_DIR) / job['pose_source_image']

            if not pose_source_path.exists() or not identity_source_path.exists():
                print(f"❌ WARNING: Skipping job. A required source image was not found.")
                continue

            # Construct the explicit prompt for the opposite logic
            final_prompt = (
                f"({character_identity_prompt}). "
                "This is a subject swap operation. "
                "The final character's identity (face, armor, style) MUST exactly match the character in the `input_path`. "
                "The final character's pose and camera angle MUST exactly match the subject in the `subject_ref_path`."
            )
            
            output_path = f"{PROJECT_DIR}/{job['job_name']}_result.png"

            print(f" -> Calling 'edit_image' with reversed inputs...")
            
            edit_image(
                model_name='imagen-3.0-capability-001',
                edit_mode=EditMode.SUBJECT,
                prompt=final_prompt,
                input_path=str(identity_source_path),  # IDENTITY SOURCE (now the image to be edited)
                subject_ref_path=str(pose_source_path), # POSE SOURCE (now the subject reference)
                output_path=output_path
            )

            print(f"\n--- ✅ JOB '{job['job_name']}' COMPLETE ---")
            print(f"--- Output available at: '{output_path}' ---")

    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "#"*70)
    print("--- ✅ All Opposite Swap Jobs Processed. ---")

if __name__ == "__main__":
    run_cloud_swap_opposite()