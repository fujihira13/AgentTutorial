"""
Debug script to inspect the actual MIME type and format of Gemini TTS output.
"""
import os
import base64
import requests
import struct
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-tts:generateContent?key={GOOGLE_API_KEY}"

test_text = "こんにちは"

payload = {
    "contents": [{
        "parts": [{
            "text": f"日本語で読んでください: {test_text}"
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

print("Sending request...")
response = requests.post(url, json=payload)

if response.status_code == 200:
    data = response.json()
    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        for i, part in enumerate(parts):
            if "inlineData" in part:
                mime_type = part["inlineData"].get("mimeType", "unknown")
                audio_b64 = part["inlineData"]["data"]
                raw_audio = base64.b64decode(audio_b64)
                
                print(f"MIME Type: {mime_type}")
                print(f"Raw audio size: {len(raw_audio)} bytes")
                print(f"First 20 bytes (hex): {raw_audio[:20].hex()}")
                
                # Check if it's already WAV (starts with RIFF)
                if raw_audio[:4] == b'RIFF':
                    print("Audio is already in WAV format!")
                    with open("output/test_direct.wav", "wb") as f:
                        f.write(raw_audio)
                else:
                    print("Audio is RAW PCM - needs WAV header!")
                    
                    # Parse sample rate from MIME type if available
                    # e.g., "audio/L16;rate=24000"
                    sample_rate = 24000  # default
                    if "rate=" in mime_type:
                        try:
                            sample_rate = int(mime_type.split("rate=")[1].split(";")[0])
                        except:
                            pass
                    
                    print(f"Detected sample rate: {sample_rate}")
                    
                    # Create WAV header
                    channels = 1
                    bits_per_sample = 16
                    byte_rate = sample_rate * channels * bits_per_sample // 8
                    block_align = channels * bits_per_sample // 8
                    data_size = len(raw_audio)
                    
                    wav_header = struct.pack(
                        '<4sI4s4sIHHIIHH4sI',
                        b'RIFF',
                        36 + data_size,
                        b'WAVE',
                        b'fmt ',
                        16,  # fmt chunk size
                        1,   # audio format (PCM)
                        channels,
                        sample_rate,
                        byte_rate,
                        block_align,
                        bits_per_sample,
                        b'data',
                        data_size
                    )
                    
                    with open("output/test_with_header.wav", "wb") as f:
                        f.write(wav_header + raw_audio)
                    
                    print("Saved with WAV header to output/test_with_header.wav")
else:
    print(f"Error: {response.status_code} - {response.text}")
