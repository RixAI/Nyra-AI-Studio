# tools/nyra_long_audio.py
# A tool to handle long-form text synthesis using Google's asynchronous Long Audio API.
# Definitive Version 2.0: Adds support for the speaking_rate parameter.

import argparse
from typing import Optional
from google.cloud import texttospeech

import config

def synthesize_long_audio(
    text_to_synthesize: str,
    output_gcs_uri: str,
    voice_name: str,
    speaking_rate: Optional[float] = 1.0,
    sample_rate_hertz: Optional[int] = 44100
) -> str:
    """
    Synthesizes long-form text asynchronously and saves the output to a GCS bucket.
    """
    print(f"\n[Tool: synthesize_long_audio] with voice '{voice_name}'")
    try:
        client = texttospeech.TextToSpeechLongAudioSynthesizeClient()

        synthesis_input = texttospeech.SynthesisInput(text=text_to_synthesize)

        voice = texttospeech.VoiceSelectionParams(
            language_code='-'.join(voice_name.split('-')[:2]),
            name=voice_name
        )

        # Added speaking_rate to the audio configuration.
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate_hertz,
            speaking_rate=speaking_rate
        )

        parent = f"projects/{config.PROJECT_ID}/locations/{config.LOCATION}"

        request = texttospeech.SynthesizeLongAudioRequest(
            parent=parent,
            input=synthesis_input,
            audio_config=audio_config,
            voice=voice,
            output_gcs_uri=output_gcs_uri,
        )

        print(f" -> Submitting long audio synthesis request with speaking rate: {speaking_rate}...")
        operation = client.synthesize_long_audio(request=request)
        print(" -> Waiting for operation to complete...")
        
        result = operation.result(timeout=600)

        message = f"Long-form audio synthesis complete. Output saved to GCS at: {output_gcs_uri}"
        print(f"✅ SUCCESS: {message}")
        return output_gcs_uri

    except Exception as e:
        error_message = f"Failed to synthesize long audio. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Long Audio Synthesis Tool")
    parser.add_argument("--text", required=True)
    parser.add_argument("--gcs_uri", required=True, help="GCS URI to save output, e.g., gs://bucket/audio.wav")
    parser.add_argument("--voice_name", default="hi-IN-Chirp3-HD-Vindemiatrix")
    parser.add_argument("--rate", type=float, default=1.0, help="Speaking rate/speed.")
    
    args = parser.parse_args()
    synthesize_long_audio(
        text_to_synthesize=args.text,
        output_gcs_uri=args.gcs_uri,
        voice_name=args.voice_name,
        speaking_rate=args.rate
    )