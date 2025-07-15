# tools/nyra_chirp3.py
import argparse
from google.cloud import texttospeech
from ._helpers import resolve_path_in_workspace
from .models import MODELS

# A list of high-quality voices for testing
VALID_VOICES = [
    "en-US-Chirp3-HD-Charon", # English Male
    "en-US-Standard-I",      # English Female
    "hi-IN-Wavenet-D",       # Hindi Male
    "hi-IN-Wavenet-C"        # Hindi Female
]

def generate_speech(text_to_speak: str, output_path: str, voice_name: str):
    """Generates high-definition speech from text."""
    print(f"\n[Tool: generate_speech] with voice '{voice_name}'")
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)
        voice = texttospeech.VoiceSelectionParams(language_code='-'.join(voice_name.split('-')[:2]), name=voice_name)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        local_path = resolve_path_in_workspace(output_path)
        local_path.write_bytes(response.audio_content)
        print(f"✅ SUCCESS: Speech saved to {local_path}")
        return str(local_path)
    except Exception as e:
        print(f"❌ FAILED: generate_speech. Error: {e}")
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chirp-3 Speech Generation")
    parser.add_argument("--text", required=True, help="The text to synthesize.")
    parser.add_argument("--output_path", required=True, help="Local path to save the MP3 file.")
    parser.add_argument("--voice_name", default=VALID_VOICES[0], choices=VALID_VOICES, help="The voice model to use.")
    args = parser.parse_args()
    generate_speech(args.text, args.output_path, args.voice_name)