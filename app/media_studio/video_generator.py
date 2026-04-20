import os
import requests
import time
from .generative_assets import canvas_engine

def render_b_roll(scene_prompt: str, aspect_ratio: str = "16:9", topic: str = None) -> str:
    """
    Modular Video Engine: Connects to the advanced Canvas Engine
    to generate cinematic footage from script cues.
    """
    print(f"[CANVAS HUB] 🎬 Generating B-Roll: {scene_prompt} ({aspect_ratio})")
    
    # Mapping user's simplified ratio strings to engine requirements
    ratio_map = {
        "16:9 (YouTube)": "16:9",
        "9:16 (Reels/Shorts)": "9:16"
    }
    target_ratio = ratio_map.get(aspect_ratio, aspect_ratio)
    
    try:
        # Use our existing high-performance engine for the actual work
        path = canvas_engine.generate_video(scene_prompt, ratio=target_ratio, prefix=topic)
        return path
    except Exception as e:
        print(f"[CANVAS HUB] Error: {e}")
        return None

def generate_static_asset(prompt: str, ratio: str = "1:1", topic: str = None) -> str:
    """
    Generates a high-quality static production asset.
    """
    try:
        path = canvas_engine.generate_image(prompt, ratio=ratio, prefix=topic)
        return path
    except Exception as e:
        print(f"[CANVAS HUB] Error: {e}")
        return None
