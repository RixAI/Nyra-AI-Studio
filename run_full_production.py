# run_full_production.py
# Definitive Version 3.3: Corrects a NameError in the audio generation loop.
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
from tools.nyra_system_tools import resolve_path_in_workspace

# --- The High-Level Idea for a 2-Minute Film ---
FILM_PROMPT = """
A 2-minute film titled 'Antariksh ka Phool' (The Flower of Space).
The story follows a lone Indian astronaut, Vikram, on a desolate red planet.
The film should have a lonely but hopeful mood.

Key Story Beats:
1. Arrival: Vikram's ship lands on Mars. He emerges, looking at the vast, empty landscape.
2. The Search: A montage of Vikram exploring, scanning, and finding nothing. Show his growing loneliness. This sequence should be longer, maybe 15-20 seconds.
3. The Discovery: He accidentally finds a hidden cave containing a single, glowing blue flower. His expression is one of pure wonder.
4. The Message: He scans the flower, confirming it's alive, and sends a hopeful message back to Earth.
"""

# --- System Prompt ---
SYSTEM_PROMPT = """
You are Nyra, an AI film director. You operate autonomously based on the user's 'DIRECTOR' prompts.

Your instructions are absolute:
1.  **Execute Directly:** When given a command to generate an asset, you MUST call the appropriate tool immediately.
2.  **Use Defaults:** For any tool parameters that are optional (like 'aspect_ratio'), you MUST use the tool's default value ('16:9') unless the user's prompt explicitly provides a different one. DO NOT ask for confirmation on default values.
3.  **Acknowledge Failure:** If a tool call results in an error, failure, or a 'None' response, you MUST report the exact failure and error message. You MUST NOT state or imply that the step was successful. After reporting a failure, STOP and wait for new instructions.
4.  **Follow the Plan:** Your first step is to create a Production Plan. After that, you will execute that plan shot-by-shot as prompted by the user.
"""

def run_production():
    """
    Orchestrates the entire production workflow using a strategic two-step planning process.
    """
    print("--- Nyra AI Studio: Strategic Film Production Initialized ---")
    try:
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        config_params = genai_types.GenerateContentConfig(tools=[tool_schemas.ALL_TOOLS_SCHEMA])
    except Exception as e:
        print(f"\nFATAL ERROR: Could not initialize: {e}"); return

    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "INSTRUCTIONS UNDERSTOOD. I will execute directives autonomously, use default parameters without confirmation, and report all failures accurately."}]}]

    def execute_turn(prompt_text: str):
        # This function remains the same as before...
        print("\n" + "="*70)
        print(f"\033[92m[DIRECTOR] > {prompt_text}\033[0m")
        chat_history.append({'role': 'user', 'parts': [{'text': prompt_text}]})
        
        while True:
            response = client.models.generate_content(model="gemini-2.5-pro", contents=chat_history, config=config_params)
            
            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                print(f"\033[91m[API ERROR] > Model returned an empty or blocked response. Aborting production.\033[0m")
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    print(f"   -> Prompt Feedback: {response.prompt_feedback}")
                if hasattr(response, 'candidates') and response.candidates and hasattr(response.candidates[0], 'finish_reason'):
                    print(f"   -> Finish Reason: {response.candidates[0].finish_reason.name}")
                return "STOP"

            part = response.candidates[0].content.parts[0]

            if not hasattr(part, 'function_call') or not part.function_call:
                final_text = part.text
                chat_history.append({'role': 'model', 'parts': [{'text': final_text}]})
                print(f"\033[96m[NYRA] > {final_text}\033[0m")
                return final_text
            
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

    # --- PRODUCTION EXECUTION ---
    if execute_turn("Let's create the project directory 'output/antariksh_ka_phool'.") == "STOP": return
    plan_path = "output/antariksh_ka_phool/production_plan.json"
    if execute_turn(f"The film concept is: '{FILM_PROMPT}'. Create the detailed production plan and save it to '{plan_path}'.") == "STOP": return
    
    if not os.path.exists(resolve_path_in_workspace(plan_path)):
        print("CRITICAL FAILURE: Production Plan was not created. Aborting production."); return

    with open(resolve_path_in_workspace(plan_path), 'r', encoding='utf-8') as f:
        production_plan = json.load(f)

    all_video_clips = []
    all_audio_clips = []
    for shot in production_plan['shots']:
        shot_num = shot['shot_number']
        video_prompt = shot['video_prompt']
        strategy = shot['generation_strategy']
        duration = shot['duration_seconds']
        
        output_clip_path = f"output/antariksh_ka_phool/shot_{shot_num:02d}.mp4"
        
        if strategy == "SINGLE_SHOT":
            prompt = f"Generate video for Shot {shot_num}: '{video_prompt}'. Duration: {min(duration, 8)}s. Model: 'veo-2.0-generate-001'. Save to '{output_clip_path}'."
            if execute_turn(prompt) == "STOP": return
        elif strategy == "EXTEND_SHOT":
            base_clip_path = f"output/antariksh_ka_phool/shot_{shot_num:02d}_base.mp4"
            prompt1 = f"Generate the FIRST PART of Shot {shot_num}: '{video_prompt}'. Duration: 8s. Model: 'veo-2.0-generate-001'. Save to '{base_clip_path}'."
            if execute_turn(prompt1) == "STOP": return
            
            prompt2 = f"Now, EXTEND the video for Shot {shot_num} at '{base_clip_path}' to create the final clip. The extension prompt is 'the astronaut continues his journey across the landscape'. Save the final extended clip as '{output_clip_path}'."
            if execute_turn(prompt2) == "STOP": return
        
        all_video_clips.append(output_clip_path)

        for i, layer in enumerate(shot['audio_layers']):
            layer_type = layer['layer_type']
            layer_prompt = layer['prompt']
            audio_path = f"output/antariksh_ka_phool/shot_{shot_num:02d}_audio_{i+1}_{layer_type.lower()}.mp3"
            
            if layer_type == "DIALOGUE":
                voice = layer.get('voice_name', 'hi-IN-Wavenet-D')
                # DEFINITIVE FIX: Replaced 'shot_name' with the correct variable 'shot_num'.
                audio_prompt = f"Generate DIALOGUE for Shot {shot_num}: '{layer_prompt}'. Voice: '{voice}'. Save to '{audio_path}'."
                if execute_turn(audio_prompt) == "STOP": return
            
            all_audio_clips.append(audio_path)

    if all_video_clips:
        final_output_path = "output/antariksh_ka_phool/final_film.mp4"
        compilation_prompt = f"All assets are generated. Compile these video clips: {all_video_clips} with these audio clips in order: {all_audio_clips}. Save the result as '{final_output_path}'."
        if execute_turn(compilation_prompt) == "STOP": return
    
    print("\n" + "="*70)
    print("--- 'Antariksh ka Phool' STRATEGIC PRODUCTION COMPLETE ---")

if __name__ == "__main__":
    run_production()