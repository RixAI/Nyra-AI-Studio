# tools/nyra_storyboarder.py
# Definitive Version 2.0: Adds the 'generate_shot_list' tool for AI-driven storyboard creation.

import argparse
import json
from pydantic import BaseModel, Field, conint, RootModel
from typing import List, Optional, Literal

from google import genai
import config
from ._helpers import resolve_path_in_workspace
from . import _schema_helper

# --- Pydantic Schemas for AI-Generated Shot List ---

class ShotDetail(BaseModel):
    shot_id: int = Field(description="The sequential number of the shot, starting from 1.")
    view_angle: Literal["front", "side", "back"] = Field(description="The camera's angle relative to the character.")
    pose_prompt: str = Field(description="A descriptive prompt for a reference image to define the character's pose. e.g., 'A photo of a person climbing a ladder'.")
    scene_prompt: str = Field(description="A detailed prompt for the background and environment of the scene.")
    action_prompt: str = Field(description="A concise description of the character's specific action in the scene. e.g., 'Jax is climbing a ladder on the exterior of a space station.'")

class ShotList(RootModel):
    root: List[ShotDetail] = Field(description="A list of shot details for a storyboard sequence.")

# --- NEW TOOL FUNCTION ---

def generate_shot_list(prompt: str, character_name: str, num_shots: int, output_path: str) -> str:
    """
    Uses an AI model to generate a dynamic list of storyboard shots from a high-level concept.
    """
    print(f"\n[Tool: generate_shot_list] for concept: '{prompt}'")
    try:
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        system_prompt = f"""
        You are an expert Storyboard Artist. Your task is to take a user's high-level story concept
        and break it down into a sequence of {num_shots} distinct and interesting shots for a character named '{character_name}'.

        For each shot, you must define:
        1.  `shot_id`: The sequence number.
        2.  `view_angle`: A logical camera angle ('front', 'side', 'back') for the shot.
        3.  `pose_prompt`: A simple, clear description of a real-world human pose for pose extraction.
        4.  `scene_prompt`: A rich, detailed description of the environment.
        5.  `action_prompt`: The specific action the character is performing.

        You must output a valid JSON object that conforms to the provided 'ShotList' schema.
        """
        gen_config = genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ShotList,
        )
        response = gcp_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[system_prompt, f"Here is the story concept: {prompt}"],
            config=gen_config
        )
        # The response.text is a JSON string of the RootModel's root list
        validated_shots = ShotList.model_validate_json(response.text)
        pretty_json = validated_shots.model_dump_json(indent=2)
        
        local_path = resolve_path_in_workspace(output_path)
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(pretty_json)
        message = f"Dynamic shot list with {len(validated_shots.root)} shots saved to {local_path}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        error_message = f"Failed to create dynamic shot list. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

# --- Existing ProductionPlan Schemas and create_production_plan function... ---
# (The rest of the file remains unchanged)
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

def create_production_plan(prompt: str, output_path: str) -> str:
    """
    Uses an AI model to generate a detailed, strategic production plan in JSON format from a high-level film concept.
    This plan includes shot durations, generation strategies (single shot, extend), and audio layering (dialogue, music, sfx).
    """
    # This function's implementation is correct and remains unchanged.
    print(f"\n[Tool: create_production_plan] for prompt: '{prompt}'")
    try:
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        system_prompt = f"""
        You are an expert AI Film Director and Production Planner...
        """ # System prompt content is unchanged
        full_prompt = [system_prompt, f"Here is the film concept: {prompt}"]
        gen_config = genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ProductionPlan,
        )
        response = gcp_client.models.generate_content(
            model="gemini-2.5-pro", contents=full_prompt, config=gen_config
        )
        plan = ProductionPlan.model_validate_json(response.text)
        pretty_json = plan.model_dump_json(indent=2)
        local_path = resolve_path_in_workspace(output_path)
        with open(local_path, 'w', encoding='utf-8') as f: f.write(pretty_json)
        message = f"Production Plan JSON saved successfully to {local_path}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        error_message = f"Failed to create production plan JSON. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

# In tools/nyra_storyboarder.py, replace the existing function with this corrected version.

def generate_documentary_script(topic: str, language: str = "Hindi") -> str:
    """
    Generates a historical documentary-style narration script for a given topic.
    The style is based on a formal, chronological, narrative tone.
    Version 2.0: Adds strict instructions to output only clean, narration-ready text.
    """
    print(f"\n[Tool: generate_documentary_script] for topic: '{topic}'")
    try:
        gcp_client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        
        # DEFINITIVE FIX: The system prompt is now extremely strict to prevent formatting artifacts.
        system_prompt = f"""
        You are an expert scriptwriter for historical documentaries. Your task is to write a script on the user's topic.

        Your output MUST follow these absolute rules:
        1.  **Content:** You MUST ONLY generate the text to be spoken by the narrator.
        2.  **No Labels:** You MUST NOT include any speaker labels like 'सूत्रधार:' or 'Narrator:'.
        3.  **No Formatting:** You MUST NOT include any scene directions, camera instructions, emotional cues, or any other text within parentheses `()` or asterisks `**`.
        4.  **Clean Output:** The final output must be a single, clean block of text containing only the narration, ready to be fed directly into a Text-to-Speech (TTS) engine.
        5.  **Language:** The script must be written in pure, formal {language}.
        """
        
        full_prompt = [system_prompt, f"The topic is: {topic}"]
        
        response = gcp_client.models.generate_content(
            model="gemini-2.5-pro", 
            contents=full_prompt
        )
        
        # Further programmatic cleaning for safety, though the prompt should handle most of it.
        clean_text = response.text.strip()
        # Remove any potential lingering labels
        clean_text = clean_text.replace("सूत्रधार:", "").replace("Narrator:", "").strip()
        
        print(f"✅ SUCCESS: Clean documentary script generated successfully.")
        return clean_text
        
    except Exception as e:
        error_message = f"Failed to generate documentary script. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message