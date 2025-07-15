@echo off
ECHO [Nyra AI Studio] - Part 3: Audio Tools Validation
ECHO =================================================================

REM --- Step 1: Setup Test Environment ---
ECHO.
ECHO [PHASE 1] Setting up test environment...
python -m tools.nyra_system_tools mkdir "output/part3_audio_tests"

REM --- Step 2: Test Music Generation ---
ECHO.
ECHO [PHASE 2] Testing Lyria Music Generation...
python -m tools.nyra_lyria --prompt "A mysterious, ambient synthwave track with a slow, driving beat, suitable for exploring a cyberpunk city" --output_path "output/part3_audio_tests/cyberpunk_theme.mp3" --duration 20

REM --- Step 3: Test Speech Generation ---
ECHO.
ECHO [PHASE 3] Testing Chirp Text-to-Speech...
python -m tools.nyra_chirp3 --text "All systems are stable. The modular tool library has been fully validated." --output_path "output/part3_audio_tests/final_report.mp3"

ECHO.
ECHO =================================================================
ECHO [Nyra AI Studio] - Part 3 Validation Complete.
ECHO All audio files have been saved to the 'output/part3_audio_tests' directory.
ECHO =================================================================
PAUSE