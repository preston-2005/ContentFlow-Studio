import os
import requests
from PIL import Image, ImageEnhance
import io

try:
    from rembg import remove
except ImportError:
    remove = None

class CanvasEngine:
    def __init__(self):
        """
        Initializes the Canvas Generative Engine.
        """
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    def generate_image(self, prompt: str, output_path: str = None, ratio: str = "1:1", prefix: str = None) -> str:
        """
        Generates a professional asset with 'Magic Prompting' enhancement.
        Prioritizes DALL-E if key is present, falls back to Flux (Pollinations) for speed.
        """
        # Proper Quality Enhancement (Magic Prompting)
        quality_keywords = "4k, ultra-hd, cinematic lighting, professional composition, highly detailed, visually authentic to any mentioned location, accurate geography and specific cultural markers, sharp focus"
        enhanced_prompt = f"{prompt}, {quality_keywords}"
        
        print(f"[CANVAS] Generating Proper Asset: {prompt} (Ratio: {ratio})")
        
        # 1. Map Aspect Ratio to Dimensions
        dimensions = {
            "16:9": (1280, 720, "1792x1024"),
            "9:16": (720, 1280, "1024x1792"),
            "1:1": (1024, 1024, "1024x1024"),
            "4:3": (1024, 768, "1024x1024"),
            "3:4": (768, 1024, "1024x1024")
        }
        width, height, dalle_size = dimensions.get(ratio, (1024, 1024, "1024x1024"))
            
        if not output_path:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            output_dir = os.path.join(base_dir, "export", "visuals")
            os.makedirs(output_dir, exist_ok=True)
            import time
            import random
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Use prefix for descriptive naming if provided
            import re
            clean_prefix = re.sub(r'[^a-zA-Z0-9]', '_', prefix.lower()) if prefix else "asset"
            filename = f"{clean_prefix}_{timestamp}.png"
            
            output_path = os.path.join(output_dir, filename)
            return_path = output_path  # Always return absolute path for Gradio
        else:
            return_path = os.path.abspath(output_path)

        if self.openai_api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_api_key)
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=enhanced_prompt,
                    size=dalle_size,
                    quality="hd",
                    n=1,
                )
                image_url = response.data[0].url
                img_data = requests.get(image_url, timeout=60).content
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                print(f"[CANVAS] DALL-E image saved: {return_path}")
                return return_path
            except Exception as e:
                print(f"[CANVAS] DALL-E HD Failed: {e}. Falling back...")

        # FALLBACK: Free Pollinations Flux Generation
        import urllib.parse
        import random

        def _build_url(p: str) -> str:
            encoded = urllib.parse.quote(p)
            seed = random.randint(1, 1000000)
            return (f"https://image.pollinations.ai/prompt/{encoded}"
                    f"?width={width}&height={height}&seed={seed}&model=flux&nologo=true")

        def _ai_rewrite_prompt(original: str) -> str:
            """
            Universal AI-powered prompt rewriter.
            When any prompt is rejected (brand names, trademarks, policy blocks),
            uses the existing LLM stack to rewrite it as a vivid visual description.
            This works for ANY subject — motorcycles, phones, cars, people, places, etc.
            """
            print(f"[CANVAS] AI Rewriting prompt for universal compatibility...")
            try:
                from litellm import completion
                from app.script_writer.ai_agents import get_best_provider
                provider = get_best_provider()
                if provider == "GROQ":
                    model = "groq/llama-3.3-70b-versatile"
                    api_key = os.getenv("GROQ_API_KEY")
                elif provider == "GEMINI":
                    model = "gemini/gemini-1.5-flash-latest"
                    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                else:  # OLLAMA fallback
                    model = "ollama/phi3"
                    api_key = None

                system_msg = (
                    "You are an expert AI image prompt engineer. "
                    "Your job is to rewrite any given subject into a rich, descriptive visual prompt "
                    "that works with image generation APIs. "
                    "Replace all brand names, trademarks, and proper nouns with vivid physical descriptions. "
                    "Describe colors, shapes, materials, style, lighting, and mood. "
                    "Output ONLY the rewritten prompt. No explanation. No preamble."
                )
                user_msg = f"Rewrite this image prompt into a brand-neutral visual description: '{original}'"

                kwargs = dict(
                    model=model,
                    messages=[{"role": "system", "content": system_msg},
                               {"role": "user", "content": user_msg}],
                    max_tokens=120,
                    temperature=0.4,
                )
                if api_key:
                    kwargs["api_key"] = api_key
                if provider == "OLLAMA":
                    kwargs["api_base"] = "http://localhost:11434"

                result = completion(**kwargs)
                rewritten = result.choices[0].message.content.strip()
                print(f"[CANVAS] AI rewrote prompt: '{rewritten[:80]}...'")
                return rewritten
            except Exception as e:
                print(f"[CANVAS] AI rewrite failed ({e}), using cleaned prompt fallback.")
                # Last-resort: strip likely brand patterns and add cinematic context
                import re
                cleaned = re.sub(r'\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\b', '', original)
                return f"a professional cinematic photograph of {cleaned.strip() or original}, dramatic lighting, 4k"

        try:
            print(f"[CANVAS] Requesting Pollinations image...")
            response = requests.get(_build_url(enhanced_prompt), timeout=90)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"[CANVAS] Image saved: {return_path}")
                return return_path
            else:
                print(f"[CANVAS] Pollinations returned HTTP {response.status_code} — invoking AI prompt rewriter...")
                rewritten = _ai_rewrite_prompt(prompt)
                retry_enhanced = f"{rewritten}, 4k, ultra-hd, cinematic lighting, professional composition, sharp focus"
                response2 = requests.get(_build_url(retry_enhanced), timeout=90)
                if response2.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response2.content)
                    print(f"[CANVAS] Retry succeeded with AI-rewritten prompt. Image saved: {return_path}")
                    return return_path
                else:
                    print(f"[CANVAS] Both attempts failed (HTTP {response2.status_code}).")
        except Exception as e:
            print(f"[CANVAS] Image Generation Failure: {e}")

        return None


    def generate_video(self, prompt: str, output_path: str = None, ratio: str = "16:9", prefix: str = None) -> str:
        """
        Generates a video from a text prompt.
        Prioritizes Replicate API if key is present, falls back to a free Pollinations-powered simulated video.
        Automatically detects scaling requirements (like 16:9 or 9:16).
        """
        print(f"[CANVAS] Generating video for prompt: {prompt} (Ratio: {ratio})")
        
        # 1. Parse Image Dimensions for fallback or API mapping
        width = 1280
        height = 720
        
        prompt_lower = f"{prompt} {ratio}".lower()
        if "16:9" in prompt_lower or "landscape" in prompt_lower:
            width = 1280
            height = 720
        elif "9:16" in prompt_lower or "portrait" in prompt_lower:
            width = 720
            height = 1280
        elif "4:3" in prompt_lower:
            width = 1024
            height = 768
        elif "3:4" in prompt_lower:
            width = 768
            height = 1024
        elif "1:1" in prompt_lower:
            width = 1024
            height = 1024
            
        import time
        import random
        if not output_path:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            output_dir = os.path.join(base_dir, "export", "visuals")
            os.makedirs(output_dir, exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Descriptive naming
            import re
            clean_prefix = re.sub(r'[^a-zA-Z0-9]', '_', prefix.lower()) if prefix else "video"
            filename = f"{clean_prefix}_{timestamp}.mp4"
            
            output_path = os.path.join(output_dir, filename)
            return_path = output_path  # Always return absolute path for Gradio
        else:
            return_path = os.path.abspath(output_path)

        replicate_key = os.getenv("REPLICATE_API_TOKEN")

        if replicate_key:
            try:
                import replicate
                client = replicate.Client(api_token=replicate_key)
                print("[CANVAS] Dispatching to Replicate Video Engine...")
                output = client.run(
                    "minimax/video-01",
                    input={"prompt": f"{prompt} (Aspect Ratio: {ratio})"},
                )
                video_url = output if isinstance(output, str) else output[0]
                vid_data = requests.get(video_url, timeout=120).content
                with open(output_path, 'wb') as f:
                    f.write(vid_data)
                return return_path
            except Exception as e:
                print(f"[CANVAS] Replicate Video Failed: {e}. Falling back to Pollinations Simulated Video...")

        # FALLBACK: Simulated Video (Pollinations image + OpenCV Ken Burns zoom)
        print("[CANVAS] Using Free Simulated Video Fallback Engine...")

        def _ai_rewrite_video_prompt(original: str) -> str:
            """Universal AI rewriter for video prompts — same logic as image rewriter."""
            print(f"[CANVAS] AI Rewriting video prompt for universal compatibility...")
            try:
                from litellm import completion
                from app.script_writer.ai_agents import get_best_provider
                provider = get_best_provider()
                if provider == "GROQ":
                    model, api_key = "groq/llama-3.3-70b-versatile", os.getenv("GROQ_API_KEY")
                elif provider == "GEMINI":
                    model, api_key = "gemini/gemini-1.5-flash-latest", os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                else:
                    model, api_key = "ollama/phi3", None

                kwargs = dict(
                    model=model,
                    messages=[
                        {"role": "system", "content": (
                            "You are a cinematic video prompt engineer. "
                            "Rewrite any subject into a vivid, brand-neutral visual scene description. "
                            "Replace all brand names and trademarks with physical descriptions of colors, shapes, style, motion, and mood. "
                            "Output ONLY the rewritten prompt. No explanation."
                        )},
                        {"role": "user", "content": f"Rewrite this video prompt into a brand-neutral cinematic scene: '{original}'"},
                    ],
                    max_tokens=120,
                    temperature=0.4,
                )
                if api_key:
                    kwargs["api_key"] = api_key
                if provider == "OLLAMA":
                    kwargs["api_base"] = "http://localhost:11434"

                result = completion(**kwargs)
                rewritten = result.choices[0].message.content.strip()
                print(f"[CANVAS] AI rewrote video prompt: '{rewritten[:80]}...'")
                return rewritten
            except Exception as e:
                print(f"[CANVAS] AI video rewrite failed ({e}), using cleaned fallback.")
                import re
                cleaned = re.sub(r'\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\b', '', original)
                return f"a cinematic shot of {cleaned.strip() or original}, dramatic lighting, 4k"

        def _fetch_and_render_video(source_prompt: str) -> str | None:
            """Fetches a Pollinations frame and renders a Ken Burns video from it."""
            import urllib.parse
            import cv2
            encoded_prompt = urllib.parse.quote(source_prompt)
            seed = random.randint(1, 1000000)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&model=flux&nologo=true"
            print(f"[CANVAS] Fetching source frame from Pollinations...")
            response = requests.get(url, timeout=90)
            if response.status_code != 200:
                print(f"[CANVAS] Pollinations frame fetch returned HTTP {response.status_code}")
                return None

            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            out_dir = os.path.join(base_dir, "export", "media")
            os.makedirs(out_dir, exist_ok=True)
            temp_img_path = os.path.join(out_dir, f"temp_{random.randint(1000,9999)}.jpg")

            with open(temp_img_path, 'wb') as f:
                f.write(response.content)

            img = cv2.imread(temp_img_path)
            if img is None:
                raise Exception("Could not decode image from Pollinations response")
            h, w = img.shape[:2]

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, 30.0, (w, h))
            frames = 90  # 3 seconds at 30fps
            for i in range(frames):
                scale = 1 + (i / (frames * 3))  # gentle Ken Burns zoom
                new_w = int(w / scale)
                new_h = int(h / scale)
                left = (w - new_w) // 2
                top = (h - new_h) // 2
                cropped = img[top:top+new_h, left:left+new_w]
                resized = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
                out.write(resized)
            out.release()

            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            return return_path

        try:
            result = _fetch_and_render_video(prompt)
            if result:
                print(f"[CANVAS] Simulated video saved: {return_path}")
                return result
            else:
                # Prompt was rejected — use AI rewriter and retry
                print(f"[CANVAS] Retrying with AI-rewritten video prompt...")
                rewritten = _ai_rewrite_video_prompt(prompt)
                result2 = _fetch_and_render_video(rewritten)
                if result2:
                    print(f"[CANVAS] Video retry succeeded. Saved: {return_path}")
                    return result2
                else:
                    print(f"[CANVAS] Both video attempts failed.")
                    return None
        except Exception as e:
            print(f"[CANVAS] Fallback Video Generation Failed: {e}")
            raise Exception(f"Video Generation failed: {str(e)}")


    def remove_background(self, input_image_path: str, output_image_path: str) -> str:
        """
        Applies a semantic ML model (Rembg) to strip away backgrounds 
        and applies high-contrast color grading for clickable thumbnails.
        """
        if not os.path.exists(input_image_path):
            return f"[ERROR] Source image not found: {input_image_path}"
            
        print(f"[PROCESS] Canvas Lab: Isolating subject: {input_image_path}")
        
        try:
            # 1. Semantic Background Removal
            with open(input_image_path, 'rb') as i:
                input_data = i.read()
                if remove:
                    no_bg_data = remove(input_data)
                    output_img = Image.open(io.BytesIO(no_bg_data)).convert("RGBA")
                else:
                    return "[ERROR] rembg library not found. Please install dependencies."
                
                # 2. Automated Color Grading (High Contrast / SAT)
                enhancer = ImageEnhance.Contrast(output_img)
                output_img = enhancer.enhance(1.4) # +40% contrast
                
                enhancer = ImageEnhance.Sharpness(output_img)
                output_img = enhancer.enhance(1.2)
                
                enhancer = ImageEnhance.Color(output_img)
                output_img = enhancer.enhance(1.3)
                
                # Save the final asset
                os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
                output_img.save(output_image_path, "PNG")
                
            return f"[SUCCESS] Subject isolated and color-graded. Saved to {output_image_path}"
        except Exception as e:
            return f"[ERROR] Background removal failed: {e}"

    def extract_frame(self, video_path: str, timestamp_sec: float = 1.0) -> str:
        """
        Extracts a single frame from a video at a given timestamp.
        """
        if not os.path.exists(video_path):
            return None
            
        import cv2
        print(f"[PROCESS] Extracting frame from {video_path} at {timestamp_sec}s")
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_id = int(fps * timestamp_sec)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        
        if ret:
            os.makedirs("static/uploads", exist_ok=True)
            import time
            output_path = f"static/uploads/frame_{int(time.time())}.png"
            cv2.imwrite(output_path, frame)
            cap.release()
            return output_path
        
        cap.release()
        return None

    def apply_text_overlay(self, image_path: str, text: str, position: str = "bottom") -> str:
        """
        Applies a professional, high-contrast text overlay to an image.
        """
        if not os.path.exists(image_path):
            return None
            
        print(f"[PROCESS] Applying branding: '{text}' to {image_path}")
        
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        import time
        
        try:
            img = Image.open(image_path).convert("RGBA")
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            # Use a heavy font
            try:
                # Try common Windows fonts first
                font_paths = [
                    "C:/Windows/Fonts/ariblk.ttf", # Arial Black
                    "C:/Windows/Fonts/impact.ttf",  # Impact
                    "C:/Windows/Fonts/arialbd.ttf", # Arial Bold
                    "arial.ttf" # Fallback
                ]
                font = None
                for path in font_paths:
                    if os.path.exists(path):
                        font = ImageFont.truetype(path, int(height * 0.12)) # 12% of height
                        break
                if not font:
                    font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()
            
            # Calculate text size using textbbox (modern Pillow)
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            text_width = right - left
            text_height = bottom - top
            
            # Position
            x = (width - text_width) // 2
            if position == "bottom":
                y = height - text_height - int(height * 0.1)
            elif position == "top":
                y = int(height * 0.1)
            else:
                y = (height - text_height) // 2
                
            # Draw semi-transparent background box for readability
            padding = 20
            box_coords = [x - padding, y - padding, x + text_width + padding, y + text_height + padding]
            draw.rectangle(box_coords, fill=(0, 0, 0, 160)) # Black 60% opacity
            
            # Draw text
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
            
            # Save branded image
            os.makedirs("static/output", exist_ok=True)
            output_path = f"static/output/branded_{int(time.time())}.png"
            img.convert("RGB").save(output_path, "JPEG", quality=95)
            
            return output_path
        except Exception as e:
            print(f"[ERROR] Branding failed: {e}")
            return None

# Singleton for easy access
canvas_engine = CanvasEngine()
