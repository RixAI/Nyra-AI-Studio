# run_final_sanatan_cosmology_production.py
# The definitive, end-to-end master production pipeline for Nyra AI Studio.
# Version 2.0: Corrects the JSON loading TypeError in Phases 3 & 4.

import os
import sys
import json
from pathlib import Path
import time
import random

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports ---
from tools.nyra_system_tools import (
    make_directory, get_audio_duration, loop_audio, mix_audio_tracks
)
from tools.nyra_moviepy_tools import (
    compile_with_moviepy_transition, speedup_video
)
from tools.nyra_storyboarder import generate_documentary_script
from tools.nyra_audio_tool import generate_narration_audio, generate_music
from tools.nyra_image_tools import generate_image, AspectRatio
from tools.nyra_video_tools import generate_veo2_video, generate_veo3_video
from tools.nyra_core import upload_to_gcs, download_from_gcs

# --- Dependency Imports ---
from google import genai
from google.genai.types import Part, GenerateContentConfig
from pydantic import BaseModel, Field, RootModel
from typing import List
from moviepy.editor import VideoFileClip, AudioFileClip

# ======================================================================
# >> MASTER PRODUCTION CONTROL PANEL <<
# ======================================================================
TOPIC = "A 2-minute journey through our solar system, exploring Mars, Jupiter, and Venus from the perspective of Sanatana Dharma, viewing the planets not just as physical bodies but as expressions of cosmic intelligence (Devatas)."
LANGUAGE = "Hindi"
VISUAL_STYLE_GUIDE = "Style: cosmic, ethereal, cinematic 4K, beautiful nebulas, swirling galaxies, sacred geometry, beams of light, highly detailed, divine aesthetic, photorealistic."
MUSIC_PROMPT = "A deep, meditative, and spacious ambient drone soundscape. Features the sound of a traditional Indian tanpura and soft, evolving synthesizer pads, creating a spiritual and cosmic atmosphere for a science documentary."
NARRATION_VOICE = "hi-IN-Chirp3-HD-Vindemiatrix"
TRANSITION_PROMPTS = {
    "fire_wipe": "A wall of intense fire wiping across the screen from left to right. Rendered as a high-contrast, black and white luma matte, where the fire is pure white and the unburned area is pure black.",
    "ink_bleed": "A high-contrast luma matte of a drop of black ink falling onto a white surface and spreading outwards to fill the screen.",
    "digital_glitch": "A high-contrast, black and white luma matte of a digital glitch effect wiping across the screen."
}
FINAL_TRANSITION_DURATION_S = 1
PROJECT_DIR = Path(config.WORKSPACE_DIR) / "output/final_sanatan_cosmology_video"
# ======================================================================

# Pydantic models for the visual plan
class ShotDetail(BaseModel):
    narration_line: str; start_time: float; end_time: float; image_prompt: str; motion_prompt: str
class VisualPlan(RootModel):
    root: List[ShotDetail]

def phase_one_pre_production() -> tuple[Path, Path]:
    print("\n" + "="*80)
    print("--- PHASE 1: PRE-PRODUCTION (SCRIPT & AUDIO) ---")
    script_text = generate_documentary_script(topic=TOPIC, language=LANGUAGE)
    narration_path = PROJECT_DIR / "master_narration.wav"
    generate_narration_audio(text_to_speak=script_text, output_path=str(narration_path), voice_name=NARRATION_VOICE, speaking_rate=0.98)
    music_path_raw = PROJECT_DIR / "music_raw.wav"
    generate_music(prompt=MUSIC_PROMPT, output_path=str(music_path_raw), duration_seconds=30)
    narration_duration = get_audio_duration(str(narration_path))
    looped_music_path = PROJECT_DIR / "music_looped.mp3"
    loop_audio(source_audio_path=str(music_path_raw), target_duration_seconds=narration_duration, output_path=str(looped_music_path))
    final_audio_path = PROJECT_DIR / "master_audio_mix.mp3"
    mix_audio_tracks(narration_path=str(narration_path), music_path=str(looped_music_path), output_path=str(final_audio_path), music_volume=0.35)
    print("--- ✅ Phase 1 Complete. Master Audio Track is ready. ---")
    return final_audio_path, narration_path

def phase_two_visual_planning(client: genai.Client, narration_audio_path: Path) -> Path:
    print("\n" + "="*80)
    print("--- PHASE 2: VISUAL PLANNING ---")
    plan_path = PROJECT_DIR / "visual_plan.json"
    gcs_uri = upload_to_gcs(narration_audio_path, "gemini-audio-inputs")
    system_prompt = f"You are an AI Film Director... Your output MUST be a single, valid JSON object conforming to the 'VisualPlan' schema."
    config_params = GenerateContentConfig(response_mime_type="application/json", response_schema=VisualPlan, audio_timestamp=True)
    contents = [system_prompt, Part.from_uri(file_uri=gcs_uri, mime_type="audio/wav")]
    response = client.models.generate_content(model="gemini-2.5-pro", contents=contents, config=config_params)
    final_plan = response.parsed
    if not final_plan: raise ValueError(f"Failed to generate Visual Plan. Response: {response.text}")
    with open(plan_path, 'w', encoding='utf-8') as f:
        f.write(final_plan.model_dump_json(indent=4))
    print(f"--- ✅ Phase 2 Complete. Visual Plan saved. ---")
    return plan_path

