"""
Screen reader module for capturing and processing screen content.
Provides OCR capabilities using KerasOCR and context extraction for the AI assistant.
"""
import asyncio
import logging
import time
from typing import Optional, Tuple, Dict, Any, List
import cv2
import numpy as np
import mss
import keras_ocr
from PIL import Image, ImageEnhance, ImageFilter
import threading
from dataclasses import dataclass
import os

from config.settings import SCREEN_CONFIG, AI_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ScreenContext:
    """Container for screen context data."""
    text_content: str
    timestamp: float
    confidence: float
    region: Optional[Tuple[int, int, int, int]] = None
    image_hash: Optional[str] = None


class ScreenReader:
    """
    Handles screen capture, OCR processing, and context extraction using KerasOCR.
    """
    
    def __init__(self):
        self.is_running = False
        self.capture_interval = AI_CONFIG["screen_capture_interval"]
        self.last_context: Optional[ScreenContext] = None
        self.capture_thread: Optional[threading.Thread] = None
        self.context_callbacks = []
        self._lock = threading.Lock()
        
        # Initialize KerasOCR pipeline
        self.ocr_pipeline = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize KerasOCR pipeline."""
        try:
            logger.info("Initializing KerasOCR pipeline...")
            
            # Set cache directory if specified
            if SCREEN_CONFIG.get("model_cache_dir"):
                os.environ['KERAS_OCR_CACHE_DIR'] = SCREEN_CONFIG["model_cache_dir"]
            
            # Initialize KerasOCR pipeline
            # This will download models on first run (~200MB)
            self.ocr_pipeline = keras_ocr.pipeline.Pipeline()
            
            logger.info("KerasOCR pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize KerasOCR: {e}")
            logger.warning("OCR functionality will be limited")
            self.ocr_pipeline = None
    
    def add_context_callback(self, callback):
        """Add a callback to be called when new screen context is available."""
        self.context_callbacks.append(callback)
    
    def remove_context_callback(self, callback):
        """Remove a context callback."""
        if callback in self.context_callbacks:
            self.context_callbacks.remove(callback)
    
    def start_monitoring(self):
        """Start continuous screen monitoring."""
        if self.is_running:
            return
        
        if not self.ocr_pipeline:
            logger.warning("OCR pipeline not available, screen monitoring disabled")
            return
        
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.capture_thread.start()
        logger.info("Screen monitoring started")
    
    def stop_monitoring(self):
        """Stop screen monitoring."""
        self.is_running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        logger.info("Screen monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop running in a separate thread."""
        while self.is_running:
            try:
                context = self.capture_screen_context()
                if context and self._is_context_changed(context):
                    with self._lock:
                        self.last_context = context
                    
                    # Notify callbacks
                    for callback in self.context_callbacks:
                        try:
                            callback(context)
                        except Exception as e:
                            logger.error(f"Error in context callback: {e}")
                
                time.sleep(self.capture_interval)
                
            except Exception as e:
                logger.error(f"Error in screen monitoring loop: {e}")
                time.sleep(1.0)  # Brief pause before retrying
    
    def capture_screen_context(self) -> Optional[ScreenContext]:
        """
        Capture current screen content and extract text via KerasOCR.
        
        Returns:
            ScreenContext object or None if capture failed
        """
        if not self.ocr_pipeline:
            return None
            
        try:
            # Capture screen
            screenshot = self._capture_screen()
            if screenshot is None:
                return None
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(screenshot)
            
            # Perform OCR
            text_content, confidence = self._extract_text_keras(processed_image)
            
            # Filter based on confidence threshold
            if confidence < SCREEN_CONFIG["ocr_confidence_threshold"]:
                logger.debug(f"OCR confidence too low: {confidence}")
                return None
            
            # Create context object
            context = ScreenContext(
                text_content=text_content,
                timestamp=time.time(),
                confidence=confidence,
                region=SCREEN_CONFIG.get("capture_region"),
                image_hash=self._calculate_image_hash(screenshot)
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to capture screen context: {e}")
            return None
    
    def _capture_screen(self) -> Optional[Image.Image]:
        """Capture screenshot using mss."""
        try:
            # Create new MSS instance for thread safety
            with mss.mss() as sct:
                # Determine capture region
                region = SCREEN_CONFIG.get("capture_region")
                if region:
                    monitor = {
                        "top": region[1],
                        "left": region[0],
                        "width": region[2],
                        "height": region[3]
                    }
                else:
                    monitor = sct.monitors[1]  # Primary monitor
                
                # Capture screenshot
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                return img
            
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: PIL Image to preprocess
            
        Returns:
            Preprocessed numpy array (BGR format for KerasOCR)
        """
        try:
            if not SCREEN_CONFIG.get("preprocessing", True):
                # Convert PIL to numpy array (RGB to BGR for OpenCV/KerasOCR)
                return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV operations
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Resize if image is too large (for performance)
            height, width = img_bgr.shape[:2]
            max_dimension = 1920  # Max width or height
            
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img_bgr = cv2.resize(img_bgr, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Optional: Apply some preprocessing for better OCR
            # Convert to grayscale for noise reduction, then back to BGR
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            
            # Apply slight Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Convert back to BGR (KerasOCR expects 3-channel image)
            img_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            return img_bgr
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            # Fallback: just convert PIL to numpy BGR
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    def _extract_text_keras(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extract text from image using KerasOCR.
        
        Args:
            image: numpy array in BGR format
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            if not self.ocr_pipeline:
                return "", 0.0
            
            # KerasOCR expects RGB format
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Run OCR
            predictions = self.ocr_pipeline.recognize([image_rgb])
            
            if not predictions or not predictions[0]:
                return "", 0.0
            
            # Extract text and confidence scores
            texts = []
            confidences = []
            
            for text, bbox in predictions[0]:
                if text.strip():  # Only add non-empty text
                    texts.append(text.strip())
                    # KerasOCR doesn't provide confidence scores directly
                    # We'll estimate based on text length and character variety
                    confidence = self._estimate_text_confidence(text)
                    confidences.append(confidence)
            
            if not texts:
                return "", 0.0
            
            # Combine texts and calculate average confidence
            combined_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Clean up text
            clean_text = self._clean_text(combined_text)
            
            return clean_text, avg_confidence
            
        except Exception as e:
            logger.error(f"KerasOCR extraction failed: {e}")
            return "", 0.0
    
    def _estimate_text_confidence(self, text: str) -> float:
        """
        Estimate confidence for extracted text based on characteristics.
        
        Args:
            text: Extracted text string
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not text:
            return 0.0
        
        # Base confidence
        confidence = 0.5
        
        # Longer text tends to be more reliable
        if len(text) >= 3:
            confidence += 0.2
        if len(text) >= 10:
            confidence += 0.1
        
        # Text with mixed alphanumeric characters is usually more reliable
        has_letters = any(c.isalpha() for c in text)
        has_numbers = any(c.isdigit() for c in text)
        has_spaces = ' ' in text
        
        if has_letters:
            confidence += 0.1
        if has_numbers and has_letters:
            confidence += 0.1
        if has_spaces:
            confidence += 0.05
        
        # Penalize text with too many special characters
        special_chars = sum(1 for c in text if not c.isalnum() and c != ' ')
        if special_chars > len(text) * 0.3:  # More than 30% special chars
            confidence -= 0.2
        
        # Ensure confidence is between 0.0 and 1.0
        return max(0.0, min(1.0, confidence))
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove very short or nonsensical fragments
        words = text.split()
        filtered_words = []
        
        for word in words:
            # Keep words that are:
            # - At least 2 characters long
            # - Or single characters that are alphanumeric
            # - Or common single-character words (a, I, etc.)
            if len(word) >= 2 or word.isalnum() or word.lower() in ['a', 'i']:
                filtered_words.append(word)
        
        return ' '.join(filtered_words)
    
    def _calculate_image_hash(self, image: Image.Image) -> str:
        """Calculate a simple hash of the image for change detection."""
        try:
            # Resize to small size for hash calculation
            small_img = image.resize((8, 8), Image.Resampling.LANCZOS)
            
            # Convert to grayscale and get pixel data
            gray_img = small_img.convert('L')
            pixels = list(gray_img.getdata())
            
            # Simple hash based on pixel values
            hash_value = hash(tuple(pixels))
            return str(abs(hash_value))
            
        except Exception as e:
            logger.error(f"Failed to calculate image hash: {e}")
            return str(time.time())
    
    def _is_context_changed(self, new_context: ScreenContext) -> bool:
        """Check if the screen context has significantly changed."""
        if not self.last_context:
            return True
        
        # Check if content is significantly different
        if abs(len(new_context.text_content) - len(self.last_context.text_content)) > 50:
            return True
        
        # Check if image hash changed (simple change detection)
        if new_context.image_hash != self.last_context.image_hash:
            return True
        
        # Check time elapsed
        time_diff = new_context.timestamp - self.last_context.timestamp
        if time_diff > self.capture_interval * 2:
            return True
        
        return False
    
    def get_current_context(self) -> Optional[ScreenContext]:
        """Get the most recent screen context."""
        with self._lock:
            return self.last_context
    
    def force_capture(self) -> Optional[ScreenContext]:
        """Force immediate screen capture and return context."""
        return self.capture_screen_context()
    
    def is_ocr_available(self) -> bool:
        """Check if OCR functionality is available."""
        return self.ocr_pipeline is not None


# Singleton instance
_screen_reader_instance: Optional[ScreenReader] = None


def get_screen_reader() -> ScreenReader:
    """Get the global screen reader instance."""
    global _screen_reader_instance
    if _screen_reader_instance is None:
        _screen_reader_instance = ScreenReader()
    return _screen_reader_instance
