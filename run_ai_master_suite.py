# run_ai_master_suite.py
#
# Definitive & Final Version: Corrects the NameError by defining SYSTEM_PROMPT.
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
from tools.models import MODELS

# --- MASTER PROMPT SEQUENCE ---
MASTER_PROMPT_SEQUENCE = [
    ("Setup", "Let's begin a new project. First, create a directory for it named 'output/master_project'."),
    ("Gen Character", "Generate a photorealistic, full-body image of a female sci-fi explorer in a rugged silver suit. Save it as 'explorer.png' in our project directory using the 'imagen-4.0-generate-preview-06-06' model with a 16:9 aspect ratio."),
    ("Edit BG Swap", "Take the 'explorer.png' image and swap the background to a dense, alien jungle at night using the 'bgswap' mode. Save the new image as 'explorer_jungle.png' in the project directory."),
    ("Audio Music", "We need a theme. Compose a 20-second heroic orchestral score and save it to 'output/master_project/main_theme.mp3'."),
    ("Audio Speech", "Generate the explorer's log: 'Mission log, entry one. We have arrived.' Use the 'en-US-Chirp3-HD-Charon' voice and save it to 'output/master_project/log_entry.mp3'."),
    ("Video T2V", "Create an establishing shot: an 8-second video of a starship flying through a nebula. Use the 'veo-3.0-generate-preview' model and save to 'output/master_project/nebula_flyby.mp4'."),
    ("Video I2V", "Animate our character. Use the 'explorer.png' to create a 5-second video with the 'veo-2.0-generate-001' model. Save it as 'explorer_animated.mp4' in our project directory."),
    ("Setup for Frames", "Prepare for a frames-to-video test. Create a new directory 'output/master_project/frames'. Then, copy 'explorer.png' into the new frames directory three times, naming them 'frame_001.png', 'frame_002.png', and 'frame_003.png'."),
    ("Frames-to-Video", "Now, compile the images from the 'output/master_project/frames' directory into a 1-fps video named 'compiled.mp4' in our project folder."),
    ("Final List", "Excellent. For a final check, please list all files in 'output/master_project'.")
]

# CORRECTED: The SYSTEM_PROMPT variable is now defined before it is used.
SYSTEM_PROMPT = f"""
SYSTEM_INSTRUCTION: You are Nyra, an AI creative partner. Follow instructions precisely.
You MUST use the correct model name and parameters for each tool call.

MODEL LIST:
- To generate an image with 'generate_image', the 'model_name' must be one of: {MODELS['imagen_gen']}
- To edit an image with 'edit_image', the 'model_name' is always '{MODELS['imagen_edit'][0]}'
- To generate a Veo 3 video with 'generate_veo3_video', 'model_name' must be one of: {[m for m in MODELS["veo"] if "veo-3.0" in m]}
- For other video tools like 'generate_veo2_video', 'model_name' must be one of: {[m for m in MODELS["veo"] if "veo-2.0" in m]}

IMAGE EDITING MODES:
- For the 'edit_image' tool, the 'edit_mode' parameter MUST be one of these exact strings: 'subject', 'style', 'scribble', 'bgswap', 'inpaint'.

GROUNDING INSTRUCTIONS:
- When a tool returns a result, you MUST base your response on the actual result.
- If a tool fails, acknowledge the failure and the error message clearly. Do not pretend it succeeded.
"""

def run_master_suite():
    print("--- Initializing Nyra AI Master Validation Suite (Definitive) ---")
    try:
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        config_params = genai_types.GenerateContentConfig(tools=[tool_schemas.ALL_TOOLS_SCHEMA])
    except Exception as e:
        print(f"\nFATAL ERROR: Could not initialize the AI Brain: {e}"); return

    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "System context understood. I will adhere to all model and parameter constraints."}]}]

    for i, (desc, prompt) in enumerate(MASTER_PROMPT_SEQUENCE):
        print("\n" + "="*70)
        print(f"--- Running Step {i+1}/{len(MASTER_PROMPT_SEQUENCE)}: {desc} ---")
        print(f"\033[92m[USER PROMPT] > {prompt}\033[0m")
        chat_history.append({'role': 'user', 'parts': [{'text': prompt}]})

        while True:
            response = client.models.generate_content(model="gemini-2.5-pro", contents=chat_history, config=config_params)
            part = response.candidates[0].content.parts[0]

            if not hasattr(part, 'function_call') or not part.function_call:
                final_text = part.text
                chat_history.append({'role': 'model', 'parts': [{'text': final_text}]})
                print(f"\033[96m[AI RESPONSE] > {final_text}\033[0m")
                break
            
            call = part.function_call
            tool_name = call.name
            tool_args = dict(call.args)
            
            print(f"\033[93m[AI ACTION] > Calling tool: {tool_name}({json.dumps(tool_args)})\033[0m")
            chat_history.append({'role': 'model', 'parts': [part]})
            
            try:
                tool_function = tool_schemas.TOOL_REGISTRY[tool_name]
                tool_result = tool_function(**tool_args)
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'result': str(tool_result)}))]})
                print(f"\033[94m[TOOL RESULT] > {tool_result}\033[0m")
            except Exception as e:
                print(f"\033[91m[TOOL ERROR] > Execution failed for {tool_name}: {e}\033[0m")
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'error': str(e)}))]})

        time.sleep(2)

    print("\n" + "="*70)
    print("--- Master Validation Suite Complete ---")

if __name__ == "__main__":
    run_master_suite()