# run_stylized_narration_generator.py
# A workflow to generate a narration script in a specific, consistent
# documentary style using the new 'generate_documentary_script' tool.

import os
import sys
from pathlib import Path

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports ---
from tools.nyra_system_tools import make_directory
from tools.nyra_storyboarder import generate_documentary_script # Import the new tool

# ======================================================================
# >> SCRIPT GENERATION CONTROL PANEL <<
# ======================================================================

# Simply change the topic here to get a new script in the same style.
NEW_TOPIC = "The rise and fall of the Vijayanagara Empire."
OUTPUT_LANGUAGE = "Hindi" # Or "English", etc. The tool is now flexible.

PROJECT_DIR = Path(config.WORKSPACE_DIR) / "output/stylized_script_generator"
OUTPUT_SCRIPT_PATH = PROJECT_DIR / "vijayanagara_empire_script.txt"

# ======================================================================

def run_script_generation():
    """Executes the stylized script generation workflow."""
    print("--- Initializing Stylized Narration Script Generator ---")
    
    try:
        make_directory(str(PROJECT_DIR))

        # Call the new tool with only the topic. The tool handles the style.
        script_content = generate_documentary_script(
            topic=NEW_TOPIC,
            language=OUTPUT_LANGUAGE
        )
        
        if "FAILED" in script_content:
            raise RuntimeError(f"Script generation failed: {script_content}")
            
        # Save the generated script to a file
        OUTPUT_SCRIPT_PATH.write_text(script_content, encoding='utf-8')

    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "="*80)
    print("--- ✅ Stylized Script Generation Complete ---")
    print(f"--- New script with the requested style saved to: {OUTPUT_SCRIPT_PATH} ---")

if __name__ == "__main__":
    run_script_generation()