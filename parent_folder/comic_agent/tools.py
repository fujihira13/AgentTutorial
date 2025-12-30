import os
import io
import json
import logging
import random
import base64
import requests
from pathlib import Path
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader

# Mock dependencies (replace with real APIs later)
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

# Local Schema
from .schemas import ComicStory, Panel

logger = logging.getLogger(__name__)

# --- Configuration ---
OUTPUT_DIR = Path("output")
USE_REAL_IMAGE_GEN = os.getenv("USE_REAL_IMAGE_GEN", "false").lower() == "true"
USE_REAL_TTS = os.getenv("USE_REAL_TTS", "false").lower() == "true"

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Configure TTS (Gemini Native)
# No extra keys needed now


def _ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- 1. Story Development ---

def develop_story(theme: str, characters: str, tone: str, twist: str) -> ComicStory:
    """
    4コマ漫画のストーリー構造をGeminiを使用して生成します。
    日本語の「起承転結」構造で、単一パネル画像に適した内容にします。
    """
    _ensure_output_dir()
    
    char_list = [c.strip() for c in characters.split(",")]
    
    # Prompt for Gemini to generate the story structure
    prompt = f"""
あなたはプロの4コマ漫画家です。以下のテーマに基づいて、日本語で面白い4コマ漫画のストーリー（起承転結）を考えてください。

テーマ: {theme}
登場人物: {characters}
トーン: {tone}
追加要素: {twist if twist else "特になし"}

以下の条件を厳守してください：
1. 必ず正確に4つのコマ（起・承・転・結）で構成すること。
2. すべて日本語で出力すること。英語は禁止です。
3. 各コマは単一の場面（single panel）として描きやすい描写にすること。
4. オチ（結）を面白くすること。

出力は以下のJSONフォーマットのみで行ってください（他のテキストは含めないでください）：
{{
  "title": "作品のタイトル",
  "panels": [
    {{
      "panel_number": 1,
      "scenario": "場面の説明（起）",
      "dialogue": "キャラクターのセリフ",
      "visual": "AI画像生成用の具体的な視覚描写（日本語）"
    }},
    ...（計4パネル）
  ]
}}
"""

    try:
        model = genai.GenerativeModel("models/gemini-3-pro-preview")
        response = model.generate_content(prompt)
        
        # Clean response if it contains markdown code blocks
        text = response.text.strip()
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0].strip()
        elif text.startswith("```"):
            text = text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(text)
        
        # 複数パネル化を防ぐための強制プロンプト
        negative_constraints = "single panel, no grid, no collage, no multiple panels, no storyboard"
        
        panels = []
        for p in data["panels"]:
            panels.append(Panel(
                panel_number=p["panel_number"],
                scenario=p["scenario"],
                dialogue=p.get("dialogue", ""),
                visual_description=p["visual"],
                image_prompt=f"日本の4コマ漫画風、{tone}、{p['visual']}、{theme}、キャラクター：{characters}、シンプルで可愛いイラスト、{negative_constraints}",
                image_path=None,
                audio_path=None
            ))

        story = ComicStory(
            title=data.get("title", f"{theme}の物語"),
            characters=char_list,
            theme=theme,
            panels=panels,
            output_dir=str(OUTPUT_DIR)
        )
    except Exception as e:
        logger.error(f"Error in LLM develop_story: {e}")
        # Error recovery: fallback to template if LLM fails
        logger.warning("Falling back to template story due to LLM error.")
        main_char = char_list[0] if char_list else "主人公"
        title = f"{theme}～{main_char}の物語～"
        
        story_patterns = [
            {"scenario": f"【起】平和な日常。{main_char}がのんびり。", "dialogue": "今日もいい天気。", "visual": f"{main_char}が笑顔"},
            {"scenario": f"【承】{theme}が発生！", "dialogue": "えっ何これ？", "visual": f"{main_char}が驚く"},
            {"scenario": f"【転】大変なことに。", "dialogue": "うわああ！", "visual": f"{main_char}が慌てる"},
            {"scenario": f"【結】なんとか解決？", "dialogue": "まあいいか。", "visual": f"{main_char}が苦笑い"}
        ]
        
        negative_constraints = "single panel, no grid, no collage, no multiple panels, no storyboard"
        panels = []
        for i, content in enumerate(story_patterns, 1):
            panels.append(Panel(
                panel_number=i,
                scenario=content['scenario'],
                dialogue=content['dialogue'],
                visual_description=content['visual'],
                image_prompt=f"日本の4コマ漫画風、{tone}、{content['visual']}、{theme}、キャラクター：{characters}、シンプルで可愛いイラスト、{negative_constraints}",
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
    
    # Use Nano Banana Pro model
    try:
        model = genai.GenerativeModel("models/nano-banana-pro-preview")
        
        response = model.generate_content(panel.image_prompt)
        
        image_data = None
        for part in response.parts:
            if part.inline_data:
                image_data = part.inline_data.data
                break
        
        if image_data:
            image = Image.open(io.BytesIO(image_data))
            image.save(filepath)
        else:
            raise Exception("No image data returned from API")
            
    except Exception as e:
        logger.error(f"Error calling Nano Banana Pro: {e}")
        raise e

# --- 3. Narration (TTS) ---

def narrate_comic(story: ComicStory) -> ComicStory:
    """
    Generates audio narration for each panel.
    """
    _ensure_output_dir()
    
    for panel in story.panels:
        filename = f"panel_{panel.panel_number}.wav"
        filepath = OUTPUT_DIR / filename
        
        # テキストの整形 (句読点の強調や不要な空白の削除)
        clean_text = panel.dialogue.strip().replace("\n", "。")
        if not clean_text.endswith(("。", "！", "？", ".", "!", "?")):
            clean_text += "。"
            
        if USE_REAL_TTS:
            try:
                _create_real_audio(clean_text, filepath)
            except Exception as e:
                logger.error(f"Failed to generate TTS for panel {panel.panel_number}: {e}")
                logger.warning("Falling back to mock audio.")
                _create_mock_audio(filepath)
        else:
            _create_mock_audio(filepath)
            
        panel.audio_path = filename
    
    _save_json(story)
    return story

def _create_real_audio(text: str, filepath: Path):
    """
    Generates audio using Gemini 2.5 Pro Preview TTS (REST).
    The API returns raw PCM audio (audio/L16), so we add WAV headers.
    """
    import struct
    
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in environment variables.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-tts:generateContent?key={GOOGLE_API_KEY}"
    
    # Prompt engineering for Japanese + Pauses
    prompt_text = (
        f"日本語で以下のテキストを読んでください。適切な箇所で自然な間を入れてください。\n"
        f"読み上げるテキスト:\n{text}"
    )

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt_text
            }]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": "Aoede"
                    }
                }
            }
        }
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        try:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                
                # 複数のパーツがある場合に備え、全オーディオデータを収集
                raw_audio_list = []
                sample_rate = 24000  # デフォルト
                
                for part in parts:
                    if "inlineData" in part:
                        mime_type = part["inlineData"].get("mimeType", "")
                        data_chunk = base64.b64decode(part["inlineData"]["data"])
                        
                        # サンプリングレートをMIMEタイプから取得
                        if "rate=" in mime_type:
                            try:
                                sample_rate = int(mime_type.split("rate=")[1].split(";")[0])
                            except:
                                pass
                        
                        # すでにWAVヘッダーが含まれている場合はヘッダーを除去し、生PCMデータとして蓄積
                        # (最初以外のチャンクにヘッダーが含まれる可能性を考慮)
                        if data_chunk[:4] == b'RIFF':
                            # WAVヘッダーは通常44バイト
                            raw_audio_list.append(data_chunk[44:])
                        else:
                            raw_audio_list.append(data_chunk)
                
                if not raw_audio_list:
                    raise Exception("No inlineData found in any parts of the response")
                
                # 全ての生PCMデータを結合
                all_raw_audio = b"".join(raw_audio_list)
                data_size = len(all_raw_audio)
                
                # 再生時間を計算 (16bit mono)
                channels = 1
                bits_per_sample = 16
                duration_sec = data_size / (sample_rate * channels * (bits_per_sample // 8))
                
                logger.info(f"TTS Audio Duration: {duration_sec:.2f} seconds (for text: {text[:30]}...)")
                if duration_sec < 3.0:
                    logger.warning(f"Audio duration check: Too short! ({duration_sec:.2f}s). The text might be truncated.")
                
                # WAVヘッダーを付けて保存
                byte_rate = sample_rate * channels * bits_per_sample // 8
                block_align = channels * bits_per_sample // 8
                
                wav_header = struct.pack(
                    '<4sI4s4sIHHIIHH4sI',
                    b'RIFF',
                    36 + data_size,
                    b'WAVE',
                    b'fmt ',
                    16,
                    1,  # PCM format
                    channels,
                    sample_rate,
                    byte_rate,
                    block_align,
                    bits_per_sample,
                    b'data',
                    data_size
                )
                
                with open(filepath, "wb") as f:
                    f.write(wav_header + all_raw_audio)
                
                logger.info(f"Generated Gemini TTS audio for: {filepath}")
                return
            
            logger.error(f"No candidates found in Gemini response: {data}")
            raise Exception("No candidates in response")

        except Exception as e:
            logger.error(f"Error parsing Gemini TTS response: {e}")
            raise e
    else:
        logger.error(f"Gemini TTS API Error: {response.status_code} - {response.text}")
        raise Exception(f"TTS API failed with status {response.status_code}")

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
