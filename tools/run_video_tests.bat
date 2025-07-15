@echo off
ECHO [Nyra AI Studio] - Part 2: Video Tools Validation
ECHO =================================================================

REM --- Step 1: Setup Test Environment ---
ECHO.
ECHO [PHASE 1] Setting up test environment...
python -m tools.nyra_system_tools mkdir "output/part2_video_tests"
python -m tools.nyra_imagen_gen --model_name "imagen-4.0-generate-preview-06-06" --prompt "A photorealistic image of a futuristic motorcycle" --output_path "output/part2_video_tests/base_image.png"

REM --- Step 2: Test Core Video Generation ---
ECHO.
ECHO [PHASE 2] Testing Core Video Generation...

ECHO.
ECHO  -> Testing Veo 3 Text-to-Video...
python -m tools.nyra_veo3_gen --model_name "veo-3.0-generate-preview" --prompt "cinematic shot of a futuristic motorcycle driving through a neon city at night" --output_path "output/part2_video_tests/t2v_motorcycle.mp4"

ECHO.
ECHO  -> Testing Veo 2 Image-to-Video...
python -m tools.nyra_veo2_gen --model_name "veo-2.0-generate-001" --image_path "output/part2_video_tests/base_image.png" --output_path "output/part2_video_tests/i2v_motorcycle.mp4"

REM --- Step 3: Test Frames-to-Video Utility ---
ECHO.
ECHO [PHASE 3] Testing Frames-to-Video Utility...

ECHO.
ECHO  -> Creating frame sequence...
python -m tools.nyra_system_tools mkdir "output/part2_video_tests/frames"
python -m tools.nyra_system_tools cp "output/part2_video_tests/base_image.png" "output/part2_video_tests/frames/frame_001.png"
python -m tools.nyra_system_tools cp "output/part2_video_tests/base_image.png" "output/part2_video_tests/frames/frame_002.png"
python -m tools.nyra_system_tools cp "output/part2_video_tests/base_image.png" "output/part2_video_tests/frames/frame_003.png"

ECHO.
ECHO  -> Compiling frames...
python -m tools.nyra_system_tools frames2vid --input_dir "output/part2_video_tests/frames" --output_path "output/part2_video_tests/compiled_video.mp4" --fps 1

ECHO.
ECHO =================================================================
ECHO [Nyra AI Studio] - Part 2 Validation Complete.
ECHO =================================================================
PAUSE