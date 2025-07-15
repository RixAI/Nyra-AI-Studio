# test_image_edit_gcs_access.py
# A focused test to isolate the edit_image tool's access to GCS.

import os
import sys
import json
import time

# --- Path and Authentication Setup ---
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- SDK, Schema & Model Imports ---
from google import genai
from google.genai import types as genai_types
from tools import tool_schemas
from tools.nyra_system_tools import make_directory, delete_file
from tools.nyra_imagen_gen import generate_image # Import generate_image to create a test image
from tools.nyra_imagen_edit import edit_image # Import edit_image directly
from tools._helpers import resolve_path_in_workspace # CORRECTED: Import resolve_path_in_workspace from _helpers

# --- Test Parameters ---
PROJECT_DIR = "output/test_image_edit_gcs"
RAW_IMAGE_PATH = os.path.join(PROJECT_DIR, "test_raw_image.png")
EDITED_IMAGE_PATH = os.path.join(PROJECT_DIR, "test_edited_image.png")
IMAGEN_GEN_MODEL = "imagen-4.0-generate-preview-06-06" # A common image generation model
IMAGEN_EDIT_MODEL = "imagen-3.0-capability-001" # The dedicated image edit model

def run_gcs_access_test():
    print("--- Initializing GCS Access Test for edit_image tool ---")
    try:
        # 1. Setup: Create directory
        make_directory(PROJECT_DIR)
        
        # 2. Generate a simple image to be used as input for editing
        print("\n--- Step 1: Generating a raw image for editing ---")
        gen_prompt = "A red apple on a plain white background."
        generate_image(
            model_name=IMAGEN_GEN_MODEL,
            prompt=gen_prompt,
            output_path=RAW_IMAGE_PATH,
            aspect_ratio="1:1" # Use a simple aspect ratio
        )
        if not os.path.exists(resolve_path_in_workspace(RAW_IMAGE_PATH)): # CORRECTED: Use imported function
            print(f"\033[91m[TEST FAILED] Failed to generate initial image at {RAW_IMAGE_PATH}. Cannot proceed.\033[0m")
            return
        print(f"Generated test image: {RAW_IMAGE_PATH}")

        # 3. Attempt the problematic edit_image call (using subject mode for simplicity)
        print("\n--- Step 2: Attempting edit_image call with GCS access ---")
        edit_prompt = "A green apple on a plain white background." # Change color to verify edit
        
        # Call the edit_image function directly
        result = edit_image(
            edit_mode="subject",
            output_path=EDITED_IMAGE_PATH,
            prompt=edit_prompt,
            input_path=RAW_IMAGE_PATH, # Use input_path to force GCS upload for general editing
            subject_ref_path=RAW_IMAGE_PATH # Also use as subject_ref to trigger that path
        )

        if result and "FAILED" not in result and os.path.exists(resolve_path_in_workspace(EDITED_IMAGE_PATH)): # CORRECTED: Use imported function
            print(f"\n\033[92m--- TEST PASSED: edit_image successfully accessed GCS and completed the edit. ---\033[0m")
            print(f"Edited image saved to: {EDITED_IMAGE_PATH}")
        else:
            print(f"\n\033[91m--- TEST FAILED: edit_image encountered an error or did not complete. ---\033[0m")
            print(f"Result: {result}")
            print("Please check the console output for specific error messages (e.g., FAILED_PRECONDITION).")

    except Exception as e:
        print(f"\n\033[91mFATAL ERROR during test execution: {e}\033[0m")
    finally:
        # Cleanup
        print("\n--- Cleaning up test directories ---")
        delete_file(PROJECT_DIR)
        print("Cleanup complete.")

if __name__ == "__main__":
    run_gcs_access_test()