import os
import sys
import re
from datetime import datetime
from crewai import Crew, Process
import threading

# Ensure relative imports work
from app.script_writer.ai_agents import NeuralAgents as ContentAgents
# Note: ContentTasks is typically local to the old brain, 
# but if ai_agents.py includes the logic, we use that.
# For now, I'll keep the import as a TODO if tasks.py was also moved.
# Actually, I'll update it to the new modular agents.

class LogCatcher:
    def __init__(self, filename="crew_output.log"):
        self.filename = filename
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write("System Ready. Neural Link Established.\n")
    def write(self, message):
        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write(message)
    def flush(self):
        pass

# Define base directory relative to this service file
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def execute_production_pipeline(topic: str, style: str, platform: str, **kwargs):
    latest_script_path = os.path.join(BASE_DIR, "export", "latest_script.txt")
    
    # Initialize LogCatcher
    sys.stdout = LogCatcher(filename=os.path.join(BASE_DIR, "app", "crew_output.log"))
    
    try:
        print(f"\n> [PIPELINE] 🚀 INITIALIZING PRODUCTION: '{topic}' [{platform.upper()}]")
        agents = ContentAgents()
        tasks = ContentTasks()
        
        # STAGE 1: BRAIN (Blitz Mode Optimized)
        print("> [STAGE 1] BRAIN HUB: Generating Content Strategy...")
        
        script_res = ""
        is_fast = kwargs.get('fast_mode', True) # Default to true for speed
        
        if is_fast:
            print("[NEURAL] ⚡ BLITZ MODE ACTIVE: Direct High-Speed Drafting...")
            # Bypassing Crew wrapper to avoid executor shutdown errors
            prompt = f"""Draft a professional production-ready script for '{topic}'.
            TARGET PLATFORM: {platform}
            TARGET LENGTH: {"60 seconds" if platform in ["shorts", "instagram"] else "8-12 minutes"}
            ARTISTIC STYLE: {style}
            
            Structure with these markers:
            #### Viral Hooks
            #### Master Script (with [Visual cues] and Narration)
            """
            
            try:
                # Use the dynamic LLM factory via the property
                response = agents.primary_llm.call(messages=[{"role": "user", "content": prompt}])
                script_res = str(response)
            except Exception as e:
                if "shutdown" in str(e).lower():
                    print("[NEURAL] 🔄 REBOOTING CONNECTION: Executor was shut down. Retrying...")
                    # Re-initialize agents to get a fresh connection pool
                    agents = ContentAgents()
                    response = agents.primary_llm.call(messages=[{"role": "user", "content": prompt}])
                    script_res = str(response)
                else:
                    raise e
        else:
            print("[NEURAL] 🔍 RESEARCH MODE: Deep-diving into web trends...")
            if not os.getenv("SERPER_API_KEY"):
                print("[WARNING] SERPER_API_KEY missing. Falling back to Direct Path...")
                prompt = f"Draft a professional production-ready script for '{topic}' on {platform} in {style} style."
                response = agents.primary_llm.call(messages=[{"role": "user", "content": prompt}])
                script_res = str(response)
            else:
                r_task = tasks.research_task(agents.researcher_agent(), topic)
                d_task = tasks.drafting_task(agents.scriptwriter_agent(), topic, platform, style)
                # Still using Crew for sequential research, but wrapped in a tighter executor scope
                crew = Crew(agents=[agents.researcher_agent(), agents.scriptwriter_agent()], tasks=[r_task, d_task], process=Process.sequential, verbose=False)
                script_res = str(crew.kickoff())

        # IMMEDIATE REVEAL: Write Stage 1 result so user can start reading the script
        interim_content = f"""# [1] BRAIN HUB: STRATEGY & SCRIPT
{script_res}

---
> [NEURAL SYNC] Stage 1 Complete. Drafting Visuals and Audio in background...
"""
        with open(latest_script_path, "w", encoding="utf-8") as f:
            f.write(interim_content)
        
        # PARALLEL STAGES (2 & 3)
        results = {"shot_list": "", "thumbnail": "", "audio_plan": "", "pacing": ""}
        
        def run_canvas_background():
            try:
                c_agents = ContentAgents()
                c_tasks = ContentTasks()
                s_task = c_tasks.shot_list_task(c_agents.visual_director_agent(), topic, style)
                t_task = c_tasks.thumbnail_task(c_agents.visual_director_agent(), topic)
                c_crew = Crew(agents=[c_agents.visual_director_agent()], tasks=[s_task, t_task], verbose=False)
                c_crew.kickoff()
                results["shot_list"] = str(c_crew.tasks[0].output.raw)
                results["thumbnail"] = str(c_crew.tasks[1].output.raw)
            except Exception as e:
                print(f"[ERROR] Stage 2 Fault: {e}")

        def run_audio_background():
            try:
                a_agents = ContentAgents()
                a_tasks = ContentTasks()
                ap_task = a_tasks.audio_plan_task(a_agents.audio_engineer_agent(), topic, style)
                pg_task = a_tasks.pacing_guide_task(a_agents.audio_engineer_agent(), topic)
                a_crew = Crew(agents=[a_agents.audio_engineer_agent()], tasks=[ap_task, pg_task], verbose=False)
                a_crew.kickoff()
                results["audio_plan"] = str(a_crew.tasks[0].output.raw)
                results["pacing"] = str(a_crew.tasks[1].output.raw)
            except Exception as e:
                print(f"[ERROR] Stage 3 Fault: {e}")

        th1 = threading.Thread(target=run_canvas_background)
        th2 = threading.Thread(target=run_audio_background)
        th1.start()
        th2.start()
        th1.join()
        th2.join()

        # FINAL ARCHIVE
        export_projects_dir = os.path.join(BASE_DIR, "export", "projects")
        os.makedirs(export_projects_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower())
        proj_file = os.path.join(export_projects_dir, f"bible_{safe_topic}_{timestamp}.md")
        
        final_bible = f"""# PRODUCTION BIBLE: {topic}
## Platform: {platform}
## Style: {style}

---

# [1] BRAIN HUB: STRATEGY & SCRIPT
{script_res}

---

# [2] CANVAS LAB: VISUAL DIRECTION
### Visual Cues
{results['shot_list']}

### Thumbnail Concepts
{results['thumbnail']}

---

# [3] AUDIO HUB: ATMOSPHERE & PACING
### Atmosphere
{results['audio_plan']}

### Pacing
{results['pacing']}
"""
        with open(proj_file, "w", encoding="utf-8") as f:
            f.write(final_bible)
        
        with open(latest_script_path, "w", encoding="utf-8") as f:
             f.write(final_bible)
            
        # Write a completion flag
        with open(os.path.join(BASE_DIR, "export", "status.txt"), "w") as f:
            f.write("COMPLETED")
            
        print(f"> [PIPELINE] Swarm Complete. Final Bible Archived at {proj_file}")

    except Exception as e:
        error_msg = f"ERROR: Swarm Failure: {e}"
        print(f"\n[{error_msg}]")
        with open(latest_script_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
    finally:
        sys.stdout = sys.__stdout__

def execute_iteration(instruction: str):
    path = os.path.join(BASE_DIR, "export", "latest_script.txt")
    if not os.path.exists(path):
        raise Exception("No existing production found to iterate.")
        
    with open(path, "r", encoding="utf-8") as f:
        original_script = f.read()

    print(f"> [PIPELINE] 🪄 INITIALIZING MAGIC ITERATION: '{instruction}'")
    agents = ContentAgents()
    tasks = ContentTasks()
    
    iter_task = tasks.iteration_task(agents.iteration_agent(), original_script, instruction)
    crew = Crew(agents=[agents.iteration_agent()], tasks=[iter_task], verbose=False)
    
    refined_script = str(crew.kickoff())
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(refined_script)
        
    return refined_script

def process_voice_pitch(transcript: str):
    print(f"> [PIPELINE] [VOICE PITCH] PROCESSING: '{transcript}'")
    agents = ContentAgents()
    tasks = ContentTasks()
    
    pitch_task = tasks.voice_intent_task(agents.universal_intel_agent(), transcript)
    crew = Crew(agents=[agents.universal_intel_agent()], tasks=[pitch_task], verbose=False)
    
    topic = str(crew.kickoff()).strip().replace('"', '')
    return topic
