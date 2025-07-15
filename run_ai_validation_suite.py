# run_ai_validation_suite.py
#
# Version 2.0: Injects a detailed system prompt with valid model names
# to prevent the AI from hallucinating incorrect parameters.
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

# --- AUTOMATED TEST SCRIPT ---
AUTOMATED_PROMPTS = [
    "First, create a new directory for this project called 'output/ai_project'.",
    "Excellent. Now, generate a photorealistic image of a sleek, futuristic motorcycle using the 'imagen-4.0-generate-preview-06-06' model. Save it in that new directory as 'moto.png'.",
    "Using that image we just made, create a 5-second video with the 'veo-2.0-generate-001' model. The output should be saved as 'moto.mp4' in the same folder.",
    "Great. Now, compose a 15-second rock music track with a heavy electric guitar riff. Save it as 'moto_theme.mp3' in our project folder.",
    "Perfect. Now generate the narration for the video. The text is: 'In a world of chrome and steel, the future of speed has arrived.' Save it as 'narration.mp3'.",
    "Okay, let's check our work. List all the files in our 'output/ai_project' directory.",
    "Looks good. Let's clean up. Please delete the original 'moto.png' image file.",
    "And for the final confirmation, list the files in the directory one last time."
]

# --- CORRECTED: New system prompt with explicit model context ---
SYSTEM_PROMPT = f"""
SYSTEM_INSTRUCTION: You are Nyra, an AI creative partner for a project. 
Follow the user's instructions step-by-step.
You MUST use the correct model name for each generative tool call.

Here is the list of available models for each tool:
- For 'generate_image', you must choose one of these: {MODELS['imagen_gen']}
- For 'generate_veo3_video', you must choose one of these: {[m for m in MODELS["veo"] if "veo-3.0" in m]}
- For 'generate_veo2_video', you must choose one of these: {[m for m in MODELS["veo"] if "veo-2.0" in m]}
- For 'generate_music', you must use this model: '{MODELS['lyria'][0]}'
- For 'generate_speech', you must use this model: '{MODELS['chirp'][0]}'

When a tool returns a result, you MUST base your response on the actual result, not your prior belief. If a tool fails, acknowledge the failure and the error message.
"""

def run_automated_chat_test():
    """
    Runs a fully automated, multi-turn chat session to test the AI's
    ability to use tools sequentially with proper context.
    """
    print("--- Initializing Automated AI Validation Suite (v2.0 with Model Context) ---")
    try:
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        config_params = genai_types.GenerateContentConfig(tools=[tool_schemas.ALL_TOOLS_SCHEMA])
    except Exception as e:
        print(f"\nFATAL ERROR: Could not initialize the AI Brain: {e}")
        return

    # Initialize Chat History with the new, detailed system prompt
    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "Understood. I have the list of valid models and will follow all instructions."}]}]

    for i, prompt in enumerate(AUTOMATED_PROMPTS):
        print("\n" + "="*50)
        print(f"--- Step {i+1}/{len(AUTOMATED_PROMPTS)} ---")
        print(f"\033[92m[USER PROMPT] > {prompt}\033[0m")
        chat_history.append({'role': 'user', 'parts': [{'text': prompt}]})

        while True:
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=chat_history,
                config=config_params
            )
            
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
                
                chat_history.append({
                    'role': 'user',
                    'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'result': str(tool_result)}))]
                })
                print(f"\033[94m[TOOL RESULT] > {tool_result}\033[0m")
            except Exception as e:
                print(f"\033[91m[TOOL ERROR] > Execution failed for {tool_name}: {e}\033[0m")
                chat_history.append({
                    'role': 'user',
                    'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'error': str(e)}))]
                })

        time.sleep(2)

    print("\n" + "="*50)
    print("--- Automated Validation Suite Complete ---")

if __name__ == "__main__":
    run_automated_chat_test()