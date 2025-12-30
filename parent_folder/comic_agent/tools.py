import os
import io
import json
import logging
import random
from pathlib import Path
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader

# Mock dependencies (replace with real APIs later)
# Mock dependencies (replace with real APIs later)
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

# Local Schema
from .schemas import ComicStory, Panel

logger = logging.getLogger(__name__)

# --- Configuration ---
OUTPUT_DIR = Path("output")
USE_REAL_IMAGE_GEN = os.getenv("USE_REAL_IMAGE_GEN", "false").lower() == "true"
USE_REAL_IMAGE_GEN = os.getenv("USE_REAL_IMAGE_GEN", "false").lower() == "true"
USE_REAL_TTS = os.getenv("USE_REAL_TTS", "false").lower() == "true"

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def _ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- 1. Story Development ---

def develop_story(theme: str, characters: str, tone: str, twist: str) -> ComicStory:
    """
    Generates a 4-panel comic story structure based on inputs.
    In a real implementation, this would call an LLM. 
    Here we implement a robust mock/template generator for MVP.
    """
    _ensure_output_dir()
    
    char_list = [c.strip() for c in characters.split(",")]
    title = f"{theme} with {char_list[0]}" if char_list else f"{theme} Story"
    
    # Mock Story Generation logic
    panels = []
    stages = ["Introduction", "Build-up", "Climax", "Punchline"]
    
    for i, stage in enumerate(stages, 1):
        panels.append(Panel(
            panel_number=i,
            scenario=f"{stage} of the story about {theme}. Tone: {tone}.",
            dialogue=f"Character says something about {theme} ({stage}).",
            visual_description=f"A scene showing {', '.join(char_list)}. {stage} phase.",
            image_prompt=f"Comic panel, {tone}, {stage}, {theme}, characters: {characters}, detailed, 4k",
            image_path=None,
            audio_path=None
        ))

    story = ComicStory(
        title=title,
        characters=char_list,
        theme=theme,
        panels=panels,
        output_dir=str(OUTPUT_DIR)
    )
    
    # In a real agent, we might save this state or pass it object-to-object.
    # We'll also dump it to JSON for debugging/persistence.
    _save_json(story)
    return story

# --- 2. Image Generation ---

def generate_panels(story: ComicStory) -> ComicStory:
    """
    Generates images for each panel in the story.
    """
    _ensure_output_dir()
    
    for panel in story.panels:
        filename = f"panel_{panel.panel_number}.png"
        filepath = OUTPUT_DIR / filename
        
        if USE_REAL_IMAGE_GEN:
        if USE_REAL_IMAGE_GEN:
            try:
                _create_real_image(panel, filepath)
            except Exception as e:
                logger.error(f"Failed to generate image for panel {panel.panel_number}: {e}")
                logger.warning("Falling back to mock image.")
                _create_mock_image(panel, filepath)
        else:
            _create_mock_image(panel, filepath)
            
        panel.image_path = filename
    
    _save_json(story)
    return story

def _create_mock_image(panel: Panel, filepath: Path):
    """Creates a simple placeholder image using Pillow."""
    img = Image.new('RGB', (512, 512), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    
    # Simple logic to center text (rough approximation)
    text = f"Panel {panel.panel_number}\n{panel.scenario[:50]}..."
    d.text((50, 200), text, fill=(255, 255, 0))
    
    img.save(filepath)

def _create_real_image(panel: Panel, filepath: Path):
    """
    Generates an image using Nano Banana Pro (Gemini 3 Pro Image).
    """
    logger.info(f"Generating image for panel {panel.panel_number} with prompt: {panel.image_prompt}")
    
    # Use the appropriate model name for "Nano Banana Pro" capabilities
    # Assuming 'imagen-3.0-generate-001' or similar latest model
    model = genai.ImageGenerationModel("imagen-3.0-generate-001")
    
    response = model.generate_images(
        prompt=panel.image_prompt,
        number_of_images=1,
    )
    
    if response.images:
        response.images[0].save(filepath)
    else:
        raise Exception("No images returned from API")

# --- 3. Narration (TTS) ---

def narrate_comic(story: ComicStory) -> ComicStory:
    """
    Generates audio narration for each panel.
    """
    _ensure_output_dir()
    
    for panel in story.panels:
        filename = f"panel_{panel.panel_number}.wav"
        filepath = OUTPUT_DIR / filename
        
        if USE_REAL_TTS:
            # TODO: Implement real API call (e.g. Google Cloud TTS)
            logger.warning("Real TTS not implemented yet, using mock.")
            _create_mock_audio(filepath)
        else:
            _create_mock_audio(filepath)
            
        panel.audio_path = filename
    
    _save_json(story)
    return story

def _create_mock_audio(filepath: Path):
    """Creates a dummy valid WAV file (1 second of silence)."""
    # RIFF header generation for a valid minimal WAV file
    # This is binary data directly written to file
    with open(filepath, "wb") as f:
        # Header bytes for 1 sec silent wav (approx) - actually just empty or minimal
        # For simplicity, we write a very small valid wav header + 0 data
        header = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        f.write(header)

# --- 4. Publishing (HTML) ---

def publish_comic(story: ComicStory) -> str:
    """
    Generates the index.html viewer.
    Returns the path to the generated HTML file.
    """
    _ensure_output_dir()
    
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("viewer.html")
    
    html_content = template.render(story=story)
    
    output_path = OUTPUT_DIR / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return str(output_path)

def _save_json(story: ComicStory):
    """Helper to save the current state of the story to JSON."""
    json_path = OUTPUT_DIR / "comic.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(story.model_dump_json(indent=2))
