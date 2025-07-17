# tools/nyra_system_tools.py
# (This is a representative example; apply this pattern to all other tool files)
import os
import shutil
import argparse
import cv2
import ffmpeg
from pathlib import Path
from ._helpers import resolve_path_in_workspace
from . import _schema_helper

# ... (All function definitions like list_files, save_text_file, compile_final_video, etc. remain unchanged) ...


# DEFINITIVE FIX: The function is upgraded to accept a list of audio clips.
def compile_final_video(video_clip_paths: list[str], audio_clip_paths: list[str], output_path: str) -> str:
    """
    Compiles multiple video clips and multiple audio tracks into a final movie using FFMPEG.
    The video and audio tracks are concatenated into single streams, respectively, before being combined.
    """
    print(f"\n[Tool: compile_final_video with FFMPEG]")
    try:
        # Resolve all input paths to be safe
        resolved_video_clips = [ffmpeg.input(resolve_path_in_workspace(p).as_posix()) for p in video_clip_paths]
        resolved_audio_clips = [ffmpeg.input(resolve_path_in_workspace(p).as_posix()) for p in audio_clip_paths]
        resolved_output = resolve_path_in_workspace(output_path).as_posix()

        # Concatenate video and audio streams separately.
        # v=1, a=0 means 1 video stream, 0 audio streams
        concatenated_video = ffmpeg.concat(*resolved_video_clips, v=1, a=0)
        # v=0, a=1 means 0 video streams, 1 audio stream
        concatenated_audio = ffmpeg.concat(*[clip.audio for clip in resolved_audio_clips], v=0, a=1)

        # Create the final output by explicitly mapping the concatenated video and audio.
        # 'shortest' ensures the output terminates when the shorter of the two streams (video or audio) ends.
        output_stream = ffmpeg.output(
            concatenated_video,
            concatenated_audio,
            resolved_output,
            vcodec='libx264',
            acodec='aac',
            shortest=None
        )

        print("--- FFMPEG Command Log ---")
        stdout, stderr = output_stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        print("STDOUT:", stdout.decode('utf8'))
        print("STDERR:", stderr.decode('utf8'))
        print("--------------------------")

        message = f"Final video with narration compiled successfully and saved to {resolved_output}"
        print(f"✅ SUCCESS: {message}")
        return message

    except ffmpeg.Error as e:
        error_message = f"FFMPEG compilation failed.\nFFMPEG STDERR: {e.stderr.decode('utf8')}"
        print(f"❌ FAILED: {error_message}")
        return error_message
    except Exception as e:
        error_message = f"An unexpected error occurred during compilation. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

# ... (The rest of the file and the __main__ block are unchanged) ...

def list_files(directory: str = "."):
    """Lists files and directories in the workspace."""
    print(f"\n[Tool: list_files] in '{directory}'")
    target_dir = resolve_path_in_workspace(directory)
    paths = [f"{'d' if e.is_dir() else 'f'} - {e.name}" for e in os.scandir(target_dir)]
    result = "\n".join(paths); print(f"✅ SUCCESS: \n{result}"); return result

def save_text_file(path: str, content: str):
    """Saves text to a file in the workspace."""
    print(f"\n[Tool: save_text_file] to '{path}'")
    file_path = resolve_path_in_workspace(path)
    file_path.write_text(content, encoding='utf-8'); print(f"✅ SUCCESS: File saved to {file_path}")
    return f"File saved to {file_path}"

def read_text_file(path: str) -> str:
    """Reads the content of a text file from the workspace and returns it."""
    print(f"\n[Tool: read_text_file] from '{path}'")
    content = resolve_path_in_workspace(path).read_text(encoding='utf-8')
    print("✅ SUCCESS: File read.")
    return content

def move_file(source_path: str, destination_path: str) -> str:
    """Moves or renames a file or directory and returns a confirmation."""
    print(f"\n[Tool: move_file] from '{source_path}' to '{destination_path}'")
    src = resolve_path_in_workspace(source_path)
    dest = resolve_path_in_workspace(destination_path)
    shutil.move(str(src), str(dest))
    message = f"Moved {source_path} to {destination_path}"
    print(f"✅ SUCCESS: {message}")
    return message

def copy_file(source_path: str, destination_path: str) -> str:
    """Copies a file or directory and returns a confirmation."""
    print(f"\n[Tool: copy_file] from '{source_path}' to '{destination_path}'")
    src = resolve_path_in_workspace(source_path)
    dest = resolve_path_in_workspace(destination_path)
    if src.is_dir(): shutil.copytree(str(src), str(dest))
    else: shutil.copy2(str(src), str(dest))
    message = f"Copied {source_path} to {destination_path}"
    print(f"✅ SUCCESS: {message}")
    return message

def delete_file(path: str) -> str:
    """Deletes a file or directory and returns a confirmation."""
    print(f"\n[Tool: delete_file] at '{path}'")
    target = resolve_path_in_workspace(path)
    if target.is_dir(): shutil.rmtree(target)
    else: os.remove(target)
    message = f"Deleted {path}"
    print(f"✅ SUCCESS: {message}")
    return message

