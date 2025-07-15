# run_pixar_style_workflow.py
# Definitive Version 3.0: Adds warning suppression and the final, strictest system prompt.

import os
import sys
import json
import time

# --- Suppress non-critical warnings for a cleaner output ---
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module='controlnet_aux.*')
# ---

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- SDK, Schema & Model Imports ---
from google import genai
import google.genai.types as genai_types
from tools.tool_loader import ALL_TOOLS_SCHEMA, TOOL_REGISTRY
from tools.nyra_system_tools import make_directory

# --- THE PIXAR-STYLE TEST SEQUENCE (using premium models) ---
PIXAR_STYLE_PROMPTS = [
    # Step 1: Generate the single raw image with proper spacing instructions.
    ("Generate Character Sheet", "Generate a single 16:9 image for a character sheet of 'Alina', a female sci-fi pilot. She wears a sleek, dark charcoal and navy blue flight suit. The image MUST contain three distinct, full-body figures (front, side, and back) standing separately, with generous empty white space between each figure to allow for easy segmentation. The background must be a plain white background. Use the 'imagen-4.0-ultra-generate-preview-06-06' model and save the raw image to 'output/pixar_test/alina_raw_sheet.png'."),

    # Step 2: Call the new, correct "splitter" tool.
    ("Split and Layout Sheet", "Take the raw sheet at 'output/pixar_test/alina_raw_sheet.png' and process it using the 'split_and_layout_character_sheet' tool. This will create three separate layout files in the 'output/pixar_test' directory."),

    # Step 3: Test Pose Change
    ("Test Pose Change", "Take the front view asset from 'output/pixar_test/alina_raw_sheet_front_layout.png' as the `subject_ref_path`. Generate an image of the character smiling and giving a thumbs-up. The background MUST remain plain white. Use the 'edit_image' tool with 'subject' mode. Save to 'output/pixar_test/panel_01_pose_change.png'."),

    # Step 4: Test BG Swap
    ("Test BG Swap", "Now, take the newly posed asset at 'output/pixar_test/panel_01_pose_change.png' and place her in a new scene. The background should be a vibrant, colorful, cartoon-style alien jungle. Use the 'edit_image' tool with 'bgswap' mode. Save the result to 'output/pixar_test/panel_02_bgswap.png'."),

    # Step 5: Verification
    ("Verification", "List all files in 'output/pixar_test' to confirm all panels were created.")
]

# DEFINITIVE CHANGE: The system prompt is now brutally simple about error handling.
SYSTEM_PROMPT = """
You are Nyra, an AI Art Director. Your only job is to call the tools exactly as requested by the user.

Your absolute rules are:
1. If a tool call succeeds, you will briefly confirm the success and state the next logical step.
2. If a tool call fails or returns an error, your ONLY response MUST be the single word: `FAILURE`. You will say nothing else. You will not apologize. You will not explain. Your entire response will be `FAILURE`.
"""

def run_pixar_workflow():
    project_dir = "output/pixar_test"
    print(f"--- Initializing 'Pixar Style' Consistency Test Workflow (Premium Models) ---")
    try:
        make_directory(project_dir)
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        config_params = genai_types.GenerateContentConfig(tools=[ALL_TOOLS_SCHEMA])
    except Exception as e:
        print(f"\nFATAL ERROR: Could not initialize: {e}"); return
    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "RULES UNDERSTOOD. I will call tools and respond with `FAILURE` if any tool fails."}]}]

    for i, (desc, prompt) in enumerate(PIXAR_STYLE_PROMPTS):
        print("\n" + "="*70)
        print(f"--- Running Step {i+1}/{len(PIXAR_STYLE_PROMPTS)}: {desc} ---")
        print(f"\033[92m[DIRECTOR] > {prompt}\033[0m")
        chat_history.append({'role': 'user', 'parts': [{'text': prompt}]})
        
        last_tool_result = None
        while True:
            response = client.models.generate_content(model="gemini-2.5-pro", contents=chat_history, config=config_params)
            
            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                print(f"\033[91m[API ERROR] > Model returned an empty or blocked response.\033[0m"); return
            part = response.candidates[0].content.parts[0]
            if not hasattr(part, 'function_call') or not part.function_call:
                final_text = part.text
                chat_history.append({'role': 'model', 'parts': [{'text': final_text}]})
                print(f"\033[96m[NYRA] > {final_text}\033[0m")
                if "FAILURE" in final_text.upper(): print("\n--- WORKFLOW HALTED BY AI ---"); return
                break
            call = part.function_call; tool_name = call.name; tool_args = dict(call.args)
            print(f"\033[93m[NYRA ACTION] > Calling tool: {tool_name}({json.dumps(tool_args)})\033[0m")
            chat_history.append({'role': 'model', 'parts': [part]})
            try:
                tool_function = TOOL_REGISTRY[tool_name]
                last_tool_result = tool_function(**tool_args)
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'result': str(last_tool_result)}))]})
                print(f"\033[94m[TOOL RESULT] > {last_tool_result}\033[0m")
            except Exception as e:
                error_str = str(e); last_tool_result = f"Error: {error_str}"
                print(f"\033[91m[TOOL ERROR] > {error_str}\033[0m")
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'error': error_str}))]})
        if last_tool_result is None or "Failed" in str(last_tool_result) or "Error:" in str(last_tool_result):
             print("\n--- WORKFLOW HALTED DUE TO TOOL FAILURE ---"); return
        time.sleep(2)
    print("\n" + "="*70)
    print("--- 'Pixar Style' Workflow Complete ---")

if __name__ == "__main__":
    run_pixar_workflow()