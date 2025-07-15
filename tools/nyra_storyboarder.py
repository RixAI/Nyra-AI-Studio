# tools/nyra_storyboarder.py
import argparse
import json
from pydantic import BaseModel, Field, conint
from typing import List, Optional, Literal

# DEFINITIVE FIX: Added missing imports for the genai library, config, and helpers.
from google import genai
import config
from ._helpers import resolve_path_in_workspace

# --- Pydantic Schemas for a Detailed Production Plan ---

class AudioLayer(BaseModel):
    layer_type: Literal["DIALOGUE", "MUSIC", "SFX"] = Field(description="The type of audio layer.")
    prompt: str = Field(description="The dialogue text, or a detailed description for generating music or sound effects.")
    voice_name: Optional[str] = Field(None, description="The specific voice model to use for dialogue (e.g., 'hi-IN-Wavenet-D').")

class ShotExecutionPlan(BaseModel):
    shot_number: int = Field(description="The sequential number of the shot.")
    description: str = Field(description="A detailed visual description of the action, characters, and setting for this shot.")
    duration_seconds: conint(ge=4, le=60) = Field(description="The final intended duration for this shot.")
    generation_strategy: Literal["SINGLE_SHOT", "EXTEND_SHOT", "FRAMES_TO_VIDEO"] = Field(description="The strategy to create the video for this shot. 'EXTEND_SHOT' should be used for shots longer than 8 seconds.")
    video_prompt: str = Field(description="The final, optimized prompt to be fed into the video generation model.")
    audio_layers: List[AudioLayer] = Field(description="A list of all audio components required for this shot.")
    transition_to_next: Optional[Literal["CUT", "FADE_TO_BLACK"]] = Field("CUT", description="The transition effect to the next shot.")

class ProductionPlan(BaseModel):
    title: str = Field(description="The title of the project.")
    overall_mood: str = Field(description="The overall mood and tone of the film (e.g., 'lonely and hopeful', 'tense and action-packed').")
    shots: List[ShotExecutionPlan] = Field(description="The detailed execution plan for every shot in the sequence.")

# --- Tool Function ---

def create_production_plan(prompt: str, output_path: str) -> str:
    """
    Uses an AI model to generate a detailed, strategic production plan in JSON format from a high-level film concept.
    This plan includes shot durations, generation strategies (single shot, extend), and audio layering (dialogue, music, sfx).
    """
    print(f"\n[Tool: create_production_plan] for prompt: '{prompt}'")
    try:
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)

        system_prompt = f"""
        You are an expert AI Film Director and Production Planner. Your task is to take a user's high-level film concept
        and create a comprehensive, shot-by-shot execution plan.

        You MUST adhere to the following technical constraints:
        - The 'veo-2.0-generate-001' model can generate a maximum of 8 seconds per call.
        - For any shot requiring a duration longer than 8 seconds, you MUST set the 'generation_strategy' to 'EXTEND_SHOT'.
        - For 'EXTEND_SHOT', the initial generation will be 8 seconds, and you must formulate a logical follow-up prompt for the extension.

        For each shot, you will define:
        1.  A precise `video_prompt`.
        2.  The final `duration_seconds`.
        3.  The correct `generation_strategy`.
        4.  A list of all `audio_layers`, specifying whether each is DIALOGUE, MUSIC, or SFX, and providing a generation prompt for it.
        5.  The `transition_to_next` shot.

        You must output a valid JSON object that conforms to the provided 'ProductionPlan' schema.
        """

        full_prompt = [system_prompt, f"Here is the film concept: {prompt}"]

        gen_config = genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ProductionPlan,
        )

        response = gcp_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=full_prompt,
            config=gen_config
        )

        json_string = response.text
        
        # Validate and reformat for readability
        plan = ProductionPlan.model_validate_json(json_string)
        pretty_json = plan.model_dump_json(indent=2)
        
        local_path = resolve_path_in_workspace(output_path)
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(pretty_json)

        message = f"Production Plan JSON saved successfully to {local_path}"
        print(f"✅ SUCCESS: {message}")
        return message

    except Exception as e:
        error_message = f"Failed to create production plan JSON. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="AI Production Plan Generator")
    parser.add_argument("--prompt", required=True, help="The high-level story or scene description.")
    parser.add_argument("--output_path", required=True, help="Local path to save the output production_plan.json file.")
    args = parser.parse_args()
    create_production_plan(args.prompt, args.output_path)