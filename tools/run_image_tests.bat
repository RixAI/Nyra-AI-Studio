@echo off
ECHO [Nyra AI Studio] - Part 1: Image Generation ^& Editing Validation
ECHO =================================================================

REM --- Step 1: Setup Test Environment ---
ECHO.
ECHO [PHASE 1] Setting up test environment...
python -m tools.nyra_system_tools mkdir "output/part1_image_tests"

REM --- Step 2: Generate Base Assets ---
ECHO.
ECHO [PHASE 2] Generating base character and style reference images...
python -m tools.nyra_imagen_gen --model_name "imagen-4.0-generate-preview-06-06" --prompt "full body photo of a female astronaut in a sleek white sci-fi suit, standing on a barren, red-rock alien planet, detailed, photorealistic" --output_path "output/part1_image_tests/astronaut.png" --aspect_ratio "9:16"
python -m tools.nyra_imagen_gen --model_name "imagen-4.0-generate-preview-06-06" --prompt "a vibrant, colorful, abstract painting in the style of Wassily Kandinsky" --output_path "output/part1_image_tests/style_ref.png" --aspect_ratio "9:16"

REM --- Step 3: Test Editing Modes ---
ECHO.
ECHO [PHASE 3] Testing Image Editing Modes...

ECHO.
ECHO  -> Testing Background Swap...
python -m tools.nyra_imagen_edit --mode bgswap --input_path "output/part1_image_tests/astronaut.png" --prompt "the same astronaut standing in a lush, green, alien jungle" --output_path "output/part1_image_tests/astronaut_jungle.png"

ECHO.
ECHO  -> Testing Subject-Based Edit...
python -m tools.nyra_imagen_edit --mode subject --subject_ref_path "output/part1_image_tests/astronaut.png" --prompt "the same astronaut, but her suit is now sleek, black carbon fiber" --output_path "output/part1_image_tests/astronaut_blacksuit.png"

ECHO.
ECHO  -> Testing Style Transfer...
python -m tools.nyra_imagen_edit --mode style --input_path "output/part1_image_tests/astronaut.png" --style_ref_path "output/part1_image_tests/style_ref.png" --prompt "An astronaut on an alien world, in an abstract style" --output_path "output/part1_image_tests/astronaut_styled.png"

ECHO.
ECHO.
ECHO  ###########################- ACTION REQUIRED -###########################
ECHO  The script is now paused.
ECHO.
ECHO  You MUST create a MASK file for the inpainting test.
ECHO  Save a black image with a white shape covering the helmet visor to:
ECHO  'output\part1_image_tests\helmet_mask.png'
ECHO.
ECHO  Once the file is saved, press any key to continue.
ECHO  #########################################################################
PAUSE

ECHO.
ECHO  -> Testing Inpainting...
python -m tools.nyra_imagen_edit --mode inpaint --input_path "output/part1_image_tests/astronaut.png" --mask_path "output/part1_image_tests/helmet_mask.png" --prompt "a cracked helmet visor with a reflection of a distant galaxy" --output_path "output/part1_image_tests/astronaut_cracked_visor.png"

ECHO.
ECHO.
ECHO  ###########################- ACTION REQUIRED -###########################
ECHO  The script is now paused again.
ECHO.
ECHO  You MUST create a SCRIBBLE file for the pose test.
ECHO  Save a simple line drawing of a figure in a dynamic pose to:
ECHO  'output\part1_image_tests\pose_scribble.png'
ECHO.
ECHO  Once the file is saved, press any key to continue.
ECHO  #########################################################################
PAUSE

ECHO.
ECHO  -> Testing Scribble-to-Image...
python -m tools.nyra_imagen_edit --mode scribble --scribble_ref_path "output/part1_image_tests/pose_scribble.png" --prompt "a photorealistic astronaut in a sleek white suit in a dynamic action pose" --output_path "output/part1_image_tests/astronaut_posed.png"

ECHO.
ECHO =================================================================
ECHO [Nyra AI Studio] - Part 1 Validation Complete.
ECHO Check the 'output/part1_image_tests' directory for results.
ECHO =================================================================
PAUSE