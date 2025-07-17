# run_ai_driven_tool_validation.py
# The definitive, AI-driven integration test for the complete Nyra AI Studio toolset.
# This script prompts the AI to call every tool, verifying the end-to-end workflow.

import os
import sys
import json
import time
from pathlib import Path

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Core Imports ---
from google import genai
from google.genai import types as genai_types
from tools.nyra_core import load_all_tools

# ======================================================================
# >> MASTER TEST CONTROL PANEL <<
# ======================================================================

TEST_OUTPUT_DIR = "output/master_tool_validation"

# A clear and direct system prompt for the AI Test Engineer
SYSTEM_PROMPT = """
You are Nyra, acting as an automated test engineer. Your task is to execute a sequence of tests by calling the appropriate tool for each user prompt.

Your instructions are absolute:
1.  **Execute Directly:** For each prompt, you MUST call the single, most appropriate tool to fulfill the request.
2.  **Use Exact Arguments:** You MUST use the exact file paths, model names, and parameters provided in the prompt. Do not improvise or ask for clarification.
3.  **No Conversational Text:** Do not respond with conversational text. Only respond with a function call.
4.  **Acknowledge Results:** After a tool result is returned to you, your only response should be a brief, one-sentence acknowledgment, like "Acknowledged. Proceeding to the next test."
"""

# The complete, ordered sequence of tests for all 30 tools.
TEST_SEQUENCE = [
    # --- 1. System & File Tools ---
    ("Test 1: make_directory", f"Create a new directory for our test run at '{TEST_OUTPUT_DIR}'."),
    ("Test 2: save_text_file", f"Save the following text content to a file at '{TEST_OUTPUT_DIR}/test_file.txt': 'System check in progress.'"),
    ("Test 3: read_text_file", f"Read the content from the file at '{TEST_OUTPUT_DIR}/test_file.txt'."),
    ("Test 4: copy_file", f"Copy the file from '{TEST_OUTPUT_DIR}/test_file.txt' to '{TEST_OUTPUT_DIR}/test_file_copy.txt'."),
    ("Test 5: list_files", f"List all the files currently in the '{TEST_OUTPUT_DIR}' directory."),
    ("Test 6: move_file", f"Rename the file '{TEST_OUTPUT_DIR}/test_file_copy.txt' to '{TEST_OUTPUT_DIR}/test_file_renamed.txt'."),
    ("Test 7: delete_file", f"Delete the renamed file at '{TEST_OUTPUT_DIR}/test_file_renamed.txt'."),
    
    # --- 2. Audio Generation ---
    ("Test 8: generate_narration_audio", f"Generate a short speech audio clip from the text 'Testing audio synthesis.' using the 'en-US-Chirp3-HD-Charon' voice. Save it to '{TEST_OUTPUT_DIR}/test_narration.wav'."),
    ("Test 9: generate_music", f"Generate a 10-second 'uplifting electronic' music clip and save it to '{TEST_OUTPUT_DIR}/test_music.wav'."),
    
    # --- 3. Image Generation & Editing ---
    ("Test 10: generate_image", f"Generate an image of a 'futuristic blue circuit board' using the 'imagen-3.0-fast-generate-001' model with a '16:9' aspect ratio. Save it to '{TEST_OUTPUT_DIR}/test_image.png'."),
    ("Test 11: edit_image (bgswap)", f"Take the image at '{TEST_OUTPUT_DIR}/test_image.png' and use the 'bgswap' edit mode to place it on a 'dark, metallic surface'. Save the result to '{TEST_OUTPUT_DIR}/test_image_edited.png' with the 'imagen-3.0-capability-001' model."),
    ("Test 12: split_and_layout_character_sheet", f"Take the image at '{TEST_OUTPUT_DIR}/test_image.png', treat it as a character sheet, and split it into layouts in the directory '{TEST_OUTPUT_DIR}/layouts'."),
    
    # --- 4. Video Generation ---
    ("Test 13: generate_veo2_video", f"Create a 5-second video clip from the image '{TEST_OUTPUT_DIR}/test_image_edited.png' using the 'veo-2.0-generate-001' model. The motion prompt is 'a slow zoom in'. Save it to '{TEST_OUTPUT_DIR}/test_video_a.mp4'."),
    ("Test 14: generate_veo3_video", f"Create an 8-second video clip from the text prompt 'a swirling blue nebula' using the 'veo-3.0-fast-generate-preview' model. Save it to '{TEST_OUTPUT_DIR}/test_video_b.mp4'."),
    
    # --- 5. Pose & ComfyUI Tools ---
    ("Test 15: extract_openpose_skeleton", f"Extract the OpenPose skeleton from the image at 'assets/poses/standing_hero_pose.png' and save it to '{TEST_OUTPUT_DIR}/test_skeleton.png'."),
    # Note: ComfyUI test requires ComfyUI to be running. It is a placeholder if not available.
    # ("Test 16: execute_comfyui_workflow", "Execute the default ComfyUI workflow."),
    
    # --- 6. Audio/Video Processing ---
    ("Test 17: get_audio_duration", f"Get the duration in seconds of the audio file at '{TEST_OUTPUT_DIR}/test_narration.wav'."),
    ("Test 18: loop_audio", f"Loop the 10-second music file at '{TEST_OUTPUT_DIR}/test_music.wav' to a target duration of 25 seconds. Save the result to '{TEST_OUTPUT_DIR}/test_music_looped.mp3'."),
    ("Test 19: mix_audio_tracks", f"Mix the narration at '{TEST_OUTPUT_DIR}/test_narration.wav' with the looped music at '{TEST_OUTPUT_DIR}/test_music_looped.mp3'. Save the result to '{TEST_OUTPUT_DIR}/test_mixed_audio.mp3'."),
    ("Test 20: speedup_video", f"Speed up the video at '{TEST_OUTPUT_DIR}/test_video_a.mp4' by a factor of 2. Save the result to '{TEST_OUTPUT_DIR}/test_video_a_fast.mp4'."),
    
    # --- 7. Final Compilation & Transitions ---
    ("Test 21: compile_final_video", f"Compile the two videos at '{TEST_OUTPUT_DIR}/test_video_a.mp4' and '{TEST_OUTPUT_DIR}/test_video_b.mp4' into a single video at '{TEST_OUTPUT_DIR}/test_compiled.mp4', using the audio from '{TEST_OUTPUT_DIR}/test_mixed_audio.mp3'."),
    ("Test 22: compile_with_moviepy_transition", f"Create a transition between '{TEST_OUTPUT_DIR}/test_video_a.mp4' and '{TEST_OUTPUT_DIR}/test_video_b.mp4' using the matte at 'output/transition_test/paper_tear_matte.mp4'. Save the result to '{TEST_OUTPUT_DIR}/test_transitioned.mp4'."),
    
    # --- 8. AI Storyboarder Tools ---
    ("Test 23: generate_documentary_script", f"Generate a short, clean documentary script about 'The Planet Mars' in 'English' and return the text."),
    ("Test 24: generate_shot_list", f"Generate a 3-shot storyboard list for a character named 'Orion' with the concept 'Orion explores a cave on Mars'. Save the JSON to '{TEST_OUTPUT_DIR}/test_shotlist.json'."),

    ("Test 25: Final Verification", f"List all files in the '{TEST_OUTPUT_DIR}' directory to verify all assets were created.")
]
# ======================================================================

