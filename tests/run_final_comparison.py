# run_final_comparison.py
# The definitive workflow to compare audio generated from the Google Cloud
# Console UI and the Python SDK using identical, high-quality parameters.

import os
import sys
from pathlib import Path

# --- Path Setup & Global Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports ---
from tools.nyra_system_tools import make_directory
from tools.nyra_chirp3 import generate_speech

# ======================================================================
# >> COMPARISON SCRIPT & PARAMETERS <<
# ======================================================================

# This exact story text must be used in both the UI and this script.
HINDI_STORY_TEXT = """
एक पुराने शहर की धूल भरी गली में, जहाँ वक्त भी ठहर कर सुस्ताता था, आरव नाम का एक युवा कुम्हार रहता था। उसके हाथ मिट्टी को छूते तो थे, पर गढ़ते थे सपने। उसका सपना था एक ऐसा दीया बनाना, जिसकी रोशनी कभी मध्यम न पड़े, जो हर तूफ़ान में जलता रहे। लोगों ने उसका उपहास किया, कहा कि ऐसा असंभव है। पर आरव अपनी धुन में लगा रहा। दिन बीते, महीने गुज़रे, और उसकी उँगलियाँ मिट्टी से खेलते-खेलते थकने लगीं।

एक रात, जब वो लगभग हार मान चुका था, उसे अपने दादाजी के शब्द याद आए, "बेटा, असली जादू मिट्टी में नहीं, बनाने वाले के विश्वास में होता है।" उस रात, आरव ने अपनी पूरी आत्मा उस मिट्टी में डाल दी। उसने अपनी आशा, अपनी निराशा, और अपने अटूट विश्वास को मिलाकर एक नया दीया गढ़ा।

जब शहर दीवाली के जश्न में डूबा था, एक तेज़ आंधी आई और सारे दीये बुझ गए। अँधेरे में सिर्फ एक लौ टिमटिमा रही थी—आरव के दीये की। उस एक दीये की रोशनी ने पूरे मोहल्ले को रोशन कर दिया। उस दिन लोगों ने समझा कि सबसे टिकाऊ चीज़ मिट्टी या आग से नहीं, बल्कि कभी न हार मानने वाले जज़्बे से बनती है।
"""

# Parameters matching your screenshot
VOICE_NAME = "hi-IN-Chirp3-HD-Vindemiatrix" #
SPEAKING_RATE = 1.0 #
VOLUME_GAIN_DB = 0.0 #
SAMPLE_RATE_HERTZ = 44100 #

# --- File Paths ---
PROJECT_DIR = Path(config.WORKSPACE_DIR) / "output/final_comparison"
SDK_OUTPUT_FILENAME = "sdk_generated_story.wav" # Changed to WAV
STORY_TEXT_FILENAME = "story_for_test.txt"
# ======================================================================

def run_final_comparison():
    """
    Saves the story text for convenience and generates the same story
    via the SDK for a direct audio comparison.
    """
    print("--- Initializing Final UI vs. SDK Comparison Workflow ---")
    
    try:
        make_directory(str(PROJECT_DIR))
        
        story_file_path = PROJECT_DIR / STORY_TEXT_FILENAME
        story_file_path.write_text(HINDI_STORY_TEXT, encoding='utf-8')
        print(f"\n-> Story text saved to '{story_file_path}' for your convenience.")

        sdk_output_path = PROJECT_DIR / SDK_OUTPUT_FILENAME
        
        print("\n-> Now generating audio from the same text using the Python script...")
        result = generate_speech(
            text_to_speak=HINDI_STORY_TEXT,
            output_path=str(sdk_output_path),
            voice_name=VOICE_NAME,
            speaking_rate=SPEAKING_RATE,
            volume_gain_db=VOLUME_GAIN_DB,
            sample_rate_hertz=SAMPLE_RATE_HERTZ
        )
        
        if "FAILED" in str(result):
            raise RuntimeError(f"SDK speech synthesis failed: {result}")

    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "="*80)
    print("--- ✅ Comparison Workflow Complete ---")
    print("\nNext Steps:")
    print(f"1. Go to the Cloud Console UI and generate audio using the text from '{story_file_path}'.")
    print(f"2. The script has generated its version here: '{sdk_output_path}'.")
    print("3. Compare the two high-quality WAV audio files.")
    print("="*80)

if __name__ == "__main__":
    run_final_comparison()