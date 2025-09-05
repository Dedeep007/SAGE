"""
Configuration settings for the SAGE Desktop AI Assistant.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Load environment variables from .env file
env_path = BASE_DIR / ".env"
load_dotenv(env_path)

# API Keys (set these as environment variables or modify here)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")

# Optional: KerasOCR cache directory
KERAS_OCR_CACHE_DIR = os.getenv("KERAS_OCR_CACHE_DIR", None)

# UI Configuration
UI_CONFIG = {
    "window_width": 350,
    "window_height": 120,
    "expanded_height": 500,
    "border_radius": 15,
    "background_color": "rgba(30, 30, 30, 0.9)",
    "text_color": "#FFFFFF",
    "accent_color": "#007ACC",
    "animation_duration": 200,
    "always_on_top": True,
    "start_position": (100, 100),
}

# Voice Configuration
VOICE_CONFIG = {
    "sample_rate": 16000,
    "channels": 1,
    "chunk_size": 1024,
    "format": "wav",
    "tts_language": "en",
    "tts_slow": False,
    "speech_timeout": 5.0,
    "phrase_timeout": 1.0,
    "ai_speak_responses": True,  # Whether AI should speak chat responses
    "ai_speak_suggestions": True,  # Whether AI should speak screen suggestions
}

# AI Configuration
AI_CONFIG = {
    "model": "openai/gpt-oss-20b",  # Updated to currently supported model
    "temperature": 0.7,
    "max_tokens": 500,
    "streaming": True,
    "context_window": 4096,
    "screen_capture_interval": 5.0,  # seconds
    "max_context_history": 10,
}

# Screen Reader Configuration
SCREEN_CONFIG = {
    "ocr_confidence_threshold": 0.5,  # KerasOCR confidence threshold (0.0-1.0)
    "capture_region": None,  # None for full screen, or (x, y, width, height)
    "preprocessing": True,
    "ocr_backend": "keras",  # "keras" or "tesseract" (fallback)
    "model_cache_dir": KERAS_OCR_CACHE_DIR,
}

# Hotkeys
HOTKEYS = {
    "toggle_expand": "ctrl+space",
    "voice_toggle": "ctrl+shift+v",
    "minimize": "escape",
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": BASE_DIR / "logs" / "sage.log",
    "max_bytes": 10 * 1024 * 1024,  # 10MB
    "backup_count": 3,
}

# Database Configuration
DATABASE_CONFIG = {
    "path": BASE_DIR / "data" / "sage.db",
    "max_history": 1000,
    "cleanup_interval": 24 * 60 * 60,  # 24 hours in seconds
}

# System Messages
SYSTEM_MESSAGES = {
    "assistant_persona": """You are SAGE, a helpful desktop AI assistant. You have access to the user's screen context and can see what they're currently looking at. 

Key behaviors:
- Be concise but helpful
- Use screen context to provide relevant assistance
- Offer actionable suggestions based on what's visible
- Ask clarifying questions when needed
- Be proactive in offering help

When you see screen content, analyze it and offer relevant assistance without being asked.""",
    
    "screen_context_prompt": """Current screen context:
{screen_content}

Based on what you can see on the user's screen, provide helpful and relevant assistance.""",
}
