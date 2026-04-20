import os
import sys
import logging
import re
from dotenv import load_dotenv

# --- WINDOWS ENCODING NORMALIZATION ---
# Force UTF-8 output on Windows to prevent UnicodeEncodeError with international characters
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# --- NEURAL PATH ALIGNMENT ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Load credentials from root .env with Force Refresh
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

# Mute third-party noise for a professional console experience
logging.getLogger("pyngrok").setLevel(logging.ERROR)
logging.getLogger("gradio").setLevel(logging.ERROR)
# Ensures modular imports work correctly across the ContentFlow structure
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import our decoupled backend modules
from app.auth.identity import verify_login, create_user
from app.script_writer.ai_agents import generate_script, refine_script, enhance_prompt, analyze_media_reference, export_project_bible, extract_speech_only, neural_chat_stream
from app.voice_studio.tts_engine import synthesize_voice, VOICE_OPTIONS, VOICE_NAMES, transcribe_media
from app.media_studio.video_generator import render_b_roll, generate_static_asset
import gradio as gr

# --- CUSTOM THEME: PROFESSIONAL PRODUCTION SUITE ---
custom_theme = gr.themes.Monochrome(
    neutral_hue="slate",
    primary_hue="indigo",
).set(
    body_background_fill="#111827",
    block_background_fill="#1F2937",
    background_fill_secondary="#374151",
    background_fill_primary="#1F2937",
    block_border_width="1px",
    block_border_color="#374151",
    button_primary_background_fill="#4F46E5",
    body_text_color="#D1D5DB",
    block_label_text_color="#9CA3AF",
    block_title_text_color="#F9FAFB",
    input_background_fill="#374151",
    input_border_color="#4B5563",
)

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif !important; }
.gradio-container { background: #111827 !important; }
h1 { color: #F9FAFB !important; text-align: left !important; font-size: 20px !important; font-weight: 600 !important; letter-spacing: -0.3px !important; }
h2, h3, h4 { color: #F9FAFB !important; text-align: left !important; font-weight: 600 !important; }
label span { color: #9CA3AF !important; font-weight: 500 !important; font-size: 13px !important; }

.login-card {
    margin: 8vh auto !important;
    border: 1px solid #374151 !important;
    padding: 40px 36px !important;
    border-radius: 10px !important;
    width: 420px !important;
    max-width: 92vw !important;
    box-sizing: border-box !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
    background: #1F2937 !important;
}

/* Chatbot */
.chatbot p, .chatbot span, .chatbot div { color: #F9FAFB !important; font-size: 15px !important; }
[data-testid="user"] { background: #4F46E5 !important; border-radius: 14px 14px 2px 14px !important; }
[data-testid="user"] * { color: white !important; }
[data-testid="bot"] { background: #1F2937 !important; border: 1px solid #374151 !important; border-radius: 14px 14px 14px 2px !important; }
[data-testid="bot"] * { color: #F9FAFB !important; }
.chatbot .wrap { background: transparent !important; }

/* Buttons */
.gradio-container button.primary {
    background: #4F46E5 !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px !important;
    border-radius: 7px !important;
}
.gradio-container button:not(.primary) {
    background: #374151 !important;
    color: #E5E7EB !important;
    border: 1px solid #4B5563 !important;
    border-radius: 7px !important;
}
.gradio-container button:hover {
    opacity: 0.92 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 3px 10px rgba(79, 70, 229, 0.25) !important;
}

/* Tab strip */
.tab-nav button {
    font-weight: 500 !important;
    font-size: 13.5px !important;
    letter-spacing: 0.1px !important;
    color: #9CA3AF !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 16px !important;
}
.tab-nav button.selected {
    color: #F9FAFB !important;
    border-bottom: 2px solid #4F46E5 !important;
    background: transparent !important;
}
"""

# --- UI LOGIC ROUTERS ---
def handle_login(username, password):
    if verify_login(username, password):
        # Returns: Update Login View (Hide), Update Dashboard View (Show), Status Message
        return gr.update(visible=False), gr.update(visible=True), f"Welcome, {username}!"
    return gr.update(visible=True), gr.update(visible=False), "❌ Invalid Credentials"

def handle_register(username, password):
    if create_user(username, password):
        return "✅ Account created! You can now log in."
    return "❌ Username already exists."

# --- BUILD THE UI ---
with gr.Blocks(title="ContentFlow Studio", theme=custom_theme, css=CSS) as demo:
    
    # LOGIN SCREEN
    with gr.Column(visible=True) as login_view:
        with gr.Column(elem_classes="login-card"):
            gr.Markdown("<h2 style='text-align: center; color: white; margin-bottom: 5px; font-weight: 700;'>ContentFlow Studio</h2>")
            gr.Markdown("<p style='text-align: center; color: #9CA3AF; font-size: 14px; margin-top: 0; margin-bottom: 25px;'>Production Suite &mdash; Sign in to continue</p>")
            
            auth_user = gr.Textbox(label="Username", placeholder="Enter username")
            auth_pass = gr.Textbox(label="Password", type="password", placeholder="Enter password")
            auth_status = gr.Markdown("")
            
            with gr.Row():
                login_btn = gr.Button("Sign In", variant="primary")
                register_btn = gr.Button("Create Account")

    # MAIN DASHBOARD
    with gr.Column(visible=False) as dashboard_view:
        gr.Markdown("""
<div style='display:flex; align-items:center; justify-content:space-between; padding:16px 8px 12px 8px; border-bottom:1px solid #1F2937; margin-bottom:12px;'>
  <div>
    <span style='font-size:22px; font-weight:800; letter-spacing:-0.8px; background:linear-gradient(90deg,#818CF8,#60A5FA); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;'>ContentFlow</span><span style='font-size:22px; font-weight:400; color:#6B7280; letter-spacing:-0.3px;'> Studio</span>
    <div style='font-size:11px; color:#374151; letter-spacing:2px; text-transform:uppercase; font-weight:500; margin-top:2px;'>Production Suite</div>
  </div>
  <div style='font-size:11px; color:#374151; letter-spacing:1px; font-weight:500;'>v2.0</div>
</div>
""")
        
        with gr.Tabs() as main_tabs:
            
            # TAB 1: SCRIPT WRITER
            with gr.Tab("Script Writer", id="production_hub"):
                gr.Markdown("### Content Planning")
                gr.Markdown("> Enter your topic below. The system will generate a content strategy and a ready-to-record script.")
                
                with gr.Row():
                    with gr.Column(scale=3):
                        topic_input = gr.Textbox(label="Topic", placeholder="Enter your content topic, or upload a reference file below...", lines=4)
                    with gr.Column(scale=1):
                        media_topic = gr.File(label="Reference File", file_types=["image", "video"])
                
                with gr.Row():
                    lang_input = gr.Dropdown(
                        choices=["English", "Kannada", "Hindi", "Marathi", "Tamil", "Telugu", "Malayalam", "Bengali"],
                        value="English",
                        label="Language",
                        scale=1
                    )
                    platform_input = gr.Dropdown(choices=["YouTube", "Vertical (Shorts/TikTok)", "LinkedIn", "Instagram"], value="YouTube", label="Platform", scale=1)
                    tone_input = gr.Dropdown(choices=["Cinematic", "Viral/High-Energy", "Educational", "Funny/Comedic", "Emotional", "Motivational", "Corporate"], value="Cinematic", label="Tone", scale=1)
                
                master_btn = gr.Button("Generate", variant="primary")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("#### Strategy & Hooks")
                        strategy_output = gr.Textbox(label="Content Strategy", lines=15, interactive=True)
                    with gr.Column(scale=3):
                        gr.Markdown("#### Script")
                        script_output = gr.Textbox(label="Teleprompter Script", lines=15, interactive=True)
                
                with gr.Row():
                    with gr.Column(scale=3):
                        gr.Markdown("#### Shot List")
                        blueprint_output = gr.Markdown("The scene breakdown will appear here after generation.")
                    with gr.Column(scale=2, variant="panel"):
                        gr.Markdown("#### Edit Script")
                        refine_input = gr.Textbox(label="Edit Instruction", placeholder="e.g. 'Make it shorter', 'Add a call to action'...")
                        with gr.Row():
                            refine_btn = gr.Button("Apply Edits", variant="secondary")
                            script_only_btn = gr.Button("Regenerate Script", variant="secondary")

                # --- ORCHESTRATION LOGIC ---
                def _build_blueprint_from_script(full_script):
                    import re as _re
                    if full_script.startswith("❌") or "Error" in full_script:
                        return full_script, f"> [!CAUTION]\n> **Blueprint failed.**\n>\n> {full_script}"

                    blueprint = "| Time | Scene | 👁️ Visual | 🎙️ Audio |\n|---|---|---|---|\n"
                    lines = full_script.split("\n")
                    scene_count = 1
                    for line in lines:
                        if "[Visual]" in line or "[Audio]" in line:
                            ts_match = _re.search(r'\[(\d+:\d+)\s*-\s*(\d+:\d+)\]', line)
                            timestamp = f"{ts_match.group(1)} – {ts_match.group(2)}" if ts_match else "—"
                            vis = line.split("[Visual]")[1].split("[Audio]")[0].replace(":", "").strip()[:80] if "[Visual]" in line else "—"
                            aud = line.split("[Audio]")[1].replace(":", "").strip()[:80] if "[Audio]" in line else "—"
                            blueprint += f"| {timestamp} | {scene_count} | {vis} | {aud} |\n"
                            scene_count += 1
                    
                    if scene_count == 1:
                        blueprint = "_Blueprint generation requires structured scenes._"
                    return full_script, blueprint

                def master_orchestration_router(topic, media_file, language, platform, tone):
                    from app.script_writer.ai_agents import generate_strategy, generate_script_direct
                    from app.voice_studio.audio_engine import audio_engine
                    
                    target_topic = topic or "Automated viral content"
                    
                    # 🧠 FULL PRODUCTION (Unified Workflow)
                    if media_file:
                        yield "👁️ Analyzing visual media...", None, "🏗️ Waiting for Strategy..."
                        vision_context = audio_engine.analyze_silent_video(media_file.name, num_frames=5, tone=tone, language=language)
                        if "Error" in vision_context:
                            yield f"❌ Vision Error: {vision_context}", None, None
                            return
                        target_topic = f"{topic}\n\n[VISUAL CONTEXT]:\n{vision_context}"
                    
                    cur_strat = ""
                    for partial in generate_strategy(target_topic, platform, tone, language):
                        cur_strat = partial
                        yield cur_strat, None, "🧠 Thinking..."
                    
                    cur_script = ""
                    for partial in generate_script_direct(cur_strat, language):
                        cur_script = partial
                        yield cur_strat, cur_script, "🏗️ Building Blueprint..."
                    
                    _, blueprint = _build_blueprint_from_script(cur_script)
                    yield cur_strat, cur_script, blueprint

                def script_only_router(strategy, language):
                    from app.script_writer.ai_agents import generate_script_direct
                    curr = ""
                    for partial in generate_script_direct(strategy, language):
                        curr = partial
                        yield curr, "🏗️ Rebuilding Blueprint..."
                    _, blueprint = _build_blueprint_from_script(curr)
                    yield curr, blueprint

                master_btn.click(
                    fn=master_orchestration_router, 
                    inputs=[topic_input, media_topic, lang_input, platform_input, tone_input], 
                    outputs=[strategy_output, script_output, blueprint_output]
                )
                
                script_only_btn.click(fn=script_only_router, inputs=[strategy_output, lang_input], outputs=[script_output, blueprint_output])
                refine_btn.click(fn=refine_script, inputs=[script_output, refine_input], outputs=script_output)

            # TAB 2: MEDIA STUDIO
            with gr.Tab("Media Studio", id="canvas_hub"):
                gr.Markdown("### Visual Asset Creator")
                with gr.Row():
                    with gr.Column(scale=1):
                        sync_canvas_btn = gr.Button("Pull from Script", size="sm")
                        ref_input = gr.File(label="Style Reference", file_types=["image", "video"])
                        magic_enhance_check = gr.Checkbox(label="Style Matching", value=True)
                        
                    with gr.Column(scale=2):
                        scene_input = gr.Textbox(label="Description", placeholder="Describe the scene, subject, or visual...", lines=5)
                        output_mode = gr.Radio(["Image", "Video"], label="Output Type", value="Video")
                        render_btn = gr.Button("Create Asset", variant="primary")
                
                image_output = gr.Image(label="Output Image", visible=False, type="filepath")
                video_output = gr.Video(label="Output Video", visible=False)
                canvas_status = gr.Markdown("Ready.")

                sync_canvas_btn.click(fn=lambda x: x, inputs=script_output, outputs=scene_input)

                def smooth_canvas_router(prompt, file, mode, magic_on, topic):
                    final_prompt = prompt
                    safe_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower()) if topic else "asset"
                    
                    if file:
                        yield "AI Analyzing reference...", gr.update(visible=False), gr.update(visible=False)
                        style_blueprint = analyze_media_reference(file.name)
                        final_prompt = f"{prompt} | Style: {style_blueprint}" if prompt else style_blueprint

                    yield f"Synthesizing {mode}...", gr.update(visible=False), gr.update(visible=False)
                    try:
                        if mode == "Image":
                            result = generate_static_asset(final_prompt, topic=safe_topic)
                        else:
                            result = render_b_roll(final_prompt, topic=safe_topic)
                        
                        if result:
                            if mode == "Image":
                                yield f"{mode} Synthesis Complete!", gr.update(value=result, visible=True), gr.update(visible=False)
                            else:
                                yield f"{mode} Synthesis Complete!", gr.update(visible=False), gr.update(value=result, visible=True)
                        else:
                            yield f"{mode} Synthesis Failed.", gr.update(visible=False), gr.update(visible=False)
                    except Exception as e:
                        yield f"Error: {str(e)}", gr.update(visible=False), gr.update(visible=False)

            render_btn.click(
                fn=smooth_canvas_router,
                inputs=[scene_input, ref_input, output_mode, magic_enhance_check, topic_input],
                outputs=[canvas_status, image_output, video_output]
            )

            # TAB 3: VOICE STUDIO
            with gr.Tab("Voice Studio", id="audio_hub"):
                with gr.Tabs():
                    with gr.Tab("Voiceover"):
                        gr.Markdown("### Voiceover Recorder")
                        with gr.Row():
                            sync_btn = gr.Button("Load Script", size="sm", variant="secondary")
                            extract_btn = gr.Button("Narration Only", size="sm", variant="secondary")
                        
                        audio_text = gr.Textbox(label="Text", lines=8, placeholder="Paste or type the text to record...")
                        voice_input = gr.Dropdown(choices=VOICE_NAMES, value="English - Male", label="Voice")
                        synth_btn = gr.Button("Record Voiceover", variant="primary")
                        audio_output = gr.Audio(label="Playback")
                        
                        sync_btn.click(fn=lambda x: x, inputs=script_output, outputs=audio_text)
                        extract_btn.click(fn=extract_speech_only, inputs=script_output, outputs=audio_text)
                        synth_btn.click(fn=synthesize_voice, inputs=[audio_text, voice_input, topic_input], outputs=audio_output)
                    
                    with gr.Tab("Media Transcription"):
                        gr.Markdown("### Media File Processor")
                        gr.Markdown("> Upload any audio, video or image file to extract a text transcript or scene description.")
                        with gr.Row():
                            gr.Markdown("**A. Audio Transcription:** For interviews, vlogs, or talking-head clips.")
                            gr.Markdown("**B. Scene Description:** For cinematic shots, product clips, or posters without dialogue.")
                        
                        media_upload = gr.File(label="Upload File")
                        with gr.Row():
                            analysis_mode = gr.Radio(["Audio Transcription", "Visual Analysis (For Silent Videos)"], label="Processing Mode", value="Audio Transcription")
                            transcribe_lang = gr.Dropdown(choices=["Auto-Detect", "English", "Hindi", "Kannada", "Marathi"], value="Auto-Detect", label="Language")
                            vision_tone = gr.Dropdown(choices=["Cinematic", "Funny", "Emotional", "Motivational"], value="Cinematic", label="Tone")
                        
                        transcribe_btn = gr.Button("Process File", variant="primary")
                        transcribe_output = gr.Textbox(label="Result", lines=6)
                        send_synth_btn = gr.Button("Send to Voiceover", size="sm")
                        
                        transcribe_btn.click(fn=transcribe_media, inputs=[media_upload, transcribe_lang, analysis_mode, vision_tone], outputs=transcribe_output)
                        send_synth_btn.click(fn=extract_speech_only, inputs=transcribe_output, outputs=audio_text)

            # TAB 4: EXPORT
            with gr.Tab("Export", id="export_hub"):
                gr.Markdown("### Export Project")
                gr.Markdown("> Save your completed script and all asset references as a structured project file.")
                export_btn = gr.Button("Save Project File", variant="primary")
                export_status = gr.Markdown("")
                export_btn.click(fn=export_project_bible, inputs=[topic_input, script_output], outputs=export_status)

    # Wire up the Auth Buttons
    login_btn.click(fn=handle_login, inputs=[auth_user, auth_pass], outputs=[login_view, dashboard_view, auth_status])
    register_btn.click(fn=handle_register, inputs=[auth_user, auth_pass], outputs=auth_status)

if __name__ == "__main__":
    # Ensure all professional directories are ready
    os.makedirs(os.path.join(BASE_DIR, "export", "audio"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "export", "visuals"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "export", "projects"), exist_ok=True)
    # Compatibility link for legacy media access if needed
    os.makedirs(os.path.join(BASE_DIR, "export", "media"), exist_ok=True)
    
    # --- ULTRA-STRICT MOBILE TUNNEL (NGROK) ---
    public_url = None
    os.system('cls' if os.name == 'nt' else 'clear')
    
    try:
        from pyngrok import ngrok, conf
        token = os.getenv("NGROK_AUTHTOKEN")
        if token and token.strip() and token != "your_token_here":
            # Clean Start: Kill all existing sessions
            ngrok.kill() 
            clean_token = token.strip()
            
            # Diagnostic: Verifying Identity
            masked = "*" * (len(clean_token) - 4) + clean_token[-4:]
            print(f"📡 [NGROK] Initializing Strict Cloud Portal (Token: {masked})...")
            
            conf.get_default().auth_token = clean_token
            public_url = ngrok.connect(8000).public_url
    except Exception as e:
        print("\n" + "!"*60)
        print("❌ [STRICT ERROR] NGROK AUTHENTICATION FAILED")
        print(f"DETAILS: {e}")
        print("\n💡 ACTION REQUIRED:")
        print("1. Go to: https://dashboard.ngrok.com/get-started/your-authtoken")
        print("2. Click 'Reset Authtoken' to get a fresh code.")
        print("3. Paste the NEW code into your .env file.")
        print("!"*60 + "\n")

    import socket
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        network_ip = s.getsockname()[0]
        s.close()
    except:
        network_ip = "localhost"

    print("\n" + "╔" + "═"*58 + "╗")
    print("║          CONTENTFLOW STUDIO  |  PRODUCTION SUITE          ║")
    print("╠" + "═"*58 + "╣")
    print(f"║  💻 Local:    http://localhost:8000                        ║")
    print(f"║  📶 Network:  http://{network_ip:<27}      ║")
    if public_url:
        print(f"║  🔗 Remote:   {public_url:<43} ║")
    else:
        print(f"║  🔗 Remote:   [Not Active — Check NGROK_AUTHTOKEN]         ║")
    print("╚" + "═"*58 + "╝\n")

    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=8000,
            allowed_paths=[os.path.join(BASE_DIR, "export")]
        )
    finally:
        if public_url:
            print("\n♻️ Shutting down tunnel...")
            try:
                ngrok.disconnect(public_url)
                ngrok.kill()
            except:
                pass
