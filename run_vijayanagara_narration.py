# run_vijayanagara_narration.py
# A dedicated pipeline to generate high-quality audio narration
# from the approved 'vijayanagara_empire_script.txt' file.
# Version 2.0: Corrected to use the Long Audio API for scripts > 5000 bytes.

import os
import sys
import time
from pathlib import Path

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports (DEFINITIVE FIX) ---
from tools.nyra_system_tools import make_directory
from tools.nyra_long_audio import synthesize_long_audio # Use the long audio tool
from tools._helpers import download_from_gcs           # Add the GCS downloader helper

# ======================================================================
# >> NARRATION PRODUCTION CONTROL PANEL <<
# ======================================================================

# The final, director-approved script file.
INPUT_SCRIPT_PATH = "output/stylized_script_generator/vijayanagara_empire_script.txt"

# Audio generation settings
VOICE_NAME = "hi-IN-Chirp3-HD-Vindemiatrix"
SPEAKING_RATE = 0.98 # A slightly slower, more deliberate pace for documentary style.

# Output settings
PROJECT_DIR = Path(config.WORKSPACE_DIR) / "output/vijayanagara_production"
OUTPUT_FILENAME = "vijayanagara_narration_long_api.wav" # WAV for max quality

# DEFINITIVE FIX: Added a unique GCS URI for the Long Audio API output.
GCS_OUTPUT_URI = f"gs://{config.GCS_BUCKET_NAME}/long_audio_outputs/vijayanagara_{int(time.time())}.wav"
# ======================================================================

def run_narration_generation():
    """Executes the narration generation from the final script using the Long Audio API."""
    print("--- Initializing Long Audio Narration from Approved Script ---")
    
    try:
        make_directory(str(PROJECT_DIR))
        
        # --- PHASE 1: Load Final Script ---
        print(f" -> Loading final script from '{INPUT_SCRIPT_PATH}'...")
        script_file = Path(config.WORKSPACE_DIR) / INPUT_SCRIPT_PATH
        if not script_file.exists():
            raise FileNotFoundError(f"CRITICAL: The script file was not found at {script_file}")
            
        script_text = script_file.read_text(encoding='utf-8').strip()
        
        # --- PHASE 2: Generate Audio to GCS (DEFINITIVE FIX) ---
        print(f" -> Submitting Long Audio API request with voice '{VOICE_NAME}'...")
        
        gcs_path = synthesize_long_audio(
            text_to_synthesize=script_text,
            output_gcs_uri=GCS_OUTPUT_URI,
            voice_name=VOICE_NAME,
            speaking_rate=SPEAKING_RATE
        )
        if "FAILED" in str(gcs_path).upper():
            raise RuntimeError(f"Long audio synthesis tool failed: {gcs_path}")

        # --- PHASE 3: Download Final Audio from GCS (DEFINITIVE FIX) ---
        print(f" -> Downloading final audio from GCS to local workspace...")
        output_path = PROJECT_DIR / OUTPUT_FILENAME
        download_from_gcs(
            gcs_uri=gcs_path,
            output_path=str(output_path)
        )

    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "="*80)
    print("--- ✅ Narration Production Complete ---")
    print(f"--- Final narration audio available at: {output_path} ---")

if __name__ == "__main__":
    run_narration_generation()