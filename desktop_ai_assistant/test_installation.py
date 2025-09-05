"""
Test script to verify SAGE Desktop AI Assistant installation and functionality.
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup basic logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    tests = [
        ("PySide6.QtWidgets", "PySide6 UI framework"),
        ("langchain_groq", "LangChain Groq integration"),
        ("speech_recognition", "Speech recognition"),
        ("keras_ocr", "KerasOCR text recognition"),
        ("mss", "Screen capture"),
        ("pyttsx3", "Text-to-speech"),
        ("pygame", "Audio playback"),
        ("PIL", "Image processing"),
        ("cv2", "OpenCV"),
        ("numpy", "Numerical processing"),
        ("tensorflow", "TensorFlow (for KerasOCR)"),
        ("aiosqlite", "Async SQLite"),
    ]
    
    failed = []
    
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"  ✓ {description}")
        except ImportError as e:
            print(f"  ✗ {description}: {e}")
            failed.append(module_name)
    
    return len(failed) == 0, failed


def test_keras_ocr():
    """Test KerasOCR installation."""
    print("\nTesting KerasOCR...")
    
    try:
        import keras_ocr
        print(f"  ✓ KerasOCR imported successfully")
        
        # Try to initialize pipeline (may take time on first run)
        print("  📦 Initializing KerasOCR pipeline (may download models on first run)...")
        pipeline = keras_ocr.pipeline.Pipeline()
        print(f"  ✓ KerasOCR pipeline initialized")
        return True
    except Exception as e:
        print(f"  ✗ KerasOCR error: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from config.settings import (
            UI_CONFIG, AI_CONFIG, VOICE_CONFIG, 
            SCREEN_CONFIG, GROQ_API_KEY
        )
        
        print(f"  ✓ UI config loaded")
        print(f"  ✓ AI config loaded")
        print(f"  ✓ Voice config loaded")
        print(f"  ✓ Screen config loaded")
        
        if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
            print(f"  ✓ Groq API key configured")
        else:
            print(f"  ⚠ Groq API key not configured")
            
        return True
    except Exception as e:
        print(f"  ✗ Config error: {e}")
        return False


def test_components():
    """Test individual components."""
    print("\nTesting components...")
    
    # Test screen reader
    try:
        from src.screen_reader import get_screen_reader
        screen_reader = get_screen_reader()
        print(f"  ✓ Screen reader initialized")
    except Exception as e:
        print(f"  ✗ Screen reader error: {e}")
    
    # Test voice processor
    try:
        from src.voice_processor import get_voice_processor
        voice_processor = get_voice_processor()
        if voice_processor.is_microphone_available():
            print(f"  ✓ Voice processor initialized with microphone")
        else:
            print(f"  ⚠ Voice processor initialized but no microphone")
    except Exception as e:
        print(f"  ✗ Voice processor error: {e}")
    
    # Test AI agent
    try:
        from src.ai_agent import get_ai_agent
        ai_agent = get_ai_agent()
        print(f"  ✓ AI agent initialized")
    except Exception as e:
        print(f"  ✗ AI agent error: {e}")
    
    # Test database
    try:
        from src.database import get_database_manager
        db_manager = get_database_manager()
        print(f"  ✓ Database manager initialized")
    except Exception as e:
        print(f"  ✗ Database error: {e}")


def test_ui_creation():
    """Test UI creation without showing."""
    print("\nTesting UI creation...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui import FloatingAssistant
        
        # Create application
        app = QApplication([])
        
        # Create assistant (but don't show)
        assistant = FloatingAssistant()
        
        print(f"  ✓ UI created successfully")
        
        # Cleanup
        app.quit()
        return True
        
    except Exception as e:
        print(f"  ✗ UI creation error: {e}")
        return False


def test_directories():
    """Test required directories exist."""
    print("\nTesting directories...")
    
    required_dirs = [
        "config",
        "src", 
        "assets"
    ]
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✓ {dir_name}/ exists")
        else:
            print(f"  ✗ {dir_name}/ missing")
            return False
    
    return True


def main():
    """Run all tests."""
    print("SAGE Desktop AI Assistant - Installation Test")
    print("=" * 50)
    
    all_passed = True
    
    # Test directories
    if not test_directories():
        all_passed = False
    
    # Test imports
    imports_ok, failed_imports = test_imports()
    if not imports_ok:
        all_passed = False
        print(f"\nFailed imports: {', '.join(failed_imports)}")
        print("Run: pip install -r requirements.txt")
    
    # Test KerasOCR
    if not test_keras_ocr():
        all_passed = False
        print("Install KerasOCR with: pip install keras-ocr tensorflow")
    
    # Test configuration
    if not test_config():
        all_passed = False
    
    # Test components (only if imports passed)
    if imports_ok:
        test_components()
        
        # Test UI creation
        if not test_ui_creation():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! SAGE is ready to run.")
        print("\nTo start the application:")
        print("  python main.py")
        print("\nTo build executable:")
        print("  python build.py")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Install KerasOCR: pip install keras-ocr tensorflow")
        print("  3. Configure API keys in .env or config/settings.py")
        print("  4. Note: KerasOCR will download models (~200MB) on first run")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
