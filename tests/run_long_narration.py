# run_long_narration.py
# A definitive workflow to handle long-form narration by using the
# Long Audio Synthesis API, saving to GCS, and then downloading the result.
# Version 3.0: Corrects GCS overwrite error by using a dynamic timestamp.

import os
import sys
from pathlib import Path
import time # DEFINITIVE FIX: Import the time module

# --- Path Setup & Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.SERVICE_ACCOUNT_KEY_PATH

# --- Tool Imports ---
from tools.nyra_system_tools import make_directory
from tools._helpers import download_from_gcs
from tools.nyra_long_audio import synthesize_long_audio

# ======================================================================
# >> NARRATION CONTROL PANEL <<
# ======================================================================

NARRATION_TEXT = """
प्राचीन भारत में जहाँ कुछ छोटे राज्य थे जिन्हें जनपद कहा जाता था, वहीं कुछ बड़े और शक्तिशाली साम्राज्य भी थे जिन्हें महाजनपद के नाम से जाना जाता था। इन्हीं 16 महाजनपदों में से एक था मगध, जहाँ 544 ईसा पूर्व में हर्यक राजवंश के बिंबिसार मात्र 15 वर्ष की आयु में सिंहासन पर बैठे।
बिंबिसार के पिता अंग प्रदेश के राजा ब्रह्मदत्त के हाथों पराजित हुए थे। अपने पिता की हार का बदला लेने के लिए, बिंबिसार ने अंग प्रदेश पर हमला किया और राजा ब्रह्मदत्त को हराकर उसे मगध साम्राज्य का हिस्सा बना लिया। इस जीत के बाद अंग प्रदेश के बंदरगाह मगध के नियंत्रण में आ गए, जिससे मगध का समुद्री व्यापार काफी बढ़ गया और मगध दिन-ब-दिन समृद्ध होता गया।
बिंबिसार एक दूरदर्शी शासक था। वह जानता था कि मगध को शक्तिशाली बनाने के लिए उसे दूसरे राज्यों के साथ मैत्रीपूर्ण संबंध बनाने होंगे। इसलिए उसने कोसल की राजकुमारी कोसला देवी से विवाह किया। इस विवाह के बाद कोसल और मगध की शत्रुता समाप्त हो गई और कोसल की ओर से काशी प्रांत बिंबिसार को दहेज के रूप में दिया गया। काशी के आने से मगध के राजस्व में भारी वृद्धि हुई। इसके बाद बिंबिसार ने वृज्जि के लिच्छवी राजवंश की राजकुमारी चेल्लना और मध्य पंजाब के मद्र राजवंश की राजकुमारी खेमा से भी विवाह किया। इन वैवाहिक संबंधों से बिंबिसार ने इन राज्यों के साथ अपने संबंध मजबूत कर लिए।
उस समय अवंती साम्राज्य मगध का सबसे बड़ा प्रतिद्वंद्वी था। बिंबिसार ने अवंती पर कई बार आक्रमण किया लेकिन हर बार युद्ध का कोई परिणाम नहीं निकला। अंत में, बिंबिसार ने अवंती के राजा प्रद्योत की ओर मित्रता का हाथ बढ़ाया।
बिंबिसार की सबसे बड़ी उपलब्धि उसका कुशल प्रशासन था। उस समय मगध साम्राज्य में 800 गाँव थे। हर गाँव में एक सभा होती थी और उस सभा के मुखिया को 'ग्रामक' कहा जाता था। बिंबिसार ने कर संग्रह के लिए एक सुव्यवस्थित प्रणाली स्थापित की थी और उसने न्यायिक, सैन्य और वित्तीय प्रशासन के लिए उच्च अधिकारियों की नियुक्ति की थी। उसने अपने लोगों और अपने साम्राज्य की रक्षा के लिए अंग प्रांत में एक नौसेना का भी निर्माण किया था।
बिंबिसार बौद्ध और जैन दोनों धर्मों का समर्थन करता था। उसने इन धर्मों के भिक्षुओं के लिए मुफ्त सुविधाओं की व्यवस्था की थी, जिसके कारण उसे 'जनता का राजा' कहा जाने लगा।
बौद्ध धर्म के अनुसार, बिंबिसार अपने पुत्र अजातशत्रु को अपना उत्तराधिकारी मानता था और उसने अजातशत्रु को अंग प्रांत की जिम्मेदारी सौंपी थी। लेकिन अजातशत्रु एक महत्वाकांक्षी राजकुमार था। गौतम बुद्ध के विरोधी देवदत्त के उकसाने पर उसने अपने पिता बिंबिसार की हत्या कर दी। हालाँकि, जैन धर्मग्रंथों के अनुसार, अजातशत्रु ने अपने पिता को कैद कर लिया था और बाद में बिंबिसार ने आत्महत्या कर ली थी।
अपने पति की मृत्यु के दुःख में कोसला देवी का भी निधन हो गया। अपनी बहन की मृत्यु से क्रोधित होकर, कोसल के राजा प्रसेनजित ने काशी को अजातशत्रु से वापस ले लिया। इसके बाद अजातशत्रु और प्रसेनजित के बीच युद्ध हुआ जिसमें अजातशत्रु पराजित हुआ और उसे बंदी बना लिया गया। बाद में, प्रसेनजित ने संबंधों को बनाए रखने के लिए अजातशत्रु को रिहा कर दिया और अपनी 17 वर्षीय बेटी वज्रा का विवाह अजातशत्रु से कर दिया, और काशी को फिर से दहेज के रूप में दे दिया।
प्रसेनजित की मृत्यु के बाद, अजातशत्रु ने कोसल पर हमला किया और उसे मगध साम्राज्य में मिला लिया। इसके बाद, अजातशत्रु ने वज्जि साम्राज्य की ओर अपना ध्यान केंद्रित किया और उसकी राजधानी वैशाली पर हमला करके उसे मगध में मिला लिया।
इतिहास ने खुद को दोहराया जब अजातशत्रु के पुत्र उदायिन ने मगध की गद्दी पर बैठने के लिए अपने पिता की हत्या कर दी। बौद्ध वृत्तांतों के अनुसार, हर्यक साम्राज्य के हर अगले शासक को उसके अपने ही पुत्र ने मार डाला। इस राजनीतिक अस्थिरता के कारण जनता में असंतोष फैल गया और माना जाता है कि हर्यक साम्राज्य के अंतिम शासक नागदासक को उसके अपने ही लोगों ने मार डाला, जिससे शिशुनाग साम्राज्य का उदय हुआ।
"""

