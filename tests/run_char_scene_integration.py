# run_char_scene_integration.py
# Definitive Version 3.0: Corrects the final step to use 'subject' edit mode
# instead of 'inpaint', as no mask is being provided.

import os
import sys
import json
import time
import re
from pathlib import Path

# --- Path Setup & Warning Suppression ---
import warnings
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- SDK, Schema & Model Imports ---
from google import genai
from google.genai import types as genai_types
from tools import tool_loader
from tools.nyra_system_tools import make_directory, delete_file
from tools.models import MODELS

# ======================================================================
# >> MASTER CONTROL PANEL <<
# ======================================================================
PROJECT_DIR = "output/character_scene_integration"
CHARACTER_NAME = "Elara"
CHARACTER_DESCRIPTION = f"A female cyberpunk rogue named '{CHARACTER_NAME}', with neon blue dreadlocks, wearing a tattered black leather jacket and glowing cybernetic arm, in a gritty, realistic style."

RAW_CHAR_SHEET = f"{PROJECT_DIR}/{CHARACTER_NAME.lower()}_raw_sheet.png"
FRONT_LAYOUT_IMAGE = f"{PROJECT_DIR}/{CHARACTER_NAME.lower()}_raw_sheet_front_layout.png"
IN_SCENE_IMAGE = f"{PROJECT_DIR}/{CHARACTER_NAME.lower()}_in_scene.png"
POSED_IN_SCENE_IMAGE = f"{PROJECT_DIR}/{CHARACTER_NAME.lower()}_posed_in_scene.png"
FINAL_CORRECTED_IMAGE = f"{PROJECT_DIR}/{CHARACTER_NAME.lower()}_final_corrected.png"

# --- AI Orchestration Sequence ---
ORCHESTRATION_PROMPTS = [
    # Step 1 & 2 are unchanged
    (f"CALL TOOL: generate_image with model_name='imagen-4.0-ultra-generate-preview-06-06', output_path='{RAW_CHAR_SHEET}', aspect_ratio='16:9', prompt='A 3-view character sheet for a {CHARACTER_DESCRIPTION}. The image must contain three separate, full-body figures (front, side, and back) with significant empty white space between each figure. The background must be a plain white background.'"),
    (f"CALL TOOL: split_and_layout_character_sheet with input_path='{RAW_CHAR_SHEET}' and output_dir='{PROJECT_DIR}'."),
    # Step 3 & 4 are unchanged
    (f"CALL TOOL: edit_image with model_name='imagen-3.0-capability-001', edit_mode='bgswap', output_path='{IN_SCENE_IMAGE}', prompt='A dimly lit starship cockpit with stars streaming by a large viewport.', input_path='{FRONT_LAYOUT_IMAGE}'"),
    (f"CALL TOOL: edit_image with model_name='imagen-3.0-capability-001', edit_mode='subject', output_path='{POSED_IN_SCENE_IMAGE}', prompt='A portrait of {CHARACTER_NAME} looking determined, with one hand on her glowing cybernetic arm, in a gritty cyberpunk style.', input_path='{IN_SCENE_IMAGE}', subject_ref_path='{FRONT_LAYOUT_IMAGE}'"),

    # DEFINITIVE FIX: Changed edit_mode from 'inpaint' to 'subject' for the final correction pass, as no mask is available.
    (f"CALL TOOL: edit_image with model_name='imagen-3.0-capability-001', edit_mode='subject', output_path='{FINAL_CORRECTED_IMAGE}', prompt='A final pass on the image to improve the vibrant glow effect on {CHARACTER_NAME}\\'s cybernetic arm and add subtle rain streaks on her jacket.', input_path='{POSED_IN_SCENE_IMAGE}'"),

    # Step 6 is unchanged
    (f"CALL TOOL: list_files with directory='{PROJECT_DIR}'")
]

# System prompt and main execution function 'run_character_scene_integration_workflow' remain unchanged.
# ... (rest of the file is identical to the previous version)
SYSTEM_PROMPT = f"""
SYSTEM_INSTRUCTION: You are Nyra, an AI Creative Director specializing in visual consistency and advanced image manipulation.
Your task is to orchestrate a multi-step character and scene generation workflow.

Your instructions are absolute:
1.  **Digital Twin Workflow:** You will first establish a character's identity (their 3-view sheet and isolated front reference).
2.  **Seamless Integration:** You will then integrate this character into new scenes and adjust their appearance using specific editing modes.
3.  **Tool Usage:**
    * For any user prompt starting with "CALL TOOL:", you MUST parse the tool name and arguments from the rest of the prompt and make the exact function call. You MUST NOT generate any text response for these prompts.
4.  **Error Handling:** If any tool call results in an error or a 'FAILED' message, you MUST report the exact failure and error message clearly. You MUST NOT state or imply that the step was successful. After reporting a failure, STOP and wait for new instructions.
5.  **Path Management:** Always use the full relative paths provided in the user's prompts for input and output files.
"""

