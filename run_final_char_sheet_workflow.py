# run_final_char_sheet_workflow.py
# Definitive Version 3.0: The final, complete workflow orchestrator.
# It directs the AI to use the definitive 'split_and_layout_character_sheet' tool.
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
import google.genai.types as genai_types
from tools.tool_loader import ALL_TOOLS_SCHEMA, TOOL_REGISTRY
from tools.nyra_system_tools import make_directory, delete_file

# --- THE FINAL WORKFLOW SEQUENCE ---
FINAL_PROMPT_SEQUENCE = [
    # Step 1: Generate the single raw image with proper spacing instructions.
    ("Generate Raw 3-View Sheet", "Generate a single 16:9 image for a character sheet of 'Alina', a female sci-fi pilot. She wears a sleek, dark charcoal and navy blue flight suit. The image must contain three separate, full-body figures (front, side, and back) with significant empty white space between each figure. The background must be a plain white background. Use the 'imagen-4.0-ultra-generate-preview-06-06' model and save the raw image to 'output/final_char_sheet/alina_raw_sheet.png'."),
    
    # Step 2: Call the new, correct "splitter" tool.
    ("Split and Layout Sheet", "Take the raw sheet at 'output/final_char_sheet/alina_raw_sheet.png' and process it using the 'split_and_layout_character_sheet' tool. This will create three separate layout files. Save them into the 'output/final_char_sheet' directory."),

    # Step 3: Verify the three new, separate layout files were created.
    ("Verification", "List all files in 'output/final_char_sheet' to confirm the entire workflow was successful.")
]

SYSTEM_PROMPT = """
You are Nyra, an AI Art Director. Your task is to execute a two-step process to create production-ready character assets.
First, you will generate a single image containing three views of a character.
Second, you will use the 'split_and_layout_character_sheet' tool to segment this image and create three separate, finalized layout files.
You must report any failures immediately and stop.
"""

def run_final_workflow():
    project_dir = "output/final_char_sheet"
    print(f"--- Initializing Final Character Sheet Workflow ---")
    try:
        make_directory(project_dir)
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        config_params = genai_types.GenerateContentConfig(tools=[ALL_TOOLS_SCHEMA])
    except Exception as e:
        print(f"\nFATAL ERROR: Could not initialize: {e}"); return

    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "RULES UNDERSTOOD. I will execute the two-step generate-and-split workflow."}]}]

    for i, (desc, prompt) in enumerate(FINAL_PROMPT_SEQUENCE):
        print("\n" + "="*70)
        print(f"--- Running Step {i+1}/{len(FINAL_PROMPT_SEQUENCE)}: {desc} ---")
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
                if "OPERATION FAILED" in final_text:
                    print("\n--- WORKFLOW HALTED DUE TO REPORTED FAILURE ---")
                    return
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
                error_str = str(e)
                last_tool_result = f"Error: {error_str}"
                print(f"\033[91m[TOOL ERROR] > {error_str}\033[0m")
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'error': error_str}))]})
        
        if last_tool_result is None or "Failed" in str(last_tool_result):
             print("\n--- WORKFLOW HALTED DUE TO TOOL FAILURE ---")
             return
        time.sleep(2)

    print("\n" + "="*70)
    print("--- Final Character Sheet Workflow Complete ---")
    print("Cleanup complete.")

if __name__ == "__main__":
    run_final_workflow()