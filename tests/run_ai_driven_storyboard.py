# run_ai_driven_storyboard.py
# This master script uses AI to dynamically generate a shot list and then
# executes the procedural v4 pipeline to generate the final storyboard assets.

import os
import sys
import json

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Import Core Logic ---
# Import the new tool for AI shot generation
from tools.nyra_storyboarder import generate_shot_list
# Import the proven procedural workflow functions from our v4 script
from run_universal_storyboard_generator_v4 import create_character_assets_if_needed, process_shot

# ======================================================================
# >> MASTER CONTROL PANEL <<
# ======================================================================
STORY_CONCEPT = "A day in the life of Jax, our space ranger. The storyboard should show a mix of at least 5 scenes: 1. A quiet, reflective moment looking out a viewport. 2. An action scene where he is repairing the ship's exterior. 3. A tense moment on the command bridge. 4. Him discovering a strange alien artifact. 5. A final triumphant pose."
CHARACTER_NAME = "Jax"
NUMBER_OF_SHOTS = 5
GENERATED_SHOT_LIST_FILE = "output/ai_driven_storyboard/generated_shot_list.json"
# ======================================================================

def run_ai_storyboard_creation():
    """Orchestrates the AI planning and procedural execution workflow."""
    print("--- Initializing AI-Driven Storyboard Production ---")

    try:
        # --- PHASE 1: AI-DRIVEN SCENE GENERATION ---
        print("\n" + "="*70)
        print("--- PHASE 1: Generating Dynamic Shot List with AI... ---")
        
        result = generate_shot_list(
            prompt=STORY_CONCEPT,
            character_name=CHARACTER_NAME,
            num_shots=NUMBER_OF_SHOTS,
            output_path=GENERATED_SHOT_LIST_FILE
        )
        
        if "FAILED" in result or not os.path.exists(GENERATED_SHOT_LIST_FILE):
            raise RuntimeError(f"Critical failure in Phase 1. Could not generate shot list: {result}")

        print("\n--- ✅ AI Planning Complete. ---")

        # --- PHASE 2: PROCEDURAL STORYBOARD EXECUTION ---
        print("\n" + "="*70)
        print("--- PHASE 2: Executing Storyboard Generation with v4 Pipeline... ---")
        
        with open(GENERATED_SHOT_LIST_FILE, 'r') as f:
            shot_list = json.load(f)
        
        # Ensure character assets exist before starting the loop
        create_character_assets_if_needed()
        
        # Process each shot from the AI-generated list using the robust v4 workflow
        for shot_data in shot_list:
            process_shot(shot_data)

    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "="*70)
    print("--- ✅ AI-Driven Storyboard Production Complete. ---")

if __name__ == "__main__":
    run_ai_storyboard_creation()