"""
Voice processing module for speech recognition and text-to-speech.
Handles microphone input, voice recognition, and AI voice output.
"""
import asyncio
import logging
import threading
import time
import queue
import tempfile
import os
from typing import Optional, Callable, Any
from dataclasses import dataclass

import speech_recognition as sr
import pyttsx3
import pygame
from gtts import gTTS
import io

from config.settings import VOICE_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class VoiceResult:
    """Container for voice recognition results."""
    text: str
    confidence: float
    timestamp: float
    success: bool
    error: Optional[str] = None


class VoiceProcessor:
    """
    Handles voice input (speech recognition) and output (text-to-speech).
    """
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone: Optional[sr.Microphone] = None
        self.tts_engine: Optional[pyttsx3.Engine] = None
        self.is_listening = False
        self.listen_thread: Optional[threading.Thread] = None
        self.voice_callback: Optional[Callable[[VoiceResult], None]] = None
        
        # Audio playback
        pygame.mixer.init()
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize voice recognition and TTS components."""
        try:
            # Initialize microphone
            self.microphone = sr.Microphone(
                sample_rate=VOICE_CONFIG["sample_rate"],
                chunk_size=VOICE_CONFIG["chunk_size"]
            )
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.info("Microphone initialized successfully")
            
            # Initialize TTS engine
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS settings
            self.tts_engine.setProperty('rate', 200)  # Speed
            self.tts_engine.setProperty('volume', 0.8)  # Volume
            
            # Try to set a pleasant voice
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.tts_engine.setProperty('voice', voices[0].id)
            
            logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice components: {e}")
            raise
    
    def set_voice_callback(self, callback: Callable[[VoiceResult], None]):
        """Set callback for voice recognition results."""
        self.voice_callback = callback
    
    def start_listening(self):
        """Start continuous voice recognition."""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        logger.info("Voice listening started")
    
    def stop_listening(self):
        """Stop voice recognition."""
        self.is_listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2.0)
        logger.info("Voice listening stopped")
    
    def _listen_loop(self):
        """Main listening loop running in a separate thread."""
        while self.is_listening and self.microphone:
            try:
                # Listen for audio with timeout
                with self.microphone as source:
                    logger.debug("Listening for speech...")
                    audio = self.recognizer.listen(
                        source,
                        timeout=VOICE_CONFIG["speech_timeout"],
                        phrase_time_limit=VOICE_CONFIG["phrase_timeout"]
                    )
                
                # Process the audio in the background
                threading.Thread(
                    target=self._process_audio,
                    args=(audio,),
                    daemon=True
                ).start()
                
            except sr.WaitTimeoutError:
                # No speech detected within timeout - this is normal
                continue
            except Exception as e:
                logger.error(f"Error in listening loop: {e}")
                time.sleep(1.0)  # Brief pause before retrying
    
    def _process_audio(self, audio):
        """Process captured audio and perform speech recognition."""
        try:
            start_time = time.time()
            
            # Try Google Speech Recognition first
            try:
                text = self.recognizer.recognize_google(audio)
                confidence = 0.8  # Google doesn't provide confidence, assume good
                success = True
                error = None
                logger.debug(f"Google SR recognized: {text}")
                
            except sr.UnknownValueError:
                # Try offline recognition as fallback
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    confidence = 0.6  # Lower confidence for offline
                    success = True
                    error = None
                    logger.debug(f"Sphinx SR recognized: {text}")
                    
                except (sr.UnknownValueError, sr.RequestError):
                    text = ""
                    confidence = 0.0
                    success = False
                    error = "Could not understand audio"
                    
            except sr.RequestError as e:
                # Try offline recognition as fallback
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    confidence = 0.6
                    success = True
                    error = None
                    logger.debug(f"Sphinx SR recognized (fallback): {text}")
                    
                except (sr.UnknownValueError, sr.RequestError):
                    text = ""
                    confidence = 0.0
                    success = False
                    error = f"Recognition service error: {e}"
            
            # Create result object
            result = VoiceResult(
                text=text.strip() if text else "",
                confidence=confidence,
                timestamp=time.time(),
                success=success,
                error=error
            )
            
            # Call callback if available and recognition was successful
            if self.voice_callback and success and text.strip():
                self.voice_callback(result)
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            result = VoiceResult(
                text="",
                confidence=0.0,
                timestamp=time.time(),
                success=False,
                error=str(e)
            )
            
            if self.voice_callback:
                self.voice_callback(result)
    
    def listen_once(self, timeout: float = 5.0) -> VoiceResult:
        """
        Listen for a single voice input with timeout.
        
        Args:
            timeout: Maximum time to wait for speech
            
        Returns:
            VoiceResult object with recognition results
        """
        if not self.microphone:
            return VoiceResult(
                text="",
                confidence=0.0,
                timestamp=time.time(),
                success=False,
                error="Microphone not available"
            )
        
        try:
            with self.microphone as source:
                logger.debug("Listening for single input...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10.0)
            
            # Process audio synchronously
            return self._process_audio_sync(audio)
            
        except sr.WaitTimeoutError:
            return VoiceResult(
                text="",
                confidence=0.0,
                timestamp=time.time(),
                success=False,
                error="Listening timeout"
            )
        except Exception as e:
            logger.error(f"Error in single listen: {e}")
            return VoiceResult(
                text="",
                confidence=0.0,
                timestamp=time.time(),
                success=False,
                error=str(e)
            )
    
    def _process_audio_sync(self, audio) -> VoiceResult:
        """Synchronously process audio and return result."""
        try:
            # Try Google Speech Recognition
            text = self.recognizer.recognize_google(audio)
            return VoiceResult(
                text=text.strip(),
                confidence=0.8,
                timestamp=time.time(),
                success=True
            )
            
        except sr.UnknownValueError:
            return VoiceResult(
                text="",
                confidence=0.0,
                timestamp=time.time(),
                success=False,
                error="Could not understand audio"
            )
        except sr.RequestError as e:
            return VoiceResult(
                text="",
                confidence=0.0,
                timestamp=time.time(),
                success=False,
                error=f"Recognition error: {e}"
            )
    
    async def speak_text(self, text: str, use_gtts: bool = True):
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            use_gtts: Use Google TTS (better quality) vs local TTS (faster)
        """
        if not text.strip():
            return
        
        try:
            if use_gtts:
                await self._speak_with_gtts(text)
            else:
                await self._speak_with_pyttsx3(text)
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            # Fallback to local TTS
            if use_gtts:
                await self._speak_with_pyttsx3(text)
    
    async def _speak_with_gtts(self, text: str):
        """Use Google TTS for speech synthesis."""
        try:
            # Create TTS object
            tts = gTTS(
                text=text,
                lang=VOICE_CONFIG["tts_language"],
                slow=VOICE_CONFIG["tts_slow"]
            )
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                tmp_filename = tmp_file.name
            
            # Play the audio file
            pygame.mixer.music.load(tmp_filename)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            # Clean up temporary file
            try:
                os.unlink(tmp_filename)
            except:
                pass
                
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            raise
    
    async def _speak_with_pyttsx3(self, text: str):
        """Use local TTS engine for speech synthesis."""
        try:
            if self.tts_engine:
                # Run TTS in thread to avoid blocking
                def speak_sync():
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                
                # Run in executor to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, speak_sync)
                
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")
            raise
    
    def is_microphone_available(self) -> bool:
        """Check if microphone is available."""
        return self.microphone is not None
    
    def get_microphone_list(self) -> list:
        """Get list of available microphones."""
        try:
            return sr.Microphone.list_microphone_names()
        except Exception as e:
            logger.error(f"Error getting microphone list: {e}")
            return []
    
    def test_microphone(self) -> bool:
        """Test microphone functionality."""
        try:
            if not self.microphone:
                return False
            
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return False


# Singleton instance
_voice_processor_instance: Optional[VoiceProcessor] = None


def get_voice_processor() -> VoiceProcessor:
    """Get the global voice processor instance."""
    global _voice_processor_instance
    if _voice_processor_instance is None:
        _voice_processor_instance = VoiceProcessor()
    return _voice_processor_instance