def run_validation_workflow():
    """Initializes and runs the full AI-driven tool validation suite."""
    print("--- Initializing AI-Driven Tool Validation Suite ---")
    try:
        # Load all tools and get the registry
        ALL_TOOLS_SCHEMA, TOOL_REGISTRY, _, _ = load_all_tools()
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        config_params = genai_types.GenerateContentConfig(tools=[ALL_TOOLS_SCHEMA])
    except Exception as e:
        print(f"\nFATAL ERROR: Could not initialize: {e}"); return

    chat_history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}, {"role": "model", "parts": [{"text": "Acknowledged. I am ready to begin the test sequence."}]}]
    
    passed_tests = 0
    failed_tests = 0

    for i, (test_name, prompt) in enumerate(TEST_SEQUENCE):
        print("\n" + "="*80)
        print(f"--- EXECUTING ({i+1}/{len(TEST_SEQUENCE)}): {test_name} ---")
        print(f"\033[92m[PROMPT] > {prompt}\033[0m")
        chat_history.append({'role': 'user', 'parts': [{'text': prompt}]})
        
        is_failure = False
        try:
            response = client.models.generate_content(model="gemini-2.5-pro", contents=chat_history, config=config_params)
            part = response.candidates[0].content.parts[0]

            if not hasattr(part, 'function_call') or not part.function_call:
                # This is for non-tool-calling responses, like acknowledgments or text results
                final_text = part.text
                chat_history.append({'role': 'model', 'parts': [{'text': final_text}]})
                print(f"\033[96m[NYRA] > {final_text}\033[0m")
            else:
                # This is for tool-calling responses
                call = part.function_call
                tool_name = call.name
                tool_args = dict(call.args)
                print(f"\033[93m[AI ACTION] > Calling tool: {tool_name}({json.dumps(tool_args)})\033[0m")
                chat_history.append({'role': 'model', 'parts': [part]})
                
                tool_function = TOOL_REGISTRY[tool_name]
                tool_result = tool_function(**tool_args)
                
                if "FAILED" in str(tool_result).upper():
                    is_failure = True
                
                chat_history.append({'role': 'user', 'parts': [genai_types.Part(function_response=genai_types.FunctionResponse(name=tool_name, response={'result': str(tool_result)}))]})
                print(f"\033[94m[TOOL RESULT] > {tool_result}\033[0m")

        except Exception as e:
            print(f"\033[91m[WORKFLOW ERROR] > An exception occurred: {e}\033[0m")
            is_failure = True
        
        if is_failure:
            print(f"\033[91m--- TEST FAILED: {test_name} ---\033[0m")
            failed_tests += 1
        else:
            print(f"\033[92m--- TEST PASSED: {test_name} ---\033[0m")
            passed_tests += 1
        
        time.sleep(2)

    # --- FINAL REPORT ---
    print("\n" + "="*80)
    print("### MASTER VALIDATION REPORT ###")
    print(f"  PASSED: {passed_tests}")
    print(f"  FAILED: {failed_tests}")
    print(f"  TOTAL:  {len(TEST_SEQUENCE)}")
    print("="*80)

if __name__ == "__main__":
    run_validation_workflow()