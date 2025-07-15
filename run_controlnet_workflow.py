# run_controlnet_workflow.py
# Definitive Version 3.0: Switched to cost-effective models (Gemini Flash, Imagen 3).

# --- Path Setup ---
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ---

import json
import time
import config
from google import genai
import google.genai.types as genai_types
from tools.tool_loader import ALL_TOOLS_SCHEMA, TOOL_REGISTRY
from tools.nyra_system_tools import make_directory

# --- DYNAMIC ASSET PATHS ---
POSE_REFERENCE_IMAGE_PATH = "output/controlnet_test/pose_ref_thumbs_up.png"
SKELETON_IMAGE_PATH = "output/controlnet_test/pose_skeleton.png"
FINAL_CHARACTER_IMAGE_PATH = "output/controlnet_test/alina_posed_thumbs_up.png"

# --- CORE PROMPT FOR THE CHARACTER ---
CHARACTER_CIP = "A photorealistic 3D cartoon character 'Alina', in the style of modern animation studios. She has large expressive eyes, sleek silver hair, and wears a dark, stylized flight suit. Plain white background."

# --- DEFINITIVE CONTROLNET TEST SEQUENCE ---
CONTROLNET_PROMPTS = [
    # 1. Generate the pose reference image using Imagen 3.
    ("Generate Pose Reference", f"Generate a full-body, photorealistic image of a generic, androgynous person standing and giving a clear thumbs-up with their right hand. The background must be a solid, uncluttered, light gray. Use the 'imagen-3.0-generate-002' model. Save it to '{POSE_REFERENCE_IMAGE_PATH}'."),

    # 2. Extract the skeleton from the newly generated pose reference.
    ("Extract Pose Skeleton", f"Analyze the pose reference image at '{POSE_REFERENCE_IMAGE_PATH}' and extract its OpenPose skeleton. Save the skeleton image to '{SKELETON_IMAGE_PATH}'."),

    # 3. Use the skeleton to generate the character in the correct pose using Imagen 3.
    ("Generate Posed Character", f"Generate an image of our character using this prompt: '{CHARACTER_CIP}'. Critically, apply the skeleton from '{SKELETON_IMAGE_PATH}' as a ControlNet input to force the character into a thumbs-up pose. Use model 'imagen-3.0-generate-002' and a 9:16 aspect ratio. Save to '{FINAL_CHARACTER_IMAGE_PATH}'."),

    # 4. Verification
    ("Verification", "List all files in 'output/controlnet_test' to confirm success.")
]

SYSTEM_PROMPT = "You are Nyra, an AI Art Director. Your task is to use a ControlNet workflow to generate a character in a specific pose. You will first generate a full-body pose reference image, extract its skeleton, then use that skeleton to guide the final image generation."

def run_controlnet_test():
    project_dir = "output/controlnet_test"
    print(f"--- Initializing Self-Contained ControlNet Workflow ---")
    try:
        make_directory(project_dir)
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        config_params = genai_types.GenerateContentConfig(tools=[ALL_TOOLS_SCHEMA])
    except Exception as e:
        print(f"\nFATAL ERROR: Could not initialize: {e}"); return
        
    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "RULES UNDERSTOOD. I will use cost-effective models and the ControlNet workflow."}]}]
    
    for i, (desc, prompt) in enumerate(CONTROLNET_PROMPTS):
        print("\n" + "="*70)
        print(f"--- Running Step {i+1}/{len(CONTROLNET_PROMPTS)}: {desc} ---")
        print(f"\033[92m[DIRECTOR] > {prompt}\033[0m")
        chat_history.append({'role': 'user', 'parts': [{'text': prompt}]})
        
        last_tool_result = None
        while True:
            # DEFINITIVE CHANGE: Using the cheaper gemini-2.5-flash model for orchestration.
            response = client.models.generate_content(model="gemini-2.5-flash", contents=chat_history, config=config_params)
            
            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                print(f"\033[91m[API ERROR] > Model returned an empty or blocked response.\033[0m"); return
            part = response.candidates[0].content.parts[0]
            if not hasattr(part, 'function_call') or not part.function_call:
                final_text = part.text
                chat_history.append({'role': 'model', 'parts': [{'text': final_text}]})
                print(f"\033[96m[NYRA] > {final_text}\033[0m")
                if "OPERATION FAILED" in final_text: print("\n--- WORKFLOW HALTED ---"); return
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
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'error': str(e)}))]})
        if last_tool_result is None or "Failed" in str(last_tool_result):
             print("\n--- WORKFLOW HALTED ---"); return
        time.sleep(2)
        
    print("\n" + "="*70)
    print("--- ControlNet Pose Consistency Workflow Complete ---")

if __name__ == "__main__":
    run_controlnet_test()