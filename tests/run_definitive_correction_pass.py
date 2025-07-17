# run_definitive_correction_pass.py
# A targeted script to execute the user-specified correction workflow.
# This workflow uses a previously generated (but flawed) image as a rich
# source for a new pose, and the original character assets for identity.

import os
import sys
import time
import shutil
from pathlib import Path

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from tools.nyra_comfyui_caller import execute_comfyui_workflow
from tools.nyra_pose_tools import extract_openpose_skeleton
from tools.nyra_system_tools import make_directory

# ======================================================================
# >> CORRECTION JOB CONTROL PANEL <<
# ======================================================================
# This list defines the correction jobs to run.
# Each job pairs a POSE source with an IDENTITY source.
CORRECTION_JOBS = [
    {
        "job_name": "Corrected_Shot_01_Pose",
        "pose_ref_path": "output/universal_storyboard_v3/shot_01/posed_char_corrected.png",
        "identity_ref_path": "assets/characters/jax/jax_back_layout.png",
        "output_prefix": "Jax_Corrected_From_Shot_01"
    },
    {
        "job_name": "Corrected_Shot_02_Pose",
        "pose_ref_path": "output/universal_storyboard_v3/shot_02/posed_char_corrected.png",
        "identity_ref_path": "assets/characters/jax/jax_side_layout.png",
        "output_prefix": "Jax_Corrected_From_Shot_02"
    },
    # Add more jobs here to test other combinations
    # {
    #     "job_name": "Corrected_Shot_03_Pose",
    #     "pose_ref_path": "output/universal_storyboard_v3/shot_03/posed_char_corrected.png",
    #     "identity_ref_path": "assets/characters/jax/jax_front_layout.png",
    #     "output_prefix": "Jax_Corrected_From_Shot_03"
    # },
]

# --- STATIC ASSETS ---
CIP_FILE_PATH = "assets/characters/jax/jax_cip.txt"
PROJECT_DIR = "output/definitive_correction_pass"
# ======================================================================

def run_definitive_correction():
    """Executes the specified correction jobs using the local ComfyUI pipeline."""
    print("--- Initializing Definitive Correction Pass Workflow ---")
    
    workspace_dir = Path(config.WORKSPACE_DIR)

    try:
        # --- Load Core Identity Prompt ---
        cip_path = workspace_dir / CIP_FILE_PATH
        if not cip_path.exists():
            raise FileNotFoundError(f"CRITICAL: Core Identity Prompt file not found at '{cip_path}'")
        character_identity_prompt = cip_path.read_text(encoding='utf-8').strip()
        print(f"[INFO] > Loaded Character Identity Prompt.")

        # --- Process Each Job ---
        for job in CORRECTION_JOBS:
            print("\n" + "#"*70)
            print(f"### PROCESSING JOB: {job['job_name']} ###")
            
            job_output_dir = workspace_dir / PROJECT_DIR / job['job_name']
            make_directory(str(job_output_dir))

            pose_source_path = workspace_dir / job['pose_ref_path']
            identity_source_path = workspace_dir / job['identity_ref_path']
            
            if not pose_source_path.exists():
                print(f"❌ WARNING: Skipping job. Pose source not found: {pose_source_path}")
                continue
            if not identity_source_path.exists():
                print(f"❌ WARNING: Skipping job. Identity source not found: {identity_source_path}")
                continue

            # --- Step 1: Extract new skeleton from the POSE SOURCE image ---
            print(f"\n[JOB: {job['job_name']}] > 1. Extracting skeleton from Pose Source...")
            new_skeleton_path = job_output_dir / "extracted_skeleton.png"
            extract_openpose_skeleton(
                input_path=str(job['pose_ref_path']),
                output_path=str(new_skeleton_path)
            )

            # --- Step 2: Execute ComfyUI workflow with the new inputs ---
            print(f"\n[JOB: {job['job_name']}] > 2. Executing local generation...")
            execute_comfyui_workflow(
                workflow_api_json_path=str(workspace_dir / "ComfyUI" / "workflow_api.json"),
                character_ref_path=str(identity_source_path), # Use canonical identity for IPAdapter
                pose_skeleton_path=str(new_skeleton_path),    # Use newly extracted skeleton for ControlNet
                positive_prompt=character_identity_prompt,   # Use the CIP file for the text prompt
                negative_prompt="ugly, deformed, blurry, text, watermark",
                output_path_prefix=job['output_prefix'],
                seed=int(time.time()) # Use a new seed for each run
            )
            
            # --- Step 3: Move final result for clarity ---
            time.sleep(2) # Give a moment for the file to be fully written
            comfyui_output_dir = workspace_dir / "ComfyUI" / "output"
            generated_files = list(comfyui_output_dir.glob(f"{job['output_prefix']}*.png"))
            if generated_files:
                source_file = max(generated_files, key=lambda f: f.stat().st_ctime)
                final_output_path = job_output_dir / f"{job['output_prefix']}_final.png"
                shutil.move(source_file, final_output_path)
                print(f"\n--- ✅ JOB '{job['job_name']}' COMPLETE ---")
                print(f"--- Final image available at: '{final_output_path}' ---")
            else:
                 print(f"\n--- ❌ JOB '{job['job_name']}' FAILED: No output image found from ComfyUI. ---")


    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "#"*70)
    print("--- ✅ All Correction Jobs Processed. ---")


if __name__ == "__main__":
    run_definitive_correction()