# tools/nyra_chirp3.py
# Definitive Version 12.0: Restores all supported parameters, including
# sample_rate_hertz, and sets encoding to LINEAR16 for max quality.

import argparse
from typing import Optional
from google.cloud import texttospeech
from ._helpers import resolve_path_in_workspace
from . import _schema_helper

VALID_VOICES = [
    "hi-IN-Chirp3-HD-Vindemiatrix",
    "en-US-Chirp3-HD-Charon"
]

def generate_speech(
    text_to_speak: str,
    output_path: str,
    voice_name: str,
    speaking_rate: Optional[float] = 1.0,
    volume_gain_db: Optional[float] = 0.0,
    sample_rate_hertz: Optional[int] = 44100
) -> str:
    """
    Generates high-definition speech from text with full controls for
    rate, volume, and sample rate. Outputs a WAV file.
    """
    print(f"\n[Tool: generate_speech] with voice '{voice_name}'")
    try:
        if not output_path.lower().endswith('.wav'):
            print(f"-> WARNING: Output path should be a .wav file for LINEAR16 encoding.")

        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)

        voice = texttospeech.VoiceSelectionParams(
            language_code='-'.join(voice_name.split('-')[:2]),
            name=voice_name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate_hertz,
            speaking_rate=speaking_rate,
            volume_gain_db=volume_gain_db
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        local_path = resolve_path_in_workspace(output_path)
        local_path.write_bytes(response.audio_content)
        
        message = f"Speech audio saved to {local_path}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        error_message = f"Failed to generate speech. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

# --- Tool Registration & CLI ---
_TOOL_FUNCTIONS = [generate_speech]
def get_tool_declarations(): return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry(): return {f.__name__: f for f in _TOOL_FUNCTIONS}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Google Cloud TTS Voice Generation with Full Controls")
    parser.add_argument("--text", required=True)
    parser.add_argument("--output_path", required=True)
    parser.add_argument("--voice_name", default=VALID_VOICES[0], choices=VALID_VOICES)
    parser.add_argument("--rate", type=float, default=1.0)
    parser.add_argument("--gain", type=float, default=0.0)
    parser.add_argument("--sample_rate", type=int, default=44100)
    
    args = parser.parse_args()
    generate_speech(
        text_to_speak=args.text,
        output_path=args.output_path,
        voice_name=args.voice_name,
        speaking_rate=args.rate,
        volume_gain_db=args.gain,
        sample_rate_hertz=args.sample_rate
    )