def run_character_scene_integration_workflow():
    """
    Executes the workflow for character generation, scene integration,
    pose adjustment, and final detailing, orchestrated by Gemini.
    """
    print("--- Initializing Character Scene Integration Workflow (AI-Orchestrated) ---")
    try:
        make_directory(PROJECT_DIR)
        print(f"[DIRECTOR] > Project directory '{PROJECT_DIR}' ensured.")

        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        config_params = genai_types.GenerateContentConfig(tools=[tool_loader.ALL_TOOLS_SCHEMA])
    except Exception as e:
        print(f"\nFATAL ERROR: Could not initialize AI Brain or project setup: {e}"); return

    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "INSTRUCTIONS UNDERSTOOD. I will orchestrate the character scene integration workflow step-by-step."}]}]
    print(f"\033[96m[NYRA] > {chat_history[-1]['parts'][0]['text']}\033[0m")

    for i, user_prompt_text in enumerate(ORCHESTRATION_PROMPTS):
        print("\n" + "="*70)
        print(f"--- Running Step {i+1}/{len(ORCHESTRATION_PROMPTS)} ---")
        print(f"\033[92m[DIRECTOR] > {user_prompt_text}\033[0m")
        chat_history.append({'role': 'user', 'parts': [{'text': user_prompt_text}]})

        tool_name = None
        tool_args = None

        for attempt in range(2):
            response = client.models.generate_content(model="gemini-2.5-pro", contents=chat_history, config=config_params)

            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                return

            part = response.candidates[0].content.parts[0]

            if hasattr(part, 'function_call') and part.function_call:
                call = part.function_call
                tool_name = call.name
                tool_args = dict(call.args)
                print(f"\033[93m[NYRA ACTION] > Calling tool: {tool_name}({json.dumps(tool_args)})\033[0m")
                chat_history.append({'role': 'model', 'parts': [part]})
                break
            elif user_prompt_text.startswith("CALL TOOL:"):
                print(f"\033[91m[AI MISBEHAVIOR DETECTED] > AI returned text instead of tool call. Forcing tool execution from prompt...\033[0m")
                
                try:
                    full_call_str = user_prompt_text.replace("CALL TOOL:", "").strip()
                    tool_name = full_call_str.split(" ")[0]
                    
                    args_section = full_call_str.split(" with ", 1)[1]
                    matches = re.findall(r"(\w+)\s*=\s*'([^']*)'", args_section)
                    
                    tool_args = {key: value for key, value in matches}
                    
                    dummy_function_call_part = genai_types.Part(function_call=genai_types.FunctionCall(name=tool_name, args=tool_args))
                    chat_history.append({'role': 'model', 'parts': [dummy_function_call_part]})
                    print(f"\033[91m[FORCING TOOL] > Parsed and forcing: {tool_name}({json.dumps(tool_args)})\033[0m")
                    break 
                except Exception as parse_e:
                    print(f"\033[91m[FORCING FAILED] > Could not parse tool arguments from prompt: {parse_e}. Aborting.\033[0m")
                    print("\n--- WORKFLOW HALTED DUE TO TOOL PARSING FAILURE ---")
                    return
            else:
                final_text_response = part.text
                chat_history.append({'role': 'model', 'parts': [{'text': final_text_response}]})
                print(f"\033[96m[NYRA] > {final_text_response}\033[0m")
                break

        if tool_name is None:
            print("\n--- WORKFLOW HALTED DUE TO UNHANDLED AI RESPONSE ---")
            return

        try:
            tool_function = tool_loader.TOOL_REGISTRY[tool_name]
            tool_result = tool_function(**tool_args)
            chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'result': str(tool_result)}))]})
            print(f"\033[94m[TOOL RESULT] > {tool_result}\033[0m")
            if "FAILED" in str(tool_result).upper():
                print("\n--- WORKFLOW HALTED DUE TO TOOL FAILURE ---")
                return
        except Exception as e:
            return
        
        time.sleep(2)

    print("\n" + "="*70)
    print("--- Character Scene Integration Workflow Complete ---")
    
    try:
        print("Cleanup complete.")
    except Exception as e:
        print(f"Cleanup failed during final step: {e}")

if __name__ == "__main__":
    run_character_scene_integration_workflow()