def phase_three_visual_production(plan_path: Path):
    print("\n" + "="*80)
    print("--- PHASE 3: VISUAL PRODUCTION (KEYFRAMES & ANIMATION) ---")
    with open(plan_path, 'r', encoding='utf-8') as f:
        # DEFINITIVE FIX: The JSON file is a direct list. Do not access the ['root'] key.
        visual_plan = json.load(f)

    for i, shot in enumerate(visual_plan):
        shot_num = i + 1
        print(f"\n--- Processing Shot {shot_num:02d}/{len(visual_plan)} ---")
        shot_dir = PROJECT_DIR / f"shot_{shot_num:02d}"
        shot_dir.mkdir(parents=True, exist_ok=True)
        keyframe_path = shot_dir / "keyframe.png"
        generate_image("imagen-4.0-ultra-generate-preview-06-06", shot['image_prompt'], str(keyframe_path), AspectRatio.RATIO_16_9)
        clip_path = shot_dir / "animated_clip.mp4"
        duration = shot['end_time'] - shot['start_time']
        clamped_duration = max(5, min(8, int(duration)))
        generate_veo2_video("veo-2.0-generate-001", str(clip_path), prompt=shot['motion_prompt'], image_path=str(keyframe_path), duration_seconds=clamped_duration)
    print("--- ✅ Phase 3 Complete. All visual assets generated. ---")


# ======================================================================
# Phase 4: Post-Production
# ======================================================================
# In this phase, we will generate the VFX transitions and assemble the final video.
# In phase_four_post_production, we just need to change which tool is called.
def phase_four_post_production(plan_path: Path, master_audio_path: Path):
    """Generates transitions and assembles the final video."""
    print("\n" + "="*80)
    print("--- PHASE 4: POST-PRODUCTION (VFX TRANSITIONS & ASSEMBLY) ---")
    
    # --- 4.1: Generate Transition Assets ---
    print(" -> 4.1 Generating Transition Assets (Matte and Texture)...")
    control_matte_path = PROJECT_DIR / "transition_control_matte.mp4"
    fire_texture_path = PROJECT_DIR / "transition_fire_texture.mp4"
    
    # Generate the simple B&W matte for shape
    generate_veo3_video("veo-3.0-fast-generate-preview", str(control_matte_path), 
                        prompt="A high-contrast luma matte of a vertical paper tear, from top to bottom. White on a pure black background.", 
                        generate_audio=False)

    # Generate the colored fire texture
    generate_veo3_video("veo-3.0-generate-preview", str(fire_texture_path), 
                        prompt="A cinematic, realistic, turbulent wall of fire, with embers and intense flames, on a solid black background.", 
                        generate_audio=False)

    # Speed up both to match the desired transition duration
    sped_up_matte_path = PROJECT_DIR / "transition_control_matte_final.mp4"
    sped_up_texture_path = PROJECT_DIR / "transition_fire_texture_final.mp4"
    speed_factor = 8 / FINAL_TRANSITION_DURATION_S
    speedup_video(str(control_matte_path), str(sped_up_matte_path), speed_factor)
    speedup_video(str(fire_texture_path), str(sped_up_texture_path), speed_factor)
        
    # --- 4.2: Iteratively Assemble Video with VFX Transitions ---
    print(" -> 4.2 Assembling video with multi-layer VFX transitions...")
    with open(plan_path, 'r', encoding='utf-8') as f:
        num_shots = len(json.load(f)['root'])
        
    # Start with the first clip
    compiled_clip_path = PROJECT_DIR / "shot_01" / "animated_clip.mp4"
    for i in range(1, num_shots):
        clip_a_path = compiled_clip_path
        clip_b_path = PROJECT_DIR / f"shot_{i+1:02d}" / "animated_clip.mp4"
        
        print(f"  -> Merging shot {i} and {i+1} with fire border...")
        output_merge_path = PROJECT_DIR / f"temp_compile_{i}.mp4"
        
        # DEFINITIVE FIX: Call the new, correct VFX tool
        compile_with_vfx_border_transition(
            clip_a_path=str(clip_a_path),
            clip_b_path=str(clip_b_path),
            control_matte_path=str(sped_up_matte_path), # The B&W shape matte
            texture_path=str(sped_up_texture_path),     # The color fire texture
            output_path=str(output_merge_path),
            transition_duration_seconds=FINAL_TRANSITION_DURATION_S
        )
        compiled_clip_path = output_merge_path
    
    # --- 4.3: Add Master Audio Track ---
    print(" -> 4.3 Adding Master Audio Track...")
    final_video_path = PROJECT_DIR / "FINAL_COSMIC_SANATAN_VIDEO_v2.mp4"
    final_video_clip = VideoFileClip(str(compiled_clip_path))
    master_audio = AudioFileClip(str(master_audio_path))
    final_clip = final_video_clip.set_audio(master_audio.set_duration(final_video_clip.duration))
    final_clip.write_videofile(str(final_video_path), codec="libx264", audio_codec="aac")
    
    final_clip.close()
    
    print("--- ✅ Phase 4 Complete. Final video with VFX transitions is rendered. ---")

# ... (The rest of the script, including the __main__ block, remains the same) ...


if __name__ == "__main__":
    try:
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        make_directory(str(PROJECT_DIR))
        
        master_audio, raw_narration = phase_one_pre_production()
        visual_plan = phase_two_visual_planning(client, raw_narration)
        phase_three_visual_production(visual_plan)
        phase_four_post_production(visual_plan, master_audio)

        print("\n" + "="*80)
        print("--- MASTER PRODUCTION COMPLETE ---")
        
    except Exception as e:
        import traceback
        print(f"\n--- ❌ MASTER WORKFLOW FAILED: {e} ---")
        traceback.print_exc()