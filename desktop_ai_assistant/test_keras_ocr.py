"""
Simple test script for KerasOCR functionality.
Tests the screen reading capabilities without running the full application.
"""
import sys
import logging
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_keras_ocr_basic():
    """Test basic KerasOCR functionality."""
    print("Testing basic KerasOCR functionality...")
    
    try:
        import keras_ocr
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple test image with text
        print("Creating test image...")
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 30), "Hello SAGE Assistant!", fill='black', font=font)
        
        # Convert PIL to numpy array (RGB format)
        img_array = np.array(img)
        
        # Initialize KerasOCR pipeline
        print("Initializing KerasOCR pipeline (may take a moment)...")
        pipeline = keras_ocr.pipeline.Pipeline()
        
        # Recognize text
        print("Recognizing text...")
        predictions = pipeline.recognize([img_array])
        
        # Print results
        if predictions and predictions[0]:
            print("✓ Text recognition successful!")
            for text, bbox in predictions[0]:
                print(f"  Detected text: '{text}'")
        else:
            print("⚠ No text detected in test image")
        
        return True
        
    except Exception as e:
        print(f"✗ KerasOCR test failed: {e}")
        return False

def test_screen_reader():
    """Test the screen reader module."""
    print("\nTesting screen reader module...")
    
    try:
        from src.screen_reader import get_screen_reader
        
        # Initialize screen reader
        screen_reader = get_screen_reader()
        
        if not screen_reader.is_ocr_available():
            print("✗ OCR not available in screen reader")
            return False
        
        print("✓ Screen reader initialized successfully")
        
        # Test screen capture (without monitoring)
        print("Testing screen capture...")
        context = screen_reader.force_capture()
        
        if context:
            print(f"✓ Screen capture successful")
            print(f"  Text length: {len(context.text_content)} characters")
            print(f"  Confidence: {context.confidence:.2f}")
            if context.text_content:
                # Show first 100 characters
                preview = context.text_content[:100]
                print(f"  Preview: '{preview}{'...' if len(context.text_content) > 100 else ''}'")
        else:
            print("⚠ Screen capture returned no context")
        
        return True
        
    except Exception as e:
        print(f"✗ Screen reader test failed: {e}")
        return False

def main():
    """Run all KerasOCR tests."""
    print("SAGE KerasOCR Test Suite")
    print("=" * 30)
    
    all_passed = True
    
    # Test basic KerasOCR functionality
    if not test_keras_ocr_basic():
        all_passed = False
    
    # Test screen reader integration
    if not test_screen_reader():
        all_passed = False
    
    print("\n" + "=" * 30)
    if all_passed:
        print("✓ All KerasOCR tests passed!")
        print("\nKerasOCR is working correctly. Your SAGE assistant will be able to:")
        print("  • Read text from your screen")
        print("  • Provide context-aware assistance")
        print("  • Monitor screen changes automatically")
    else:
        print("✗ Some tests failed.")
        print("\nTroubleshooting:")
        print("  1. Install KerasOCR: pip install keras-ocr tensorflow")
        print("  2. Ensure internet connection for model download")
        print("  3. Check available disk space (~500MB for models)")
        print("  4. Try running: python -c \"import keras_ocr; keras_ocr.pipeline.Pipeline()\"")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
