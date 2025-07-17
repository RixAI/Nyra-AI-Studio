# tools/nyra_audio_tool.py
# A unified, intelligent tool for all audio generation, including
# speech synthesis (TTS) and music.

import os
import sys
import time
import argparse
import base64
import requests
from typing import Optional

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from .nyra_core import (
    resolve_path_in_workspace, 
    download_from_gcs, 
    MODELS, 
    create_function_declaration
)

# --- Dependency Imports ---
from google.cloud import texttospeech
import google.auth
import google.auth.transport.requests

# ======================================================================
# --- TOOL: UNIFIED SPEECH SYNTHESIS ---
# ======================================================================
STANDARD_API_BYTE_LIMIT = 5000

def generate_narration_audio(
    text_to_speak: str,
    output_path: str,
    voice_name: str,
    speaking_rate: Optional[float] = 1.0,
    volume_gain_db: Optional[float] = 0.0,
    sample_rate_hertz: Optional[int] = 44100
) -> str:
    """
    Generates speech from text using the optimal Google Cloud TTS API.
    Automatically switches to the Long Audio API for texts over 5000 bytes.
    The final output is always saved to the local 'output_path'.
    """
    print(f"\n[Tool: generate_narration_audio] with voice '{voice_name}'")
    
    text_bytes = text_to_speak.encode('utf-8')
    if len(text_bytes) <= STANDARD_API_BYTE_LIMIT:
        print(f" -> Text is under {STANDARD_API_BYTE_LIMIT} bytes. Using standard API.")
        try:
            client = texttospeech.TextToSpeechClient()
            synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)
            voice = texttospeech.VoiceSelectionParams(language_code='-'.join(voice_name.split('-')[:2]), name=voice_name)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate_hertz,
                speaking_rate=speaking_rate,
                volume_gain_db=volume_gain_db
            )
            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
            local_path = resolve_path_in_workspace(output_path)
            local_path.write_bytes(response.audio_content)
            
            message = f"Speech audio saved to {local_path}"
            print(f"✅ SUCCESS: {message}")
            return str(local_path)
        except Exception as e:
            error_message = f"Failed to generate speech with standard API. Error: {e}"
            print(f"❌ FAILED: {error_message}")
            return error_message
            
    else:
        print(f" -> Text is over {STANDARD_API_BYTE_LIMIT} bytes. Using Long Audio API.")
        try:
            client = texttospeech.TextToSpeechLongAudioSynthesizeClient()
            synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)
            voice = texttospeech.VoiceSelectionParams(language_code='-'.join(voice_name.split('-')[:2]), name=voice_name)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate_hertz,
                speaking_rate=speaking_rate
            )
            parent = f"projects/{config.PROJECT_ID}/locations/{config.LOCATION}"
            
            gcs_filename = f"long_audio_outputs/narration_{int(time.time())}.wav"
            output_gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{gcs_filename}"

            request = texttospeech.SynthesizeLongAudioRequest(
                parent=parent, input=synthesis_input, audio_config=audio_config, voice=voice, output_gcs_uri=output_gcs_uri
            )

            operation = client.synthesize_long_audio(request=request)
            operation.result(timeout=600)

            local_path = download_from_gcs(gcs_uri=output_gcs_uri, output_path=output_path)
            
            message = f"Long-form speech audio saved to {local_path}"
            print(f"✅ SUCCESS: {message}")
            return str(local_path)
        except Exception as e:
            error_message = f"Failed to generate speech with Long Audio API. Error: {e}"
            print(f"❌ FAILED: {error_message}")
            return error_message

# ======================================================================
# --- TOOL: MUSIC GENERATION ---
# ======================================================================

def generate_music(
    prompt: str,
    output_path: str,
    duration_seconds: int = 30,
    negative_prompt: Optional[str] = None
):
    """Generates music via a direct REST call, with negative prompt support."""
    print(f"\n[Tool: generate_music]")
    try:
        creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(google.auth.transport.requests.Request())
        
        api_endpoint = f"https://{config.LOCATION}-aiplatform.googleapis.com/v1/projects/{config.PROJECT_ID}/locations/{config.LOCATION}/publishers/google/models/{MODELS['lyria'][0]}:predict"
        headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
        
        instance = {"prompt": prompt, "duration_seconds": duration_seconds, "seed": int(time.time())}
        if negative_prompt:
            instance["negative_prompt"] = negative_prompt
        
        payload = {"instances": [instance], "parameters": {"sample_count": 1}}
        
        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        response_data = response.json()
        if 'predictions' not in response_data or not response_data['predictions']:
            raise ValueError("API response did not contain predictions.")

        b64_content = response_data['predictions'][0]['bytesBase64Encoded']
        audio_bytes = base64.b64decode(b64_content)
        
        local_path = resolve_path_in_workspace(output_path)
        local_path.write_bytes(audio_bytes)

        print(f"✅ SUCCESS: Music saved to {local_path}")
        return str(local_path)
    except Exception as e:
        print(f"❌ FAILED: generate_music. Error: {e}")
        return None

# ======================================================================
# --- TOOL REGISTRATION ---
# ======================================================================
_TOOL_FUNCTIONS = [
    generate_narration_audio,
    generate_music
]
def get_tool_declarations(): return [create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry(): return {f.__name__: f for f in _TOOL_FUNCTIONS}