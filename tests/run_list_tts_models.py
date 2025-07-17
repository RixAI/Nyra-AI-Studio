# run_list_all_voices.py
# A definitive diagnostic script to list all voices available to the project
# through the standard TextToSpeechClient, filtering for Wavenet and Chirp.

import os
import sys

# --- Path Setup & Global Configuration ---
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- SDK Import ---
from google.cloud import texttospeech

def generate_voice_report():
    """Queries the TTS API and prints a formatted list of available voices."""
    print(f"--- Querying Google Cloud TTS API for project '{config.PROJECT_ID}' ---")
    
    try:
        client = texttospeech.TextToSpeechClient()
        response = client.list_voices()
        
        wavenet_voices = []
        chirp_voices = []
        
        for voice in response.voices:
            voice_info = {
                "name": voice.name,
                "language": voice.language_codes[0],
                "gender": texttospeech.SsmlVoiceGender(voice.ssml_gender).name
            }
            if "Wavenet" in voice.name:
                wavenet_voices.append(voice_info)
            elif "Chirp" in voice.name:
                chirp_voices.append(voice_info)

        print("\n" + "="*80)
        print(f"### Voice Availability Report for Project: {config.PROJECT_ID} ###")
        print("="*80)

        print("\n--- [ Wavenet Voices ] ---")
        if wavenet_voices:
            for v in sorted(wavenet_voices, key=lambda x: x['name']):
                print(f"  > Name: {v['name']:<25} | Language: {v['language']:<10} | Gender: {v['gender']}")
        else:
            print("  No Wavenet voices found.")
            
        print("\n--- [ Chirp3 HD Voices ] ---")
        if chirp_voices:
            for v in sorted(chirp_voices, key=lambda x: x['name']):
                print(f"  > Name: {v['name']:<25} | Language: {v['language']:<10} | Gender: {v['gender']}")
        else:
            print("  No Chirp3 HD voices were found for your project via the standard Text-to-Speech API.")
            
        print("\n" + "="*80)

    except Exception as e:
        print(f"\n--- ❌ QUERY FAILED ---")
        print(f"An error occurred while trying to list voices: {e}")
        return

if __name__ == "__main__":
    generate_voice_report()