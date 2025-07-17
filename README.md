
# Nyra AI Studio 

## 1\. Overview

**Nyra AI Studio** is a complete, modular, and robust Python framework designed for the end-to-end production of generative AI video content. It functions as an orchestration engine, intelligently combining a suite of Google's state-of-the-art generative models with advanced local processing tools to transform a high-level creative concept into a finished, professional-quality video.

The studio's architecture is built on a "director and crew" model:

  * **The Director (Gemini 2.5 Pro):** Analyzes high-level concepts, writes scripts, and creates detailed, timestamped visual plans.
  * **The Crew (The Toolset):** A collection of specialized tools that execute specific tasks like generating an image (Imagen), animating a scene (Veo), synthesizing a voice (Chirp), or compiling video clips (MoviePy).

This blueprint documents the entire system, from setup to final rendering.

## 2\. System Architecture

The studio operates on a clean, three-layer architecture:

1.  **Configuration (`config.py`):** A single file to manage all project-specific variables, such as Google Cloud project IDs, storage buckets, and local file paths.
2.  **Core Engine (`tools/nyra_core.py`):** The central nervous system of the studio. It contains shared helper functions, model definitions, the schema generator, and the dynamic tool loader that discovers and registers all other tools.
3.  **Modular Toolset (`tools/nyra_*.py`):** A suite of consolidated Python modules, each responsible for a specific domain (e.g., `nyra_audio_tool.py`, `nyra_image_tools.py`). All tools are designed to be called by the AI director.
4.  **Pipeline Scripts (`run_*.py`):** High-level orchestration scripts that define a sequence of tasks to achieve a specific goal, from running a diagnostic check to producing a complete film.

## 3\. Installation and Setup

### 3.1. Prerequisites

  * Python 3.11
  * `git` (for installing specific library versions from source)
  * `ffmpeg` (must be installed on the system and accessible from the command line)

### 3.2. Configuration

Before running any scripts, you must edit the **`config.py`** file in the root directory and set the values for your specific Google Cloud project and local workspace.

### 3.3. Dependencies

Install all required Python libraries by running the following command from the root project directory. This command uses the `py -3.11` launcher to ensure dependencies are installed for the correct Python version.

```bash
py -3.11 -m pip install -r requirements.txt
```

## 4\. Core Toolset Reference

The following is a complete reference of all tools available in Nyra AI Studio.

### `tools/nyra_audio_tool.py`

The unified module for all audio generation.

  * **`generate_narration_audio(text_to_speak: str, output_path: str, voice_name: str, speaking_rate: float = 1.0, volume_gain_db: float = 0.0, sample_rate_hertz: int = 44100)`**

      * **Description:** An intelligent tool that generates speech. It automatically detects the length of the input text and uses the appropriate Google TTS API (standard for short text, Long Audio for scripts \>5000 bytes).
      * **Parameters:**
          * `text_to_speak`: The script to be narrated.
          * `output_path`: The local path to save the final `.wav` file.
          * `voice_name`: The TTS voice model to use (e.g., `'hi-IN-Chirp3-HD-Vindemiatrix'`).
          * `speaking_rate`: The speed of the narration (e.g., `0.95` for slightly slower).

  * **`generate_music(prompt: str, output_path: str, duration_seconds: int = 30, negative_prompt: str = None)`**

      * **Description:** Generates a high-quality instrumental music clip using Lyria.
      * **Parameters:**
          * `prompt`: A detailed description of the desired music (mood, genre, instruments).
          * `output_path`: The local path to save the final `.wav` file.
          * `duration_seconds`: The length of the music clip (max 30s).
          * `negative_prompt`: A list of elements to exclude (e.g., `"vocals, drums"`).

### `tools/nyra_image_tools.py`

The unified module for all still image generation and editing.

  * **`generate_image(model_name: str, prompt: str, output_path: str, aspect_ratio: AspectRatio, ...)`**

      * **Description:** Generates a still image using an Imagen model.
      * **Parameters:**
          * `model_name`: The specific Imagen model to use (e.g., `'imagen-4.0-ultra-generate-preview-06-06'`).
          * `prompt`: The text prompt describing the image.
          * `output_path`: The local path to save the `.png` file.
          * `aspect_ratio`: Must be one of the `AspectRatio` enum values (e.g., `'16:9'`).

  * **`edit_image(model_name: str, edit_mode: EditMode, output_path: str, prompt: str, ...)`**

      * **Description:** A powerful, multi-purpose tool for advanced image editing.
      * **Parameters:**
          * `model_name`: Always `'imagen-3.0-capability-001'`.
          * `edit_mode`: The type of edit to perform. Must be one of the `EditMode` enum values: `'bgswap'`, `'inpaint'`, `'subject_customization'`, etc.
          * `input_path`: The source image to be edited.
          * `subject_ref_path`: A reference image to maintain character identity in `'subject_customization'` mode.
          * `mask_path`: An image mask for `'inpaint'` mode.

  * **`split_and_layout_character_sheet(input_path: str, output_dir: str)`**

      * **Description:** A utility that takes a 3-view character sheet and splits it into separate, production-ready layout files.

