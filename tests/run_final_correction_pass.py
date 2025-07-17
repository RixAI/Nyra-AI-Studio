# run_final_correction_pass.py
# This script executes the definitive, user-specified correction workflow.
# It uses the local ComfyUI pipeline because it is the only tool capable of
# extracting a pose from a full image and applying it to another identity
# without saving an intermediate "scribble" file.

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
CORRECTION_JOBS = [
    {
        "job_name": "Final_Correction_Shot_01",
        "pose_source_image": "output/universal_storyboard_v3/shot_01/posed_char_corrected.png",
        "identity_source_image": "assets/characters/jax/jax_back_layout.png",
        "output_prefix": "Jax_Final_Corrected_01"
    },
    {
        "job_name": "Final_Correction_Shot_02",
        "pose_source_image": "output/universal_storyboard_v3/shot_02/posed_char_corrected.png",
        "identity_source_image": "assets/characters/jax/jax_side_layout.png",
        "output_prefix": "Jax_Final_Corrected_02"
    },
    {
        "job_name": "Final_Correction_Shot_03",
        "pose_source_image": "output/universal_storyboard_v3/shot_03/posed_char_corrected.png",
        "identity_source_image": "assets/characters/jax/jax_front_layout.png",
        "output_prefix": "Jax_Final_Corrected_03"
    },
]

# --- STATIC ASSETS ---
CIP_FILE_PATH = "assets/characters/jax/jax_cip.txt"
PROJECT_DIR = "output/final_correction_pass"
# ======================================================================

def run_final_correction():
    """Executes the specified correction jobs using the local ComfyUI pipeline."""
    print("--- Initializing Final Correction Pass Workflow (Local Pipeline) ---")
    
    workspace_dir = Path(config.WORKSPACE_DIR)

    try:
        # --- Load Core Identity Prompt ---
        cip_path = workspace_dir / CIP_FILE_PATH
        if not cip_path.exists():
            raise FileNotFoundError(f"CRITICAL: CIP file not found at '{cip_path}'")
        character_identity_prompt = cip_path.read_text(encoding='utf-8').strip()
        print(f"[INFO] > Loaded Character Identity Prompt.")

        # --- Process Each Job ---
        for job in CORRECTION_JOBS:
            print("\n" + "#"*70)
            print(f"### PROCESSING JOB: {job['job_name']} ###")
            
            job_output_dir = workspace_dir / PROJECT_DIR / job['job_name']
            make_directory(str(job_output_dir))

            pose_source_path = workspace_dir / job['pose_source_image']
            identity_source_path = workspace_dir / job['identity_source_image']
            
            if not pose_source_path.exists() or not identity_source_path.exists():
                print(f"❌ WARNING: Skipping job. A required source image was not found.")
                continue

            # STEP 1: Extract skeleton from the POSE SOURCE image.
            print(f"\n[JOB: {job['job_name']}] > 1. Extracting pose skeleton from '{job['pose_source_image']}'...")
            skeleton_path_for_job = job_output_dir / "temp_skeleton.png"
            extract_openpose_skeleton(
                input_path=str(job['pose_source_image']),
                output_path=str(skeleton_path_for_job)
            )

            # STEP 2: Execute ComfyUI workflow.
            print(f"\n[JOB: {job['job_name']}] > 2. Executing local generation...")
            execute_comfyui_workflow(
                workflow_api_json_path=str(workspace_dir / "ComfyUI" / "workflow_api.json"),
                character_ref_path=str(identity_source_path), # Feeds IPAdapter for Identity
                pose_skeleton_path=str(skeleton_path_for_job),    # Feeds ControlNet for Pose
                positive_prompt=character_identity_prompt,
                negative_prompt="ugly, deformed, blurry, text, watermark, signature",
                output_path_prefix=job['output_prefix'],
                seed=int(time.time())
            )
            
            # STEP 3: Move final result into the job folder for organization.
            time.sleep(2)
            comfyui_output_dir = workspace_dir / "ComfyUI" / "output"
            generated_files = list(comfyui_output_dir.glob(f"{job['output_prefix']}*.png"))
            if generated_files:
                source_file = max(generated_files, key=lambda f: f.stat().st_ctime)
                final_output_path = job_output_dir / f"final_result.png"
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
    print("--- ✅ All Final Correction Jobs Processed. ---")

if __name__ == "__main__":
    run_final_correction()