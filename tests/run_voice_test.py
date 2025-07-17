# run_voice_test.py
# A dedicated script to test the corrected voice generation tool.

import os
import sys

# --- Path Setup & Global Configuration ---
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Import ---
from tools.nyra_chirp3 import generate_speech

# ======================================================================
# >> TEST PARAMETERS <<
# ======================================================================
TEST_TEXT = "नमस्ते विशाल, यह अंतिम और सफल परीक्षण होना चाहिए।"
# The definitive, correct voice name from your list.
VOICE_TO_TEST = "hi-IN-Chirp3-HD-Vindemiatrix"
OUTPUT_PATH = "output/vindemiatrix_final_test.mp3"
# ======================================================================

def run_test():
    """Executes a single, direct call to the voice generation tool."""
    print("--- Initializing Definitive Voice Tool Test ---")
    
    try:
        generate_speech(
            text_to_speak=TEST_TEXT,
            output_path=OUTPUT_PATH,
            voice_name=VOICE_TO_TEST
        )
    except Exception as e:
        print(f"\n--- ❌ TEST FAILED ---")
        print(f"An error occurred: {e}")
        return

    print("\n--- ✅ TEST COMPLETE ---")
    print(f"--- Review the output file at: {OUTPUT_PATH} ---")


if __name__ == "__main__":
    run_test()