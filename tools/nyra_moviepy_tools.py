# tools/nyra_moviepy_tools.py
# A definitive toolset for advanced video editing using the MoviePy library.

import os
import sys
from moviepy.editor import (VideoFileClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip)
import moviepy.video.fx.all as vfx

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .nyra_core import resolve_path_in_workspace, create_function_declaration

def compile_with_moviepy_transition(
    clip_a_path: str,
    clip_b_path: str,
    matte_path: str,
    output_path: str,
    transition_duration_seconds: int = 2
) -> str:
    """
    Compiles two clips using a luma matte video and the MoviePy library.
    """
    print(f"\n[Tool: compile_with_moviepy_transition (MoviePy Engine v4.0)]")
    clip_a, clip_b, matte, final_clip = None, None, None, None
    try:
        resolved_clip_a = str(resolve_path_in_workspace(clip_a_path))
        resolved_clip_b = str(resolve_path_in_workspace(clip_b_path))
        resolved_matte = str(resolve_path_in_workspace(matte_path))
        resolved_output = str(resolve_path_in_workspace(output_path))
        
        clip_a = VideoFileClip(resolved_clip_a)
        clip_b = VideoFileClip(resolved_clip_b)
        matte = VideoFileClip(resolved_matte).set_duration(transition_duration_seconds)
        
        part_a = clip_a.subclip(0, clip_a.duration - transition_duration_seconds)
        part_b = clip_b.subclip(transition_duration_seconds)
        transition_clip_a = clip_a.subclip(clip_a.duration - transition_duration_seconds)
        transition_clip_b = clip_b.subclip(0, transition_duration_seconds)
        
        matte_normalized = matte.fx(vfx.blackwhite)
        matte_mask = matte_normalized.to_mask()
        
        transition_clip_b_masked = transition_clip_b.set_mask(matte_mask)
        transition_segment = CompositeVideoClip([transition_clip_a, transition_clip_b_masked])
        final_video = concatenate_videoclips([part_a, transition_segment, part_b])
        
        if clip_a.audio and clip_b.audio:
            final_audio = concatenate_audioclips([clip_a.audio, clip_b.audio])
            final_clip = final_video.set_audio(final_audio)
        else:
            final_clip = final_video.set_audio(None)

        final_clip.write_videofile(
            resolved_output, 
            codec="libx264", 
            audio_codec="aac" if final_clip.audio else None, 
            threads=8
        )
        message = f"Successfully compiled video with MoviePy transition and saved to {resolved_output}"
        print(f"✅ SUCCESS: {message}")
        return str(resolved_output)
    except Exception as e:
        error_message = f"MoviePy compilation with transition failed. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message
    finally:
        if clip_a: clip_a.close()
        if clip_b: clip_b.close()
        if matte: matte.close()
        if 'final_clip' in locals() and final_clip: final_clip.close()

def speedup_video(input_path: str, output_path: str, speed_factor: float) -> str:
    """
    Speeds up a video by a given factor and saves the result.
    """
    print(f"\n[Tool: speedup_video] by factor of {speed_factor}x")
    clip = None
    sped_up_clip = None
    try:
        resolved_input = str(resolve_path_in_workspace(input_path))
        resolved_output = str(resolve_path_in_workspace(output_path))
        clip = VideoFileClip(resolved_input)
        sped_up_clip = clip.fx(vfx.speedx, speed_factor)
        sped_up_clip.write_videofile(resolved_output, codec="libx264", audio_codec="aac")
        message = f"Successfully sped up video and saved to {resolved_output}"
        print(f"✅ SUCCESS: {message}")
        return str(resolved_output)
    except Exception as e:
        error_message = f"MoviePy speedup failed. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message
    finally:
        if clip: clip.close()
        if sped_up_clip: sped_up_clip.close()


# In tools/nyra_moviepy_tools.py, replace the old transition function with this one.

def compile_with_vfx_border_transition(
    clip_a_path: str,
    clip_b_path: str,
    control_matte_path: str,
    texture_path: str,
    output_path: str,
    transition_duration_seconds: int = 1
) -> str:
    """
    Composites a definitive transition with a colored texture border (e.g., real fire).
    This is the final, multi-layer compositing solution using MoviePy.
    """
    print(f"\n[Tool: compile_with_vfx_border_transition (VFX Engine)]")
    clip_a, clip_b, matte, texture, final_clip = [None] * 5
    try:
        # --- 1. Load all video assets ---
        clip_a = VideoFileClip(str(resolve_path_in_workspace(clip_a_path)))
        clip_b = VideoFileClip(str(resolve_path_in_workspace(clip_b_path)))
        matte = VideoFileClip(str(resolve_path_in_workspace(control_matte_path)))
        texture = VideoFileClip(str(resolve_path_in_workspace(texture_path)))

        # --- 2. Prepare all clips for the transition segment ---
        transition_a = clip_a.subclip(clip_a.duration - transition_duration_seconds)
        transition_b = clip_b.subclip(0, transition_duration_seconds)
        
        # Resize matte and texture to match the main video dimensions and duration
        matte = matte.resize(height=clip_a.h).set_duration(transition_duration_seconds)
        texture = texture.resize(height=clip_a.h).set_duration(transition_duration_seconds)
        
        # --- 3. The Core Compositing Logic ---
        # Create a clean transparency mask from the black and white control matte
        transition_mask = matte.fx(vfx.blackwhite).to_mask()
        
        # Apply the mask to Clip B, so it is revealed by the matte's shape
        transition_b_masked = transition_b.set_mask(transition_mask)
        
        # Apply the SAME mask to the fire texture video
        fire_border_element = texture.set_mask(transition_mask)

        # --- 4. Layer the final transition ---
        # The layers are ordered from bottom to top:
        # 1. The end of Clip A (base layer)
        # 2. The start of Clip B (revealed by the mask)
        # 3. The fire texture (revealed by the same mask, appearing on top of the seam)
        transition_segment = CompositeVideoClip(
            [transition_a, transition_b_masked, fire_border_element],
            size=clip_a.size
        )

        # --- 5. Stitch the final video with the new transition segment ---
        final_video = concatenate_videoclips([
            clip_a.subclip(0, clip_a.duration - transition_duration_seconds),
            transition_segment,
            clip_b.subclip(transition_duration_seconds)
        ])
        
        # Concatenate audio tracks to match the final video length
        final_audio = concatenate_audioclips([clip_a.audio, clip_b.audio])
        final_clip = final_video.set_audio(final_audio.set_duration(final_video.duration))

        # --- 6. Render final output ---
        print(" -> Rendering final video with real fire border...")
        final_clip.write_videofile(str(resolve_path_in_workspace(output_path)), codec="libx264", audio_codec="aac")

        message = f"Successfully compiled video with VFX border and saved to {output_path}"
        print(f"✅ SUCCESS: {message}")
        return str(output_path)
    except Exception as e:
        error_message = f"MoviePy VFX compilation failed. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message
    finally:
        for clip in [clip_a, clip_b, matte, texture, final_clip]:
            if clip:
                clip.close()

# --- Tool Registration ---
_TOOL_FUNCTIONS = [compile_with_moviepy_transition, compile_with_vfx_border_transition, speedup_video]
def get_tool_declarations(): return [create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry(): return {f.__name__: f for f in _TOOL_FUNCTIONS}
# End of file: tools/nyra_moviepy_tools.py