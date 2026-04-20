import os
import asyncio
from .audio_engine import audio_engine

# Voice ID map: display name -> (edge-tts voice ID, target language code)
VOICE_OPTIONS = {
    # --- English ---
    "English - Male":           ("en-US-GuyNeural",       "en"),
    "English - Female":         ("en-US-JennyNeural",     "en"),
    "English - British Female": ("en-GB-SoniaNeural",     "en"),

    # --- Hindi ---
    "Hindi - Female":           ("hi-IN-SwaraNeural",     "hi"),
    "Hindi - Male":             ("hi-IN-MadhurNeural",    "hi"),

    # --- Tamil ---
    "Tamil - Female":           ("ta-IN-PallaviNeural",   "ta"),
    "Tamil - Male":             ("ta-IN-ValluvarNeural",  "ta"),

    # --- Telugu ---
    "Telugu - Female":          ("te-IN-ShrutiNeural",   "te"),
    "Telugu - Male":            ("te-IN-MohanNeural",    "te"),

    # --- Bengali ---
    "Bengali - Female":         ("bn-IN-TanishaaNeural", "bn"),
    "Bengali - Male":           ("bn-IN-BashkarNeural",  "bn"),

    # --- Kannada ---
    "Kannada - Female":         ("kn-IN-SapnaNeural",    "kn"),
    "Kannada - Male":           ("kn-IN-GaganNeural",    "kn"),

    # --- Marathi ---
    "Marathi - Female":         ("mr-IN-AarohiNeural",   "mr"),
    "Marathi - Male":           ("mr-IN-ManoharNeural",  "mr"),

    # --- Malayalam ---
    "Malayalam - Female":       ("ml-IN-SobhanaNeural",  "ml"),
    "Malayalam - Male":         ("ml-IN-MidhunNeural",   "ml"),

    # --- Gujarati ---
    "Gujarati - Female":        ("gu-IN-DhwaniNeural",   "gu"),
    "Gujarati - Male":          ("gu-IN-NiranjanNeural", "gu"),

    # --- Urdu ---
    "Urdu - Female":            ("ur-IN-GulNeural",      "ur"),
    "Urdu - Male":              ("ur-IN-SalmanNeural",   "ur"),

}

# Flat list of display names for the dropdown
VOICE_NAMES = list(VOICE_OPTIONS.keys())


def _translate_text(text: str, target_lang: str) -> str:
    """
    Translates text to target_lang using the Neural Brain (Groq/Gemini).
    Returns the original text on failure to ensure speech synthesis still proceeds.
    """
    if target_lang == "en":
        return text

    print(f"[AUDIO STUDIO] Requesting Neural Translation (Target: {target_lang})...")
    
    from litellm import completion
    from app.script_writer.ai_agents import get_best_provider
    
    prov = get_best_provider()
    if prov == "GROQ":
        model_name = "groq/llama-3.3-70b-versatile"
        api_key = os.getenv("GROQ_API_KEY")
    elif prov == "GEMINI":
        model_name = "gemini/gemini-1.5-flash-latest"
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    else:
        # Fallback to English if no premium provider is configured
        print("[AUDIO STUDIO] No premium provider found for translation, using original text.")
        return text

    prompt = (
        f"You are a professional translator. Translate the following text strictly into the target language. "
        f"Target Language ISO Code: {target_lang}. "
        f"Output ONLY the translated text. Do not add explanations or quotes.\n\n"
        f"TEXT TO TRANSLATE:\n{text}"
    )

    try:
        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key
        )
        translated = response.choices[0].message.content.strip()
        print(f"[AUDIO STUDIO] Neural Translation Successful.")
        return translated
    except Exception as e:
        print(f"[AUDIO STUDIO] Neural Translation failed: {e}. Falling back to original.")
        return text


def synthesize_voice(text: str, voice_name: str, topic: str = None) -> str:
    """
    Modular Audio Studio: Translates text to target language if needed,
    then synthesizes speech with the selected Edge-TTS voice.
    """
    if not text:
        return None

    voice_id, target_lang = VOICE_OPTIONS.get(voice_name, ("en-US-GuyNeural", "en"))
    print(f"[AUDIO STUDIO] Synthesizing ({voice_name}) | lang={target_lang}")

    # Auto-translate if the voice language differs from the input (assumed English if not detected)
    text_to_speak = _translate_text(text, target_lang)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        file_path = loop.run_until_complete(audio_engine.synthesize(text_to_speak, voice=voice_id, prefix=topic))
        loop.close()
        return file_path
    except Exception as e:
        print(f"[AUDIO STUDIO] Synthesis Failed: {e}")
        return None


def transcribe_media(file_path: str, language_hint: str = "Auto-Detect", mode: str = "Audio Transcription", vision_tone: str = "Cinematic/Dramatic") -> str:
    """
    Intake hub: Routes uploaded media to either audio transcription or silent visual analysis.
    """
    if not file_path:
        return "No file provided"
        
    if mode == "Visual Analysis (For Silent Videos)":
        return audio_engine.analyze_silent_video(file_path, num_frames=5, tone=vision_tone, language=language_hint)
    
    LANG_CODE_MAP = {
        "Auto-Detect": None,
        "English": "en",
        "Hindi": "hi",
        "Kannada": "kn",
        "Malayalam": "ml",
        "Tamil": "ta",
        "Telugu": "te",
        "Marathi": "mr",
        "Gujarati": "gu",
        "Urdu": "ur",
        "Bengali": "bn"
    }
    
    lang_code = LANG_CODE_MAP.get(language_hint, None)
    
    try:
        return audio_engine.transcribe_video(file_path, language=lang_code)
    except Exception as e:
        return f"Processing error: {e}"
