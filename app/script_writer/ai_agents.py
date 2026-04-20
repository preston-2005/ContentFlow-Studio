import os
import re
import sys
import time
import litellm
from crewai import Agent, LLM
from dotenv import load_dotenv

# Force UTF-8 output on Windows to prevent UnicodeEncodeError with emoji logs
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Migrate to new google-genai SDK
try:
    from google import genai as google_genai
    _genai_client = None
except ImportError:
    google_genai = None
    _genai_client = None

load_dotenv()

def _get_genai_client():
    global _genai_client
    if google_genai and _genai_client is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        _genai_client = google_genai.Client(api_key=api_key)
    return _genai_client

# --- DYNAMIC NEURAL LINK (High Performance Factory) ---

def get_best_provider():
    """Returns the best available provider. Returns NO_PROVIDER if none configured."""
    # Priority: Groq -> Gemini -> Ollama
    gsk = os.getenv("GROQ_API_KEY", "")
    aiza = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")

    if gsk and gsk.startswith("gsk_"):
        return "GROQ"
    if aiza and aiza.startswith("AIza"):
        return "GEMINI"
    # Only fallback to Ollama as a last resort; flag if truly nothing
    return "OLLAMA"

def get_modular_llm():
    """
    Fresh connection factory to avoid 'executor shutdown' errors.
    """
    prov = get_best_provider()
    
    if prov == "GROQ":
        return LLM(model="groq/llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
    elif prov == "GEMINI":
        # Force correct provider and model name
        return LLM(
            model="google_generative_ai/gemini-1.5-flash-latest", 
            api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        )
    else:
        # Fallback to Local Ollama - Ensure we use a model Ollama actually has
        return LLM(
            model="ollama/phi3", 
            base_url="http://localhost:11434"
        )

# --- CORE STRATEGY & SCRIPT LOGIC (Split Pipeline) ---

def generate_strategy_stream(topic: str, platform: str, tone: str, language: str = "English"):
    """
    Step 1: Generates a Marketing Strategy outline including viral titles, SEO keywords, and a bulleted outline.
    """
    print(f"[BRAIN] Generating Strategy for: '{topic}'")
    
    prompt = f"""Act as a Marketing Strategist.
Topic: {topic}
Platform: {platform}
Tone: {tone}

Provide 3 viral titles, SEO keywords, and a bulleted video outline. 
CRITICAL: You MUST write the entire response strictly in the following language: {language}. 
Keep it punchy and professional.
"""
    try:
        prov = get_best_provider()
        if prov == "GROQ":
            model_name = "groq/llama-3.3-70b-versatile"
            api_key = os.getenv("GROQ_API_KEY")
        elif prov == "GEMINI":
            model_name = "gemini/gemini-1.5-flash-latest"
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        else:
            model_name = "ollama/phi3"
            api_key = "none"

        response = litellm.completion(
            model=model_name, messages=[{"role": "user", "content": prompt}],
            api_key=api_key, stream=True
        )

        full_text = ""
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            full_text += content
            yield full_text
    except Exception as e:
        error_msg = str(e)
        if "getaddrinfo failed" in error_msg or "Errno 11001" in error_msg:
            yield "❌ Connection Error: Your computer cannot reach the AI servers. Please ensure you are connected to the Internet and not blocked by a VPN/Firewall."
        else:
            yield f"Strategy Error: {error_msg}"

def generate_script_direct(strategy: str, language: str = "English"):
    """
    Step 2: Takes the Strategy outline and drafts a teleprompter script.
    """
    print(f"[BRAIN] Starting Streaming Draft based on strategy...")
    
    prompt = f"""Act as a Scriptwriter. Using this marketing strategy, write the word-for-word spoken teleprompter script.

STRATEGY OUTLINE:
{strategy}

STRICT FORMAT RULES:
    - Start each scene with a timestamp range, e.g. [0:00 - 0:10]
    - On the SAME line, add [Visual]: <camera/visual instruction> and [Audio]: <spoken narration>
    - Keep each scene 5-15 seconds long
    - Aim for 8-12 scenes total
    - CRITICAL: If a specific location, city, or culture is mentioned, ensure the [Visual] descriptions are highly authentic to that exact place (e.g., local landmarks, authentic architecture, accurate geography). Do NOT use generic imagery.
    - Example format:
      [0:00 - 0:08] [Visual]: Aerial drone shot over the historic red-tiled roofs of Mangalore [Audio]: Have you ever wondered what makes this place different?

    CRITICAL: You MUST write the complete spoken teleprompter script strictly in the following language: {language}.
    
    Write the complete script now:
    """
    
    try:
        prov = get_best_provider()
        print(f"[BRAIN] Active Provider: {prov}")

        if prov == "GROQ":
            model_name = "groq/llama-3.3-70b-versatile"
            api_key = os.getenv("GROQ_API_KEY")
        elif prov == "GEMINI":
            model_name = "gemini/gemini-1.5-flash-latest"
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        else:  # OLLAMA
            model_name = "ollama/phi3"
            api_key = "none"

        # Use LiteLLM directly for native streaming support
        response = litellm.completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            stream=True
        )

        full_text = ""
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            full_text += content
            yield full_text

    except Exception as e:
        err_msg = str(e)
        if "getaddrinfo failed" in err_msg or "Errno 11001" in err_msg:
            user_msg = "❌ Connection Error: Your computer cannot reach the AI servers. Please ensure you are connected to the Internet and not blocked by a VPN/Firewall."
        elif "10061" in err_msg or "refused" in err_msg.lower():
            user_msg = (
                "[ERROR] Brain Connection Failed: Ollama is not running.\n\n"
                "Fix Options:\n"
                "1. Start Ollama: run `ollama serve` in a terminal.\n"
                "2. OR add a valid Gemini API key (starts with `AIza`) to your `.env` file as `GEMINI_API_KEY=...`.\n"
                "3. OR add a valid Groq API key (starts with `gsk_`) to your `.env` file as `GROQ_API_KEY=...`."
            )
        else:
            user_msg = f"[Brain Error]: {err_msg}"
        yield user_msg