# Definitive high-quality settings
VOICE_NAME = "hi-IN-Chirp3-HD-Vindemiatrix"
SPEAKING_RATE = 0.95 # Set to slightly slower than normal speed.
PROJECT_DIR = Path(config.WORKSPACE_DIR) / "output/bimbisara_narration_long"

# DEFINITIVE FIX: Added a timestamp to the GCS URI to ensure it's always unique.
GCS_OUTPUT_URI = f"gs://{config.GCS_BUCKET_NAME}/long_audio_outputs/bimbisara_narration_{int(time.time())}.wav"
LOCAL_OUTPUT_PATH = PROJECT_DIR / "bimbisara_full_narration_long.wav"
# ======================================================================

def generate_long_narration():
    """Executes the long narration generation and download."""
    print("--- Initializing Long-Form Narration Generation ---")

    try:
        make_directory(str(PROJECT_DIR))

        # --- PHASE 1: Asynchronous Synthesis to GCS ---
        gcs_path = synthesize_long_audio(
            text_to_synthesize=NARRATION_TEXT,
            output_gcs_uri=GCS_OUTPUT_URI,
            voice_name=VOICE_NAME,
            speaking_rate=SPEAKING_RATE
        )
        if "FAILED" in str(gcs_path).upper(): raise RuntimeError(f"Long audio synthesis failed: {gcs_path}")

        # --- PHASE 2: Download Result from GCS to Local Workspace ---
        print(f"\n -> Downloading result from {gcs_path} to local machine...")
        download_from_gcs(
            gcs_uri=gcs_path,
            output_path=str(LOCAL_OUTPUT_PATH)
        )

    except Exception as e:
        print(f"\n--- ❌ WORKFLOW HALTED DUE TO CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return

    print("\n" + "="*80)
    print("--- ✅ Long-Form Narration Complete ---")
    print(f"--- Final narration audio available at: {LOCAL_OUTPUT_PATH} ---")

if __name__ == "__main__":
    generate_long_narration()