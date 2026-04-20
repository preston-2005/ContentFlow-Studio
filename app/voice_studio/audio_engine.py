import os
from datetime import datetime
import edge_tts
import whisper
import cv2
import base64
import litellm
from langdetect import detect, DetectorFactory

# Set seed for reproducible language detection
DetectorFactory.seed = 0

class AudioEngine:
    """
    Local Text-to-Speech Engine and Video Transcription for ContentFlow AI.
    Features: Auto-Language detection and high-performance neural synthesis.
    """
    def __init__(self):
        self.whisper_model = None
        # Map ISO language codes to specific high-quality Edge-TTS voices
        self.LANGUAGE_VOICE_MAP = {
            'kn': 'kn-IN-SapnaNeural',   # Kannada
            'hi': 'hi-IN-SwaraNeural',   # Hindi
            'mr': 'mr-IN-AarohiNeural',  # Marathi
            'kok': 'mr-IN-AarohiNeural', # Konkani (closest match)
            'ml': 'ml-IN-SobhanaNeural', # Malayalam
            'beary': 'ml-IN-SobhanaNeural', # Beary (closest match)
            'ta': 'ta-IN-PallaviNeural', # Tamil
            'te': 'te-IN-ShrutiNeural',  # Telugu
            'en': 'en-US-GuyNeural',     # English Default
            'es': 'es-ES-ElviraNeural',  # Spanish
            'fr': 'fr-FR-DeniseNeural',  # French
            'de': 'de-DE-KatjaNeural',   # German
        }

        self.GENDER_VOICE_MAP = {
            'boy': 'en-US-GuyNeural',
            'girl': 'en-US-JennyNeural',
            'agent': 'en-US-SteffanNeural'
        }

    async def synthesize(self, text, voice="auto", output_path=None, prefix=None):
        """
        Convert text to a professional audio file asynchronously.
        Supports 'auto' mode or explicit 'boy'/'girl' keys.
        """
        if not output_path:
            # Standardize and use ABSOLUTE paths for Gradio reliability
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            media_dir = os.path.join(base_dir, "export", "audio") # Proper audio folder
            os.makedirs(media_dir, exist_ok=True)
            
            # Use prefix for descriptive naming (e.g., Asset_Topic_Timestamp)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Refined Slugify: lowercase and alphanumeric only
            import re
            clean_prefix = re.sub(r'[^a-zA-Z0-9]', '_', prefix.lower()) if prefix else "voiceover"
            filename = f"{clean_prefix}_{timestamp}.mp3"
            
            output_path = os.path.join(media_dir, filename)
            # Always return the absolute path for Gradio
            return_path = os.path.abspath(output_path)
        else:
            return_path = os.path.abspath(output_path)

        # Handle Gender Select or Auto Detect
        if voice in self.GENDER_VOICE_MAP:
            voice = self.GENDER_VOICE_MAP[voice]
        elif voice == "auto":
            try:
                lang = detect(text)
                voice = self.LANGUAGE_VOICE_MAP.get(lang, 'en-US-GuyNeural')
            except Exception:
                voice = 'en-US-GuyNeural'

        print(f"[AUDIO] Synthesizing Voiceover ({voice}) -> {output_path}")
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            return return_path
        except Exception as e:
            print(f"[AUDIO] Synthesis Failed: {e}")
            return None

    def transcribe_video(self, file_path, language=None):
        """
        Extract text from an audio or video file using local Whisper.
        Includes Smart Filter to catch silence hallucinations.
        """
        print(f"[AUDIO] Transcribing content from -> {file_path} (Language config: {language or 'Auto'})")
        try:
            # Upgrade model to 'small' - much better at regional Indian languages than 'base'
            if not getattr(self, "whisper_model", None) or getattr(self, "current_model_size", None) != "small":
                print("[AUDIO] Loading Whisper 'small' model for high accuracy...")
                self.whisper_model = whisper.load_model("small")
                self.current_model_size = "small"
            
            options = {
                "task": "transcribe",
                "verbose": False
            }
            if language:
                options["language"] = language
                
            result = self.whisper_model.transcribe(file_path, **options)
            
            # --- ANTI-HALLUCINATION LOGIC ---
            segments = result.get("segments", [])
            transcript = result["text"].strip()
            
            if not segments:
                return "⚠️ No audio detected in this file."
            
            # 1. Check for silence/no-speech probability
            # If the AI is more than 60% sure there is no speech, we flag it.
            avg_no_speech = sum([s['no_speech_prob'] for s in segments]) / len(segments)
            
            # 2. Check for "Garbage Pattern" hallucinations
            # Hallucinations often repeat the same character or use non-standard symbols like 
            is_repetitive = len(transcript) > 5 and len(set(transcript)) < (len(transcript) * 0.1)
            has_corrupt_chars = "" in transcript or "{" in transcript and "}" in transcript and len(transcript) < 20
            
            if avg_no_speech > 0.65 or is_repetitive or has_corrupt_chars or not transcript:
                print(f"[AUDIO] Potential Hallucination Detected (Confidence Error: {avg_no_speech:.2f}). Blocking gibberish.")
                return "⚠️ **Speech Analysis Failed:** No clear dialogue detected. If this is a silent video or a cinematic shot, please switch to **'Visual Analysis'** mode below."

            print(f"[AUDIO] ✅ Transcription Complete (Confidence: {(1-avg_no_speech)*100:.1f}%).")
            return transcript
        except Exception as e:
            err_msg = str(e)
            if "reshape" in err_msg or "0 elements" in err_msg:
                print(f"[AUDIO] ❌ Whisper Tensor Error: {err_msg}. This usually means the video is silent or too short.")
                return "⚠️ **Transcription Failed:** This video appears to have no valid audio track or is too short. Please use **'Visual Analysis'** mode for silent clips."
            
            print(f"[AUDIO] ❌ Transcription Failed: {e}")
            return f"❌ Audio processing error: {str(e)}"

    def analyze_silent_video(self, file_path, num_frames=4, tone="Cinematic/Dramatic", language="English"):
        """
        Uses OpenCV to rip frames from the video timeline and sends them to Gemini 1.5 Flash Vision
        to autonomously generate a descriptive narrative voiceover script.
        """
        print(f"[VISION] Analyzing Visual Media -> {file_path} [{tone} Style]")
        try:
            base64_frames = []
            
            # Detect whether it is an image or video
            ext = os.path.splitext(file_path.lower())[1]
            if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                # 1A. Static Image Processing
                frame = cv2.imread(file_path)
                if frame is not None:
                    # Compress
                    frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA) if frame.shape[1] > 1000 else frame
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    b64 = base64.b64encode(buffer).decode('utf-8')
                    base64_frames.append(b64)
                    print("[VISION] Detected Static Image. Extracted 1 main frame.")
            else:
                # 1B. Extract Video Frames
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    return "❌ Error: Could not parse visual media file for vision analysis."
                    
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                if total_frames > 0:
                    skip = max(1, total_frames // num_frames)
                    count = 0
                    while cap.isOpened() and len(base64_frames) < num_frames:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, count * skip)
                        ret, frame = cap.read()
                        if not ret: break
                        
                        # Compress to manageable size
                        frame = cv2.resize(frame, (640, 360))
                        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        b64 = base64.b64encode(buffer).decode('utf-8')
                        base64_frames.append(b64)
                        count += 1
                cap.release()

            if not base64_frames:
                return "❌ Error: Video is empty or unreadable by internal Vision Engine."
                
            # 2. Query Gemini Vision or Groq Vision via LiteLLM
            print(f"[VISION] Extracted {len(base64_frames)} keyframes. Transmitting to Neural Vision Hub...")
            
            gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            groq_key = os.getenv("GROQ_API_KEY")
            
            if gemini_key:
                active_model = "gemini/gemini-1.5-flash-latest"
                active_key = gemini_key
            elif groq_key:
                active_model = "groq/meta-llama/llama-4-scout-17b-16e-instruct"
                active_key = groq_key
            else:
                return "❌ Error: Neither GEMINI_API_KEY nor GROQ_API_KEY found in .env. Computer Vision requires one of these."

            # Construct multimodal prompt payload
            instruction = (
                f"Act as a narrator. You are looking at visual media (a video or an image poster). "
                f"Describe exactly what the essence of it is in a smooth, creative voiceover script so that an AI voice can narrate it appropriately. "
                f"The tone of your narration MUST strictly be: {tone}. "
                f"You MUST output the narration text strictly in the following language: {language}. "
                "DO NOT include any preamble, introduction, translation, or 'Here is your script' text. "
                "Provide only the lines that should be spoken by a narrator in the target language."
            )
            content_payload = [{"type": "text", "text": instruction}]
            for b64 in base64_frames:
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

            response = litellm.completion(
                model=active_model,
                messages=[{"role": "user", "content": content_payload}],
                api_key=active_key
            )
            
            script = response.choices[0].message.content
            print("[VISION] ✅ Narrative Script Generated Successfully.")
            return str(script)
            
        except Exception as e:
            print(f"[VISION] ❌ Analysis Failed: {e}")
            return f"❌ Vision Error: {e}"

# Singleton Pattern for global access
audio_engine = AudioEngine()