def neural_chat_stream(message: str, history: list):
    """
    Standard Conversational AI loop for the Neural Chat. 
    Separate from the structured Script Lab. Converts Gradio history into LiteLLM format.
    """
    from litellm import completion
    print(f"[CHAT] Neural Message: '{message}'")
    
    messages = [
        {"role": "system", "content": "You are the ContentFlow Neural Brain. You are a conversational AI production assistant. Be helpful, professional, and concise. Do not force script generation formatting unless explicitly asked."}
    ]
    
    # Add history
    for human, assistant in history:
        messages.append({"role": "user", "content": human})
        if assistant:
            messages.append({"role": "assistant", "content": assistant})
            
    messages.append({"role": "user", "content": message})
    
    try:
        prov = get_best_provider()
        if prov == "GROQ":
            model_name = "groq/llama-3.3-70b-versatile"
            api_key = os.getenv("GROQ_API_KEY")
        elif prov == "GEMINI":
            model_name = "gemini/gemini-1.5-flash-latest"
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        else:
            model_name = "ollama/phi3"
            api_key = "none"

        response = completion(
            model=model_name,
            messages=messages,
            api_key=api_key,
            stream=True
        )

        full_text = ""
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            full_text += content
            yield full_text
    except Exception as e:
        yield f"Chat Error: {str(e)}"

def enhance_prompt(raw_prompt: str) -> str:
    """
    Magic Prompting: Transforms simple text into professional cinematic engineering.
    """
    print(f"[BRAIN] Enhancing Visual Prompt: '{raw_prompt}'")
    guideline = (
        "Turn this prompt into a highly detailed, cinematic description for an AI image generator. "
        "Include lighting, camera depth, and high-fidelity details. "
        "CRITICAL: If a specific place, city, or culture is mentioned, make sure to explicitly describe authentic "
        "geographical, architectural, and cultural elements native to that exact location to prevent generic outputs. "
        "Output ONLY the enhanced prompt."
    )
    try:
        llm = get_modular_llm()
        response = llm.call(messages=[{"role": "user", "content": f"{guideline}\n\nPROMPT: {raw_prompt}"}])
        return str(response)
    except Exception as e:
        return raw_prompt # Fallback to raw

def refine_script(current_script: str, instruction: str) -> str:
    """
    Magic Iteration: Refines an existing script based on directorial instructions.
    """
    print(f"[BRAIN] 🪄 Refining Script with instruction: '{instruction}'")
    prompt = f"""You are a master script editor. Refine the manuscript below based on this instruction: '{instruction}'.
    
    ORIGINAL MANUSCRIPT:
    {current_script}
    
    Refine it while keeping the professional structure.
    """
    try:
        llm = get_modular_llm()
        response = llm.call(messages=[{"role": "user", "content": prompt}])
        return str(response)
    except Exception as e:
        return f"Refinement Error: {str(e)}"

