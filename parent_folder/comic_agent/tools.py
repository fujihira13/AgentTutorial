import os
import io
import json
import logging
import re
import time
import base64
import requests
from pathlib import Path
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader

# Mock dependencies (replace with real APIs later)
from PIL import Image, ImageDraw
import google.generativeai as genai

# Local Schema
from .schemas import ComicStory, Panel

logger = logging.getLogger(__name__)

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}

def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid int for %s=%s; using default %s", name, value, default)
        return default

def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning("Invalid float for %s=%s; using default %s", name, value, default)
        return default

def _normalize_model_name(value: Optional[str], default: str) -> str:
    normalized = (value or "").strip() or default
    if not normalized.startswith("models/"):
        normalized = f"models/{normalized}"
    return normalized

def _resolve_output_dir(raw_value: Optional[str]) -> Path:
    if not raw_value:
        return PROJECT_ROOT / "output"
    path = Path(raw_value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path

OUTPUT_DIR = _resolve_output_dir(os.getenv("COMIC_OUTPUT_DIR"))
USE_REAL_STORY_GEN = _env_bool("USE_REAL_STORY_GEN", True)
USE_REAL_IMAGE_GEN = _env_bool("USE_REAL_IMAGE_GEN", False)
USE_REAL_TTS = _env_bool("USE_REAL_TTS", False)

STORY_MODEL = _normalize_model_name(os.getenv("COMIC_STORY_MODEL"), "models/gemini-3-pro-preview")
IMAGE_MODEL = _normalize_model_name(os.getenv("COMIC_IMAGE_MODEL"), "models/nano-banana-pro-preview")
TTS_MODEL = _normalize_model_name(os.getenv("COMIC_TTS_MODEL"), "models/gemini-2.5-pro-preview-tts")

HTTP_TIMEOUT_SECONDS = _env_float("COMIC_HTTP_TIMEOUT_SECONDS", 60.0)
API_MAX_RETRIES = _env_int("COMIC_API_MAX_RETRIES", 2)
API_RETRY_BACKOFF_SECONDS = _env_float("COMIC_API_RETRY_BACKOFF_SECONDS", 1.5)
STORY_VALIDATION_MAX_RETRIES = _env_int("COMIC_STORY_VALIDATION_MAX_RETRIES", 2)

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Configure TTS (Gemini Native)
# No extra keys needed now


def _ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LATIN_LETTER_RE = re.compile(r"[A-Za-z]")
NEGATIVE_CONSTRAINTS = "single panel, no grid, no collage, no multiple panels, no storyboard"

def _note_once(story: ComicStory, note: str) -> None:
    if note and note not in story.generation_notes:
        story.generation_notes.append(note)

def _genai_request_options() -> dict:
    if HTTP_TIMEOUT_SECONDS <= 0:
        return {}
    return {"timeout": HTTP_TIMEOUT_SECONDS}

def _with_retries(fn, *, operation: str):
    max_retries = max(API_MAX_RETRIES, 0)
    backoff = max(API_RETRY_BACKOFF_SECONDS, 0.0)
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt >= max_retries:
                break
            delay = backoff * (2 ** attempt)
            logger.warning(
                "Retrying %s (attempt %d/%d) after error: %s",
                operation,
                attempt + 1,
                max_retries + 1,
                exc,
            )
            if delay:
                time.sleep(delay)
    raise last_exc

def _split_characters(characters: str) -> List[str]:
    if not characters:
        return []
    parts = re.split(r"[,\u3001，]", characters)
    return [part.strip() for part in parts if part.strip()]

def _clean_response_text(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    return cleaned

def _extract_json_block(text: str) -> str:
    candidate = text.strip()
    if candidate.startswith("{") and candidate.endswith("}"):
        return candidate
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end != -1 and end > start:
        return candidate[start:end + 1]
    return candidate

def _is_japanese_text(text: str) -> bool:
    if not text:
        return True
    return LATIN_LETTER_RE.search(text) is None

def _validate_story_data(data: dict) -> List[str]:
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["Response is not a JSON object."]

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title is missing or empty.")
    elif not _is_japanese_text(title):
        errors.append("title contains non-Japanese text.")

    panels = data.get("panels")
    if not isinstance(panels, list):
        errors.append("panels is missing or not a list.")
        return errors

    if len(panels) != 4:
        errors.append(f"panels length is {len(panels)}; expected 4.")

    for idx, panel in enumerate(panels, 1):
        if not isinstance(panel, dict):
            errors.append(f"panel {idx} is not an object.")
            continue

        scenario = panel.get("scenario")
        visual = panel.get("visual")
        dialogue = panel.get("dialogue", "")

        if not isinstance(scenario, str) or not scenario.strip():
            errors.append(f"panel {idx} scenario is missing or empty.")
        elif not _is_japanese_text(scenario):
            errors.append(f"panel {idx} scenario contains non-Japanese text.")

        if not isinstance(visual, str) or not visual.strip():
            errors.append(f"panel {idx} visual is missing or empty.")
        elif not _is_japanese_text(visual):
            errors.append(f"panel {idx} visual contains non-Japanese text.")

        if dialogue is not None:
            if not isinstance(dialogue, str):
                errors.append(f"panel {idx} dialogue is not a string.")
            elif dialogue.strip() and not _is_japanese_text(dialogue):
                errors.append(f"panel {idx} dialogue contains non-Japanese text.")

    return errors

def _build_story_from_data(
    data: dict,
    theme_label: str,
    characters_label: str,
    tone_label: str,
    char_list: List[str],
) -> ComicStory:
    panels = []
    for idx, panel_data in enumerate(data["panels"], 1):
        visual = panel_data["visual"]
        panels.append(Panel(
            panel_number=idx,
            scenario=panel_data["scenario"],
            dialogue=panel_data.get("dialogue", ""),
            visual_description=visual,
            image_prompt=(
                "日本の4コマ漫画風、"
                f"{tone_label}、{visual}、{theme_label}、"
                f"キャラクター：{characters_label}、"
                f"シンプルで可愛いイラスト、{NEGATIVE_CONSTRAINTS}"
            ),
            image_path=None,
            audio_path=None
        ))

    return ComicStory(
        title=data.get("title", f"{theme_label}の物語"),
        characters=char_list,
        theme=theme_label,
        panels=panels,
        output_dir=str(OUTPUT_DIR),
    )

def _build_template_story(
    theme_label: str,
    characters_label: str,
    tone_label: str,
    char_list: List[str],
) -> ComicStory:
    main_char = char_list[0] if char_list else "主人公"
    title = f"{theme_label}～{main_char}の物語～"

    story_patterns = [
        {"scenario": f"【起】平和な日常。{main_char}がのんびり。", "dialogue": "今日もいい天気。", "visual": f"{main_char}が笑顔"},
        {"scenario": f"【承】{theme_label}が発生！", "dialogue": "えっ何これ？", "visual": f"{main_char}が驚く"},
        {"scenario": "【転】大変なことに。", "dialogue": "うわああ！", "visual": f"{main_char}が慌てる"},
        {"scenario": "【結】なんとか解決？", "dialogue": "まあいいか。", "visual": f"{main_char}が苦笑い"}
    ]

    panels = []
    for i, content in enumerate(story_patterns, 1):
        panels.append(Panel(
            panel_number=i,
            scenario=content["scenario"],
            dialogue=content["dialogue"],
            visual_description=content["visual"],
            image_prompt=(
                "日本の4コマ漫画風、"
                f"{tone_label}、{content['visual']}、{theme_label}、"
                f"キャラクター：{characters_label}、"
                f"シンプルで可愛いイラスト、{NEGATIVE_CONSTRAINTS}"
            ),
            image_path=None,
            audio_path=None
        ))

    return ComicStory(
        title=title,
        characters=char_list,
        theme=theme_label,
        panels=panels,
        output_dir=str(OUTPUT_DIR),
    )

# --- 1. Story Development ---

def develop_story(theme: str, characters: str, tone: str, twist: str) -> ComicStory:
    """
    4コマ漫画のストーリー構造をGeminiを使用して生成します。
    日本語の「起承転結」構造で、単一パネル画像に適した内容にします。
    """
    _ensure_output_dir()

    theme = theme or ""
    characters = characters or ""
    tone = tone or ""
    twist = twist or ""

    theme_label = theme.strip() or "テーマ未指定"
    characters_label = characters.strip() or "未指定"
    tone_label = tone.strip() or "指定なし"
    twist_label = twist.strip() or "特になし"

    char_list = _split_characters(characters)

    if not USE_REAL_STORY_GEN:
        story = _build_template_story(theme_label, characters_label, tone_label, char_list)
        _note_once(story, "ストーリー生成はモックを使用しました (USE_REAL_STORY_GEN=false)。")
        _save_json(story)
        return story

    if not GOOGLE_API_KEY:
        story = _build_template_story(theme_label, characters_label, tone_label, char_list)
        _note_once(story, "GOOGLE_API_KEYが未設定のためストーリー生成をモックにフォールバックしました。")
        _save_json(story)
        return story

    # Prompt for Gemini to generate the story structure
    prompt = f"""
あなたはプロの4コマ漫画家です。以下のテーマに基づいて、日本語で面白い4コマ漫画のストーリー（起承転結）を考えてください。

テーマ: {theme_label}
登場人物: {characters_label}
トーン: {tone_label}
追加要素: {twist_label}

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

    max_attempts = 1 + max(STORY_VALIDATION_MAX_RETRIES, 0)
    last_errors: List[str] = []
    for attempt in range(max_attempts):
        try:
            model = genai.GenerativeModel(STORY_MODEL)
            response = _with_retries(
                lambda: model.generate_content(prompt, request_options=_genai_request_options()),
                operation="Gemini story generation",
            )
            text = _clean_response_text(response.text or "")
            data = json.loads(_extract_json_block(text))
            errors = _validate_story_data(data)
            if not errors:
                story = _build_story_from_data(
                    data,
                    theme_label,
                    characters_label,
                    tone_label,
                    char_list,
                )
                _save_json(story)
                return story
            last_errors = errors
            logger.warning(
                "Story validation failed (attempt %d/%d): %s",
                attempt + 1,
                max_attempts,
                "; ".join(errors),
            )
        except Exception as e:
            last_errors = [str(e)]
            logger.warning(
                "Story generation failed (attempt %d/%d): %s",
                attempt + 1,
                max_attempts,
                e,
            )

    story = _build_template_story(theme_label, characters_label, tone_label, char_list)
    _note_once(story, "ストーリー生成に失敗したためテンプレートを使用しました。")
    if last_errors:
        _note_once(story, f"理由: {last_errors[0]}")
    _save_json(story)
    return story

# --- 2. Image Generation ---

def generate_panels(story: ComicStory) -> ComicStory:
    """
    Generates images for each panel in the story.
    """
    _ensure_output_dir()

    use_real = USE_REAL_IMAGE_GEN and bool(GOOGLE_API_KEY)
    had_failures = False

    if not USE_REAL_IMAGE_GEN:
        _note_once(story, "画像生成はモックを使用しました (USE_REAL_IMAGE_GEN=false)。")
    elif not GOOGLE_API_KEY:
        _note_once(story, "GOOGLE_API_KEYが未設定のため画像生成をモックにフォールバックしました。")

    for panel in story.panels:
        filename = f"panel_{panel.panel_number}.png"
        filepath = OUTPUT_DIR / filename

        if use_real:
            try:
                _create_real_image(panel, filepath)
            except Exception as e:
                had_failures = True
                logger.error(f"Failed to generate image for panel {panel.panel_number}: {e}")
                logger.warning("Falling back to mock image.")
                _create_mock_image(panel, filepath)
        else:
            _create_mock_image(panel, filepath)

        panel.image_path = filename

    if had_failures:
        _note_once(story, "一部の画像生成に失敗したためモックにフォールバックしました。")

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

    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in environment variables.")

    try:
        model = genai.GenerativeModel(IMAGE_MODEL)
        response = _with_retries(
            lambda: model.generate_content(panel.image_prompt, request_options=_genai_request_options()),
            operation="Gemini image generation",
        )

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
        logger.error(f"Error calling image generation model: {e}")
        raise e

# --- 3. Narration (TTS) ---

def narrate_comic(story: ComicStory) -> ComicStory:
    """
    Generates audio narration for each panel.
    """
    _ensure_output_dir()

    use_real = USE_REAL_TTS and bool(GOOGLE_API_KEY)
    had_failures = False
    skipped_empty_dialogue = False

    if not USE_REAL_TTS:
        _note_once(story, "音声生成はモックを使用しました (USE_REAL_TTS=false)。")
    elif not GOOGLE_API_KEY:
        _note_once(story, "GOOGLE_API_KEYが未設定のため音声生成をモックにフォールバックしました。")

    for panel in story.panels:
        if not panel.dialogue or not panel.dialogue.strip():
            skipped_empty_dialogue = True
            panel.audio_path = None
            continue

        filename = f"panel_{panel.panel_number}.wav"
        filepath = OUTPUT_DIR / filename

        # テキストの整形 (句読点の強調や不要な空白の削除)
        clean_text = panel.dialogue.strip().replace("\n", "。")
        if not clean_text.endswith(("。", "！", "？", ".", "!", "?")):
            clean_text += "。"

        if use_real:
            try:
                _create_real_audio(clean_text, filepath)
            except Exception as e:
                had_failures = True
                logger.error(f"Failed to generate TTS for panel {panel.panel_number}: {e}")
                logger.warning("Falling back to mock audio.")
                _create_mock_audio(filepath)
        else:
            _create_mock_audio(filepath)

        panel.audio_path = filename

    if skipped_empty_dialogue:
        _note_once(story, "空のセリフのコマは音声を生成していません。")
    if had_failures:
        _note_once(story, "一部の音声生成に失敗したためモックにフォールバックしました。")

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

    url = f"https://generativelanguage.googleapis.com/v1beta/{TTS_MODEL}:generateContent?key={GOOGLE_API_KEY}"
    
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
    
    def _post_request():
        timeout = HTTP_TIMEOUT_SECONDS if HTTP_TIMEOUT_SECONDS > 0 else None
        response = requests.post(url, json=payload, timeout=timeout)
        if response.status_code in {429, 500, 502, 503, 504}:
            raise RuntimeError(f"Retryable TTS API error: {response.status_code}")
        return response

    response = _with_retries(_post_request, operation="Gemini TTS request")
    
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
