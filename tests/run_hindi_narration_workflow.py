# run_hindi_narration_workflow.py
# This corrected workflow uses the fully parameterized tool to generate
# a high-quality WAV audio file.

import os
import sys
from pathlib import Path
import time

# --- Path Setup & Global Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- SDK and Tool Imports ---
from google import genai
from tools.nyra_system_tools import make_directory
from tools.nyra_chirp3 import generate_speech

# ======================================================================
# >> NARRATION CONTROL PANEL <<
# ======================================================================

# --- Story Generation ---
STORY_TOPIC = "एक युवा कलाकार की भावनात्मक कहानी जो भोपाल से मुंबई अपने सपनों का पीछा करने आता है, चुनौतियों का सामना करता है लेकिन उम्मीद नहीं छोड़ता।"
AI_MODEL_FOR_STORY = "gemini-2.5-pro"

# --- Speech Synthesis ---
VOICE_NAME = "hi-IN-Chirp3-HD-Vindemiatrix"
OUTPUT_FILENAME = "emotional_hindi_story.wav" # Changed to WAV for LINEAR16

# --- Project Directory ---
PROJECT_DIR = Path(config.WORKSPACE_DIR) / "output/pure_hindi_narration"

# ======================================================================

def run_narration_workflow():
    """Orchestrates the AI story generation and speech synthesis workflow."""
    start_time = time.time()
    print("--- Initializing AI-Driven Pure Hindi Narration Workflow ---")
    
    try:
        make_directory(str(PROJECT_DIR))

        # --- PHASE 1: AI Story Generation (Pure Hindi) ---
        print("\n" + "="*80)
        print(f"--- PHASE 1: Generating Hindi Story from topic ---")
        
        genai_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        
        system_prompt = """
        You are an expert storyteller. Your task is to write a short, emotional story based on the user's topic.
        The story MUST be written entirely in pure, formal Hindi using Devanagari script.
        Do not use any English or Hinglish words.
        The tone should be emotional and slightly cinematic.
        Keep the story to about 3-4 short paragraphs.
        """
        
        prompt = f"Here is the topic: {STORY_TOPIC}"
        
        response = genai_client.models.generate_content(
            model=AI_MODEL_FOR_STORY,
            contents=[system_prompt, prompt]
        )
        
        story_text = response.text.strip()
        
        if not story_text:
            raise RuntimeError("AI failed to generate story text.")
            
        script_path = PROJECT_DIR / "generated_hindi_script.txt"
        script_path.write_text(story_text, encoding='utf-8')
        
        print(f"-> AI Storyteller Generated Script (saved to {script_path.name}):")
        print("-" * 60)
        print(story_text)
        print("-" * 60)

        # --- PHASE 2: Speech Synthesis ---
        print("\n" + "="*80)
        print(f"--- PHASE 2: Narrating story with voice '{VOICE_NAME}' ---")
        
        final_audio_path = PROJECT_DIR / OUTPUT_FILENAME
        
        narration_result = generate_speech(
            text_to_speak=story_text,
            output_path=str(final_audio_path),
            voice_name=VOICE_NAME,
            speaking_rate=0.95,
            sample_rate_hertz=44100 # Using the specified sample rate
        )
        
        if "FAILED" in str(narration_result):
            raise RuntimeError(f"Speech synthesis failed: {narration_result}")

    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    end_time = time.time()
    print("\n" + "="*80)
    print("--- ✅ Pure Hindi Narration Workflow Complete ---")
    print(f"--- Final audio narration available at: {final_audio_path} ---")
    print(f"--- Total execution time: {end_time - start_time:.2f} seconds ---")

if __name__ == "__main__":
    run_narration_workflow()