### `tools/nyra_video_tools.py`

The unified module for all Veo video generation and editing.

  * **`generate_veo3_video(model_name: str, output_path: str, prompt: str, ...)`**

      * **Description:** Generates a fixed 8-second, high-quality video clip using a Veo 3 model. Can be used for Text-to-Video or Image-to-Video.
      * **Parameters:**
          * `model_name`: A Veo 3 model (e.g., `'veo-3.0-generate-preview'`).
          * `output_path`: The local path to save the `.mp4` file.
          * `prompt`: The text prompt describing the scene and motion.
          * `image_path`: (Optional) The path to a still image to animate (I2V mode).

  * **`generate_veo2_video(model_name: str, output_path: str, prompt: str, ...)`**

      * **Description:** Generates a 5-8 second video clip using a Veo 2 model.
      * **Parameters:** Same as `generate_veo3_video`, but for Veo 2 models.

### `tools/nyra_moviepy_tools.py`

The definitive module for advanced video compilation using the MoviePy library.

  * **`compile_with_moviepy_transition(clip_a_path, clip_b_path, matte_path, ...)`**

      * **Description:** The robust tool for joining two video clips with a custom, generative transition.
      * **Parameters:**
          * `clip_a_path`: The first video clip.
          * `clip_b_path`: The second video clip.
          * `matte_path`: The path to the black-and-white luma matte video that defines the transition's shape.

  * **`speedup_video(input_path, output_path, speed_factor)`**

      * **Description:** Speeds up a video clip. Used to adjust the timing of generated transition mattes.

### `tools/nyra_storyboarder.py`

The module for AI-driven planning and scriptwriting.

  * **`generate_documentary_script(topic: str, language: str)`**
      * **Description:** Uses Gemini to write a clean, narration-ready script in a specific documentary style, free of formatting artifacts.

### `tools/nyra_system_tools.py` & `tools/nyra_pose_tools.py`

These modules contain various essential utilities for file management, pose extraction (`extract_openpose_skeleton`), and basic video/audio processing (`loop_audio`, `mix_audio_tracks`, `compile_final_video`).

## 5\. Production Workflows & Strategies

The studio is designed to execute several high-level production workflows.

### The Master Production Workflow (`run_master_cosmic_production.py`)

This is the main end-to-end pipeline. It demonstrates the full power of the studio by chaining multiple phases together:

1.  **Audio Pre-Production:** It calls `generate_documentary_script` to create the script and `generate_narration_audio` to produce the master narration track.
2.  **Visual Planning:** It feeds the narration audio to Gemini to create the timestamped `visual_plan.json`, which contains a detailed `image_prompt` and `motion_prompt` for every shot.
3.  **Visual Production:** It iterates through the plan, first calling `generate_image` to create a static keyframe for each shot, then calling `generate_veo2_video` (in I2V mode) to animate that keyframe.
4.  **Post-Production:** It generates a library of custom transition mattes and then uses the `compile_with_moviepy_transition` tool to stitch all the animated clips together into the final video, synchronized with the master audio.

### The Character Consistency Workflow

This strategy, seen in scripts like `run_universal_storyboard_generator_v4.py`, prioritizes character consistency by:

1.  Generating a master character reference image using `generate_image`.
2.  Using `edit_image` with `edit_mode='subject_customization'` and the master image as a `subject_ref_path` to create new poses and expressions of the *same character*.

### The Direct-to-Video Workflow (`run_veo3_t2v_production.py`)

This is a faster, more streamlined workflow that:

1.  Uses Gemini to generate a visual plan with a single, combined `video_prompt` for each shot.
2.  Calls `generate_veo3_video` directly from this text prompt, skipping the intermediate still image step. This is faster but offers less fine-grained control over visual details.

## 6\. System Validation

The studio includes scripts for testing and validation.

  * **`run_system_diagnostics.py`:** This script should be run after any changes to the toolset. It loads every tool module and reports on its status, ensuring there are no missing dependencies or registration errors.
  * **`run_ai_driven_tool_validation.py`:** This is the ultimate integration test. It contains a sequence of dozens of natural language prompts that instruct the AI to call every single tool in the studio in a logical order, creating and processing assets from scratch. A 100% pass rate on this test confirms the entire system is fully operational.