def make_directory(path: str) -> str:
    """Creates a new directory (and any parents) if it doesn't exist."""
    print(f"\n[Tool: make_directory] at '{path}'")
    try:
        # Use the helper to get a safe, resolved path object
        target_path = resolve_path_in_workspace(path)
        
        # Explicitly create the target directory itself.
        target_path.mkdir(parents=True, exist_ok=True)
        
        message = f"Directory ensured at {target_path}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        error_message = f"Failed to create directory. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

def frames_to_video(input_dir: str, output_path: str, fps: int = 24) -> str:
    """Compiles a sequence of image frames into a video file and returns a confirmation."""
    print(f"\n[Tool: frames_to_video]")
    frame_dir = resolve_path_in_workspace(input_dir)
    output_file = resolve_path_in_workspace(output_path)
    images = sorted([img for img in frame_dir.iterdir() if img.suffix.lower() in ['.png', '.jpg', '.jpeg']])
    if not images: raise ValueError(f"No image frames found in '{frame_dir}'")

    frame = cv2.imread(str(images[0]))
    height, width, _ = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(str(output_file), fourcc, float(fps), (width, height))

    for image in images:
        video.write(cv2.imread(str(image)))

    video.release()
    message = f"Video compiled and saved to {output_file}"
    print(f"✅ SUCCESS: {message}")
    return message

 
def mix_audio_tracks(narration_path: str, music_path: str, output_path: str, music_volume: float = 0.25) -> str:
    """
    Mixes a primary narration track with a background music track.
    The music volume is lowered to ensure the narration is clear.
    """
    print(f"\n[Tool: mix_audio_tracks] -> Mixing narration and music")
    try:
        narration_input = ffmpeg.input(resolve_path_in_workspace(narration_path))
        music_input = ffmpeg.input(resolve_path_in_workspace(music_path))
        resolved_output = resolve_path_in_workspace(output_path)

        # DEFINITIVE FIX: Corrected the invalid variable name 'music_ quieter' to 'music_quieter'.
        music_quieter = music_input.filter('volume', volume=music_volume)

        # Mix the narration at full volume with the quieter music track
        # 'shortest' ensures the output duration matches the narration.
        mixed_audio = ffmpeg.filter([narration_input, music_quieter], 'amix', duration='first')

        # Execute the ffmpeg command
        output_stream = ffmpeg.output(mixed_audio, str(resolved_output), acodec='mp3')
        output_stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)

        message = f"Successfully mixed audio and saved to {resolved_output}"
        print(f"✅ SUCCESS: {message}")
        return message
    except ffmpeg.Error as e:
        error_message = f"FFMPEG mixing failed.\nFFMPEG STDERR: {e.stderr.decode('utf8')}"
        print(f"❌ FAILED: {error_message}")
        return error_message
    except Exception as e:
        error_message = f"An unexpected error occurred during audio mixing. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message



# Add this helper function to the file
def get_audio_duration(file_path: str) -> float:
    """Gets the duration of an audio or video file in seconds using ffprobe."""
    print(f"\n[HELPER: get_audio_duration] for '{file_path}'")
    try:
        resolved_path = resolve_path_in_workspace(file_path)
        probe = ffmpeg.probe(str(resolved_path))
        duration = float(probe['format']['duration'])
        print(f" -> Duration: {duration:.2f} seconds")
        return duration
    except Exception as e:
        print(f"❌ FAILED: Could not get duration. Error: {e}")
        return 0.0

# Add this new tool function to the file
def loop_audio(source_audio_path: str, target_duration_seconds: float, output_path: str) -> str:
    """
    Loops a source audio file to create a new file of a specific target duration.
    """
    print(f"\n[Tool: loop_audio] to target duration {target_duration_seconds:.2f}s")
    try:
        resolved_source = resolve_path_in_workspace(source_audio_path)
        resolved_output = resolve_path_in_workspace(output_path)

        # Use ffmpeg's stream_loop for efficient, gapless looping
        # -1 means infinite loop, which we then cut short with the -t (t) parameter.
        input_stream = ffmpeg.input(str(resolved_source), stream_loop=-1)
        
        # Create the output stream, trimming it to the exact target duration.
        # acodec='copy' is used to avoid re-encoding if the format is the same, making it faster.
        output_stream = ffmpeg.output(input_stream, str(resolved_output), t=target_duration_seconds, acodec='copy', shortest=None)

        # Execute the command
        output_stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)

        message = f"Successfully looped '{source_audio_path}' to {target_duration_seconds:.2f}s. Saved to {resolved_output}"
        print(f"✅ SUCCESS: {message}")
        return str(resolved_output)
    except ffmpeg.Error as e:
        error_message = f"FFMPEG looping failed.\nFFMPEG STDERR: {e.stderr.decode('utf8')}"
        print(f"❌ FAILED: {error_message}")
        return error_message
    except Exception as e:
        error_message = f"An unexpected error occurred during audio looping. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

# Remember to add `get_audio_duration` and `loop_audio` to the _TOOL_FUNCTIONS list in the file.



# --- TOOL REGISTRATION ---
_TOOL_FUNCTIONS = [
    list_files, save_text_file, read_text_file, move_file, copy_file,
    delete_file, make_directory, frames_to_video, compile_final_video,
    mix_audio_tracks, get_audio_duration, loop_audio
]
def get_tool_declarations(): return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry(): return {f.__name__: f for f in _TOOL_FUNCTIONS}