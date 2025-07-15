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
    """Creates a new directory and returns a confirmation."""
    print(f"\n[Tool: make_directory] at '{path}'")
    target_path = resolve_path_in_workspace(path)
    # The directory is already created by resolve_path_in_workspace helper
    message = f"Created directory at {target_path}"
    print(f"✅ SUCCESS: {message}")
    return message

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

# --- TOOL REGISTRATION ---
_TOOL_FUNCTIONS = [
    list_files, save_text_file, read_text_file, move_file, copy_file,
    delete_file, make_directory, frames_to_video, compile_final_video
]
def get_tool_declarations():
    return [_schema_helper.create_function_declaration(f) for f in _TOOL_FUNCTIONS]
def get_tool_registry():
    return {f.__name__: f for f in _TOOL_FUNCTIONS}
