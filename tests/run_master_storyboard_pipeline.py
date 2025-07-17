# run_master_storyboard_pipeline.py
# The definitive, end-to-end master pipeline.
# Phase 1: Generates a new, stylized 3D character from a text prompt.
# Phase 2: Splits the character sheet into usable assets.
# Phase 3: Uses the local ComfyUI pipeline to re-pose the character.
# Phase 4: Uses the cloud-based Imagen 3 tool for final quality refinement.

import os
import sys
import random
import time
import shutil
from pathlib import Path

# --- Path Setup & Warning Suppression ---
import warnings
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports ---
from tools.nyra_system_tools import make_directory
from tools.nyra_comfyui_caller import execute_comfyui_workflow
from tools.nyra_imagen_gen import generate_image, AspectRatio
from tools.nyra_character_tools import split_and_layout_character_sheet
from tools.nyra_imagen_edit import edit_image, EditMode
from tools.nyra_pose_tools import extract_facemesh # Re-using the pose assets from previous runs

# ======================================================================
# >> MASTER CONTROL PANEL <<
# ======================================================================
# --- PHASE 1: CHARACTER CONCEPT ---
CHARACTER_PROMPT = "A 3-view character sheet of a new male space ranger named 'Jax', rugged, short blonde hair, wearing a white and gold armored suit, in the style of a modern 3D Pixar animated film, plain white background."

# --- PHASE 3: POSE & LOCAL GENERATION ---
# This skeleton will be used to define the new pose
POSE_SKELETON_REF = "output/pixar_test_v2/pose_skeleton.png" 
LOCAL_PROMPT = "A photorealistic 3D cartoon character, Jax, smiling and giving a thumbs-up"
LOCAL_SEED = random.randint(0, 9999999999)

# --- PHASE 4: CLOUD REFINEMENT ---
STYLE_TRANSFER_PROMPT = "A high quality 3D cartoon character, cinematic, high detail, in the style of a Pixar film"

# --- FILE & DIRECTORY SETUP ---
PROJECT_DIR = "output/master_pipeline_jax"
# Phase 1 output
CHAR_SHEET_PATH = f"{PROJECT_DIR}/00_jax_master_sheet.png"
# Phase 2 output (the key asset)
CHAR_FRONT_LAYOUT_PATH = f"{PROJECT_DIR}/00_jax_master_sheet_front_layout.png"
# Phase 3 output
STAGE_3_PREFIX = "01_posed_from_local"
# Phase 4 output
FINAL_OUTPUT_PATH = f"{PROJECT_DIR}/02_jax_final_posed.png"
# ======================================================================

def run_master_workflow():
    """Executes the entire character creation and posing pipeline."""
    print("--- Initializing Master Storyboard Pipeline ---")
    
    workspace_dir = Path(config.WORKSPACE_DIR)
    
    try:
        make_directory(PROJECT_DIR)

        # === PHASE 1: GENERATE MASTER CHARACTER SHEET ===
        print("\n" + "="*70)
        print("--- PHASE 1: Generating Master Character Sheet via Imagen 4 ---")
        
        result1 = generate_image(
            model_name="imagen-4.0-ultra-generate-preview-06-06",
            prompt=CHARACTER_PROMPT,
            output_path=CHAR_SHEET_PATH,
            aspect_ratio=AspectRatio.RATIO_16_9
        )
        if "FAILED" in str(result1): raise RuntimeError(f"Phase 1 failed: {result1}")
        print(f"[DIRECTOR] > Phase 1 successful. Master sheet saved to '{result1}'")

        # === PHASE 2: SPLIT CHARACTER SHEET ===
        print("\n" + "="*70)
        print("--- PHASE 2: Splitting Character Sheet ---")
        
        result2 = split_and_layout_character_sheet(
            input_path=CHAR_SHEET_PATH,
            output_dir=PROJECT_DIR
        )
        if "FAILED" in str(result2): raise RuntimeError(f"Phase 2 failed: {result2}")
        print(f"[DIRECTOR] > Phase 2 successful. Character layouts saved in '{PROJECT_DIR}'")

        # === PHASE 3: LOCAL POSE GENERATION ===
        print("\n" + "="*70)
        print("--- PHASE 3: Local Pose Generation via ComfyUI ---")

        # Define the exact path for the character reference for ComfyUI
        character_ref_for_comfy = str(workspace_dir / CHAR_FRONT_LAYOUT_PATH)
        
        result3 = execute_comfyui_workflow(
            workflow_api_json_path=str(workspace_dir / "ComfyUI" / "workflow_api.json"),
            character_ref_path=character_ref_for_comfy,
            pose_skeleton_path=str(workspace_dir / POSE_SKELETON_REF),
            positive_prompt=LOCAL_PROMPT,
            negative_prompt="ugly, deformed",
            output_path_prefix=STAGE_3_PREFIX,
            seed=LOCAL_SEED
        )
        if "FAILED" in str(result3): raise RuntimeError(f"Stage 3 failed: {result3}")

        # Find and move the generated file
        time.sleep(2)
        comfyui_output_dir = workspace_dir / "ComfyUI" / "output"
        generated_files = list(comfyui_output_dir.glob(f'{STAGE_3_PREFIX}*.png'))
        if not generated_files: raise FileNotFoundError("Could not find output from ComfyUI.")
        stage_3_output_file = max(generated_files, key=lambda f: f.stat().st_ctime)
        stage_3_final_path = workspace_dir / PROJECT_DIR / "01_posed_from_local.png"
        shutil.move(stage_3_output_file, stage_3_final_path)
        print(f"[DIRECTOR] > Stage 3 successful. Posed image saved to '{stage_3_final_path}'")
        
        # === PHASE 4: CLOUD REFINEMENT ===
        print("\n" + "="*70)
        print("--- PHASE 4: Cloud Refinement via Imagen 3 ---")

        result4 = edit_image(
            edit_mode=EditMode.STYLE,
            output_path=FINAL_OUTPUT_PATH,
            prompt=STYLE_TRANSFER_PROMPT,
            input_path=str(stage_3_final_path.relative_to(workspace_dir)),
            style_ref_path=CHAR_FRONT_LAYOUT_PATH
        )
        if "FAILED" in str(result4): raise RuntimeError(f"Stage 4 failed: {result4}")
        print(f"[DIRECTOR] > Stage 4 successful. Final image saved to {result4}")

    except Exception as e:
        print(f"\n--- WORKFLOW HALTED DUE TO ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "="*70)
    print("--- Master Storyboard Pipeline Complete ---")
    print(f"--- Final image available at: {FINAL_OUTPUT_PATH} ---")

if __name__ == "__main__":
    run_master_workflow()