def analyze_media_reference(file_path: str) -> str:
    """
    Vision Sense: Analyzes an uploaded image or video to extract style/content prompts.
    Uses the new google-genai SDK.
    """
    print(f"[BRAIN VISION] Analyzing reference: {file_path}")
    if not file_path or not os.path.exists(file_path):
        return "No reference file detected."

    try:
        client = _get_genai_client()
        if not client:
            return "Vision Analysis unavailable: google-genai SDK not installed."

        # Upload file to Gemini Cloud (Temporary)
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        uploaded_file = client.files.upload(
            path=file_path,
        )

        # Performance wait for video processing
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(1)
            uploaded_file = client.files.get(name=uploaded_file.name)

        vision_prompt = (
            "Analyze this media file. Output a highly detailed, cinematic prompt that captures the MOOD, COLORS, "
            "CHARACTERS, and SCENE structure. Focus on being descriptive enough for an AI image/video generator. "
            "Output ONLY the descriptive prompt."
        )

        response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=[uploaded_file, vision_prompt],
        )
        return response.text
    except Exception as e:
        print(f"[BRAIN VISION] Analysis Failed: {e}")
        return f"Vision Analysis Error: {str(e)}"

# --- MODULAR AI AGENTS ---

class NeuralAgents:
    def __init__(self):
        self.llm = get_modular_llm()

    def specialist(self, role, goal, backstory):
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            allow_delegation=False,
            verbose=False,
            llm=self.llm
        )

# Unified interface for the Gradio UI (MODULAR ALIGNMENT + STREAMING)
def generate_strategy(topic: str, platform: str, tone: str, language: str = "English"):
    """
    Executes the streaming modular pipeline for Step 1: Strategy.
    """
    for partial in generate_strategy_stream(topic, platform, tone, language):
        yield partial

def generate_script(strategy: str, language: str = "English"):
    """
    Executes the streaming modular pipeline for Step 2: Script Drafting.
    """
    full_script = ""
    for partial in generate_script_direct(strategy, language):
        full_script = partial
        yield full_script
    
    # Final Archive
    try:
        os.makedirs("export/projects", exist_ok=True)
        clean_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower()) if topic else "untitled"
        filename = f"bible_{clean_topic}.md"
        with open(os.path.join("export", "projects", filename), "w", encoding="utf-8") as f:
            f.write(full_script)
    except:
        pass

def export_project_bible(topic, script):
    """
    Executive Packaging: Compiles all project assets into a single Markdown Bible.
    """
    if not topic or not script:
        return "[Export] Nothing to export. Please generate a script first."
    
    os.makedirs("export/projects", exist_ok=True)
    clean_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower()) if topic else "untitled"
    filename = f"bible_{clean_topic}.md"
    file_path = os.path.join("export", "projects", filename)
    
    bible_content = f"""# PRODUCTION BIBLE: {topic.upper()}

## PRODUCTION DATE: {time.strftime("%Y-%m-%d %H:%M:%S")}

## MASTER MANUSCRIPT
{script}

## ASSETS DISPATCHED
- All related voiceovers and visuals can be found in `export/media/`
- This project is synchronized with ContentFlow Studio.

---
*Generated by the ContentFlow Neural Hub*
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(bible_content)
        
    return f"[OK] Production Bible exported to: {file_path}"

def extract_speech_only(full_script: str) -> str:
    """
    Neural Speech Filter: Strips visual markers and directions, leaving only the spoken narration.
    """
    if not full_script: return ""
    print("[BRAIN] 🎙️ Extracting Narratival Speech...")
    
    prompt = f"""Extract ONLY the spoken words/narration from the script below. 
    Remove all [Visual] markers, Scene titles, camera directions, and labels. 
    Output only the clean text that should be read by the selected voice.
    
    SCRIPT:
    {full_script}
    """
    try:
        llm = get_modular_llm()
        response = llm.call(messages=[{"role": "user", "content": prompt}])
        return str(response)
    except Exception as e:
        print(f"[BRAIN] Speech Extraction Failed: {e}")
        return full_script # Fallback
