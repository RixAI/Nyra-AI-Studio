# run_character_consistency_suite.py
# A new test suite to validate the AI's ability to create and use
# a "Digital Twin" for generating visually consistent storyboard images.
#
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
from tools.nyra_system_tools import delete_file

# --- THE CONSISTENCY TEST SEQUENCE ---
CONSISTENCY_PROMPT_SEQUENCE = [
    # Phase 1, Step 1: Establish the Core Identity Prompt (CIP)
    ("Define Character", "Let's begin. First, define a new character named 'Kaelen'. Create a detailed Core Identity Prompt for him. He is a rugged male space explorer, around 35 years old, with short, dark hair, a trimmed beard, and a small scar over his left eyebrow. He wears a practical, dark gray, high-tech jumpsuit with orange piping. Save this detailed prompt as 'output/consistency_test/kaelen_cip.txt'."),

    # Phase 1, Step 2: Generate the Master Reference Image
    ("Create Reference Image", "Now, read the CIP from 'kaelen_cip.txt'. Using that prompt, generate the master reference image. The image should be a photorealistic, full-body shot of Kaelen in a neutral T-pose against a plain white background with flat, even lighting. Save it as 'output/consistency_test/kaelen_master_ref.png' using the 'imagen-4.0-generate-preview-06-06' model and a '9:16' aspect ratio."),

    # Phase 2, Step 1: Create Storyboard Panel 1 (Background Swap)
    ("Panel 1: Scene Setting", "Excellent. Now create the first storyboard panel. Take the master reference image at 'output/consistency_test/kaelen_master_ref.png' and place Kaelen inside the cockpit of a dimly lit starship. The background should show stars streaming by a large viewport. Use the 'bgswap' edit mode and save the result as 'output/consistency_test/panel_01.png'."),

    # Phase 2, Step 2: Create Storyboard Panel 2 (Pose/Action Change)
    ("Panel 2: Action Pose", "For the second panel, let's change his pose. Using the master reference image at 'output/consistency_test/kaelen_master_ref.png' as the `subject_ref_path`, generate an image of Kaelen looking worried and pointing at a flashing red alert on a console. Use the 'subject' edit mode for this. Save the result as 'output/consistency_test/panel_02.png'."),

    # Phase 3: Verification
    ("Verification", "Perfect. The sequence is complete. As a final check, please list all the files in our 'output/consistency_test' directory.")
]

SYSTEM_PROMPT = """
You are Nyra, an AI Creative Director specializing in visual consistency.

Your instructions are absolute:
1.  **Digital Twin First:** Your primary workflow is to first establish a character's identity (their Core Identity Prompt and Master Reference Image).
2.  **Use the Anchor:** You will then use this Master Reference Image as the anchor for all subsequent image generations for that character.
3.  **Select the Right Tool:**
    * To place the character in a new scene, use the `edit_image` tool with `edit_mode='bgswap'`.
    * To change the character's pose or expression, use the `edit_image` tool with `edit_mode='subject'`, providing the master reference as the `subject_ref_path`.
4.  **Acknowledge Failure:** If any tool fails, you MUST report the failure and STOP. Do not proceed.
"""

def run_consistency_suite():
    """Initializes and runs the character consistency test suite."""
    project_dir = "output/consistency_test"
    print(f"--- Initializing Character Consistency Test Suite ---")
    try:
        # Setup
        if not os.path.exists(os.path.join(config.WORKSPACE_DIR, project_dir)):
             os.makedirs(os.path.join(config.WORKSPACE_DIR, project_dir))
        
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        config_params = genai_types.GenerateContentConfig(tools=[tool_schemas.ALL_TOOLS_SCHEMA])
    except Exception as e:
        print(f"\nFATAL ERROR: Could not initialize: {e}"); return

    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "INSTRUCTIONS UNDERSTOOD. I will follow the Digital Twin workflow to ensure character consistency."}]}]

    for i, (desc, prompt) in enumerate(CONSISTENCY_PROMPT_SEQUENCE):
        print("\n" + "="*70)
        print(f"--- Running Step {i+1}/{len(CONSISTENCY_PROMPT_SEQUENCE)}: {desc} ---")
        print(f"\033[92m[DIRECTOR] > {prompt}\033[0m")
        chat_history.append({'role': 'user', 'parts': [{'text': prompt}]})

        while True:
            response = client.models.generate_content(model="gemini-2.5-pro", contents=chat_history, config=config_params)
            
            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                print(f"\033[91m[API ERROR] > Model returned an empty or blocked response.\033[0m"); return

            part = response.candidates[0].content.parts[0]

            if not hasattr(part, 'function_call') or not part.function_call:
                final_text = part.text
                chat_history.append({'role': 'model', 'parts': [{'text': final_text}]})
                print(f"\033[96m[NYRA] > {final_text}\033[0m")
                break
            
            call = part.function_call; tool_name = call.name; tool_args = dict(call.args)
            print(f"\033[93m[NYRA ACTION] > Calling tool: {tool_name}({json.dumps(tool_args)})\033[0m")
            chat_history.append({'role': 'model', 'parts': [part]})
            
            try:
                tool_function = tool_schemas.TOOL_REGISTRY[tool_name]
                tool_result = tool_function(**tool_args)
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'result': str(tool_result)}))]})
                print(f"\033[94m[TOOL RESULT] > {tool_result}\033[0m")
            except Exception as e:
                error_str = str(e)
                print(f"\033[91m[TOOL ERROR] > {error_str}\033[0m")
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'error': error_str}))]})
        time.sleep(2)

    # Cleanup
    print("\n" + "="*70)
    print("--- Character Consistency Test Suite Complete ---")
    try:
        delete_file(project_dir)
        print("Cleanup complete.")
    except Exception as e:
        print(f"Cleanup failed: {e}")

if __name__ == "__main__":
    run_consistency_suite()