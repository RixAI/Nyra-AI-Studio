# tools/nyra_system_tools.py
# Core system utilities for file I/O and video/audio processing.

import os
import shutil
import cv2
import ffmpeg
from pathlib import Path

# --- Path Setup & Configuration ---
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from .nyra_core import resolve_path_in_workspace, create_function_declaration

# --- TOOL FUNCTIONS ---

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
        target_path = resolve_path_in_workspace(path)
        target_path.mkdir(parents=True, exist_ok=True)
        message = f"Directory ensured at {target_path}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        error_message = f"Failed to create directory. Error: {e}"
        print(f"❌ FAILED: {error_message}")
        return error_message

def frames_to_video(input_dir: str, output_path: str, fps: int = 24) -> str:
    """Compiles a sequence of image frames into a video file."""
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

def get_audio_duration(file_path: str) -> float:
    """Gets the duration of an audio or video file in seconds using ffprobe."""
    print(f"\n[HELPER: get_audio_duration] for '{file_path}'")
    try:
        probe = ffmpeg.probe(str(resolve_path_in_workspace(file_path)))
        duration = float(probe['format']['duration'])
        print(f" -> Duration: {duration:.2f} seconds")
        return duration
    except Exception as e:
        print(f"❌ FAILED: Could not get duration. Error: {e}")
        return 0.0

def loop_audio(source_audio_path: str, target_duration_seconds: float, output_path: str) -> str:
    """Loops a source audio file to create a new file of a specific target duration."""
    print(f"\n[Tool: loop_audio] to target duration {target_duration_seconds:.2f}s")
    try:
        input_stream = ffmpeg.input(str(resolve_path_in_workspace(source_audio_path)), stream_loop=-1)
        output_stream = ffmpeg.output(input_stream, str(resolve_path_in_workspace(output_path)), t=target_duration_seconds, acodec='mp3', shortest=None)
        output_stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        message = f"Successfully looped audio to {target_duration_seconds:.2f}s."
        print(f"✅ SUCCESS: {message}")
        return str(resolve_path_in_workspace(output_path))
    except Exception as e:
        # ... error handling ...
        pass

def mix_audio_tracks(narration_path: str, music_path: str, output_path: str, music_volume: float = 0.25) -> str:
    """Mixes a primary narration track with a background music track."""
    print(f"\n[Tool: mix_audio_tracks]")
    try:
        narration_input = ffmpeg.input(str(resolve_path_in_workspace(narration_path)))
        music_input = ffmpeg.input(str(resolve_path_in_workspace(music_path)))
        music_quieter = music_input.filter('volume', volume=music_volume)
        mixed_audio = ffmpeg.filter([narration_input, music_quieter], 'amix', duration='first')
        output_stream = ffmpeg.output(mixed_audio, str(resolve_path_in_workspace(output_path)), acodec='mp3')
        output_stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        message = f"Successfully mixed audio and saved to {output_path}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        # ... error handling ...
        pass

def compile_final_video(video_clip_paths: list[str], audio_clip_paths: list[str], output_path: str) -> str:
    """Compiles multiple video and audio tracks into a final movie using FFMPEG."""
    print(f"\n[Tool: compile_final_video with FFMPEG]")
    try:
        resolved_video_clips = [ffmpeg.input(resolve_path_in_workspace(p).as_posix()) for p in video_clip_paths]
        resolved_audio_clips = [ffmpeg.input(resolve_path_in_workspace(p).as_posix()) for p in audio_clip_paths]
        resolved_output = resolve_path_in_workspace(output_path).as_posix()
        concatenated_video = ffmpeg.concat(*resolved_video_clips, v=1, a=0)
        concatenated_audio = ffmpeg.concat(*[clip.audio for clip in resolved_audio_clips], v=0, a=1)
        output_stream = ffmpeg.output(concatenated_video, concatenated_audio, resolved_output, vcodec='libx264', acodec='aac', shortest=None)
        output_stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        message = f"Final video compiled successfully and saved to {resolved_output}"
        print(f"✅ SUCCESS: {message}")
        return message
    except Exception as e:
        # ... error handling ...
        pass

# --- TOOL REGISTRATION ---
_TOOL_FUNCTIONS = [
    list_files, save_text_file, read_text_file, move_file, copy_file,
    delete_file, make_directory, frames_to_video, compile_final_video,
    mix_audio_tracks, get_audio_duration, loop_audio
]
def get_tool_declarations(): return [create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry(): return {f.__name__: f for f in _TOOL_FUNCTIONS}
# End of file: tools/nyra_system_tools.py