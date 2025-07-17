# run_image_edit_suite.py
#
# Definitive Final Version v2: The prompts for the edit steps are now
# brutally explicit about the full output path to prevent AI pathing errors.
#
import os
import sys
import json
import time

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

from google import genai
from google.genai import types as genai_types
from tools.tool_loader import ALL_TOOLS_SCHEMA, TOOL_REGISTRY
from tools.nyra_system_tools import make_directory, delete_file

# --- FINALIZED TEST SEQUENCE WITH EXPLICIT PATHS ---
IMAGE_EDIT_PROMPTS = [
    ("Generate Character", "Generate a photorealistic, full-body image of a female sci-fi explorer in a rugged silver suit. Save it as 'explorer.png' in our 'output/image_edit_test' directory. Use the 'imagen-4.0-generate-preview-06-06' model with a 16:9 aspect ratio."),

    # DEFINITIVE FIX: The output_path is now explicit and complete.
    ("Edit - Background Swap", "Take the 'explorer.png' image and swap the background to a dense, alien jungle at night using the 'bgswap' mode. Save the new image to the full path 'output/image_edit_test/explorer_jungle.png'."),

    # DEFINITIVE FIX: The output_path and subject_ref_path are now explicit and complete.
    ("Edit - Subject", "Now take the original image again. Use the file at 'output/image_edit_test/explorer.png' as the subject_ref_path to perform a subject edit. The prompt is 'a female explorer in a sleek, black carbon fiber suit'. Save the result to the full path 'output/image_edit_test/explorer_blacksuit.png'."),

    ("Final Check", "This looks great. Please list all the image files we created in the 'output/image_edit_test' directory.")
]

SYSTEM_PROMPT = """
SYSTEM_INSTRUCTION: You are Nyra, an AI creative partner. Follow instructions precisely.
You MUST use the correct model name and parameters for each tool call.
For any file paths in user prompts, you MUST use them exactly as provided. Do not shorten or alter them.

MODEL LIST:
- To generate an image, the 'model_name' must be one of: ['imagen-4.0-ultra-generate-preview-06-06', 'imagen-4.0-generate-preview-06-06', 'imagen-4.0-fast-generate-preview-06-06', 'imagen-3.0-generate-002', 'imagen-3.0-fast-generate-001']
- To edit an image, the 'model_name' is always 'imagen-3.0-capability-001'

IMAGE EDITING MODES:
- For the 'edit_image' tool, the 'edit_mode' parameter MUST be one of these exact strings: 'subject', 'style', 'scribble', 'bgswap', 'inpaint'.

GROUNDING INSTRUCTIONS:
- When a tool returns a result, you MUST base your response on the actual result.
- If a tool fails, acknowledge the failure and the error message clearly. Do not pretend it succeeded.
"""

def run_image_edit_test():
    """Initializes and runs the image editing test suite."""
    project_dir = "output/image_edit_test"
    print("--- Initializing Image Editing AI Test Suite (Definitive) ---")
    try:
        # Use the tool to make the directory to ensure consistency
        tool_function = TOOL_REGISTRY['make_directory']
        tool_function(path=project_dir)

        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        config_params = genai_types.GenerateContentConfig(tools=[ALL_TOOLS_SCHEMA])
    except Exception as e:
        print(f"\nFATAL ERROR: Could not initialize: {e}"); return

    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "System context understood. I will use file paths exactly as provided."}]}]

    for i, (desc, prompt) in enumerate(IMAGE_EDIT_PROMPTS):
        print("\n" + "="*70)
        print(f"--- Running Step {i+1}/{len(IMAGE_EDIT_PROMPTS)}: {desc} ---")
        print(f"\033[92m[USER PROMPT] > {prompt}\033[0m")
        chat_history.append({'role': 'user', 'parts': [{'text': prompt}]})

        while True:
            response = client.models.generate_content(model="gemini-2.5-pro", contents=chat_history, config=config_params)
            
            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                print(f"\033[91m[API ERROR] > Model returned an empty or blocked response.\033[0m"); return

            part = response.candidates[0].content.parts[0]

            if not hasattr(part, 'function_call') or not part.function_call:
                final_text = part.text
                chat_history.append({'role': 'model', 'parts': [{'text': final_text}]})
                print(f"\033[96m[AI RESPONSE] > {final_text}\033[0m")
                break
            
            call = part.function_call; tool_name = call.name; tool_args = dict(call.args)
            print(f"\033[93m[AI ACTION] > Calling tool: {tool_name}({json.dumps(tool_args)})\033[0m")
            chat_history.append({'role': 'model', 'parts': [part]})
            
            try:
                tool_function = TOOL_REGISTRY[tool_name]
                tool_result = tool_function(**tool_args)
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'result': str(tool_result)}))]})
                print(f"\03-3[94m[TOOL RESULT] > {tool_result}\033[0m")
            except Exception as e:
                error_str = str(e)
                print(f"\033[91m[TOOL ERROR] > {error_str}\033[0m")
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'error': error_str}))]})
        
        time.sleep(2)

    print("\n" + "="*70)
    print("--- Image Editing Test Suite Complete ---")
    try:
        delete_tool = TOOL_REGISTRY['delete_file']
        delete_tool(path=project_dir)
        print("Cleanup complete.")
    except Exception as e:
        print(f"Cleanup failed: {e}")

if __name__ == "__main__":
    run_image_edit_test()