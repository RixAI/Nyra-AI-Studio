# run_post_production.py
# A focused test to validate the AI's ability to call the final video compilation tool.
# Corrected Version: Fixes the TypeError in the generate_content call.
import os
import sys
import json
import time

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

from google import genai
from google.genai import types as genai_types
from tools import tool_schemas

# --- Test Setup ---
VIDEO_CLIPS = ['output/final_film/shot_01.mp4', 'output/final_film/shot_02.mp4']
AUDIO_TRACK = 'output/final_film/main_theme.mp3'
FINAL_OUTPUT = 'output/final_film/final_movie_ai.mp4'

SYSTEM_PROMPT = "You are an AI post-production supervisor. Your only task is to assemble the provided media assets into a final film using the 'compile_final_video' tool."

def run_post_prod_test():
    """Initializes the client and runs a focused test on the video compilation tool."""
    print("--- Initializing AI Post-Production Test ---")
    client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
    config_params = genai_types.GenerateContentConfig(tools=[tool_schemas.ALL_TOOLS_SCHEMA])
    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "Understood. I am ready to compile the final film."}]}]
    
    # --- Execute Turn ---
    prompt = f"All assets are ready. Please compile the following video clips: {VIDEO_CLIPS} with the audio track '{AUDIO_TRACK}'. Save the final movie as '{FINAL_OUTPUT}'."
    print(f"\033[92m[DIRECTOR] > {prompt}\033[0m")
    chat_history.append({'role': 'user', 'parts': [{'text': prompt}]})
    
    # CORRECTED: Added keyword arguments 'model=' and 'contents='
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=chat_history,
        config=config_params
    )
    part = response.candidates[0].content.parts[0]

    if hasattr(part, 'function_call') and part.function_call.name == 'compile_final_video':
        call = part.function_call
        tool_args = dict(call.args)
        print(f"\033[93m[NYRA ACTION] > Calling tool: {call.name}({json.dumps(tool_args)})\033[0m")
        
        try:
            tool_function = tool_schemas.TOOL_REGISTRY[call.name]
            tool_result = tool_function(**tool_args)
            print(f"\033[94m[TOOL RESULT] > {tool_result}\033[0m")
        except Exception as e:
            print(f"\033[91m[TOOL ERROR] > {e}\033[0m")
    else:
        print("\033[91m[AI ERROR] > AI failed to call the compilation tool.\033[0m")

    print("\n--- Post-Production Test Complete ---")

if __name__ == "__main__":
    run_post_prod_test()