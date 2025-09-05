"""
Main entry point for the SAGE Desktop AI Assistant.
"""
import sys
import asyncio
import logging
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging first
from src.logging_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    try:
        import PySide6
    except ImportError:
        missing_deps.append("PySide6")
    
    try:
        import langchain_groq
    except ImportError:
        missing_deps.append("langchain-groq")
    
    try:
        import speech_recognition
    except ImportError:
        missing_deps.append("SpeechRecognition")
    
    try:
        import keras_ocr
    except ImportError:
        missing_deps.append("keras-ocr")
    
    try:
        import mss
    except ImportError:
        missing_deps.append("mss")
    
    if missing_deps:
        logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
        logger.error("Please install missing dependencies with: pip install -r requirements.txt")
        return False
    
    return True

def check_api_keys():
    """Check if required API keys are configured."""
    from config.settings import GROQ_API_KEY
    
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        logger.warning("GROQ_API_KEY not configured. Please set the GROQ_API_KEY environment variable or update config/settings.py")
        return False
    
    return True

def check_keras_ocr():
    """Check if KerasOCR is installed and accessible."""
    try:
        import keras_ocr
        # Try to create a pipeline to ensure it works
        pipeline = keras_ocr.pipeline.Pipeline()
        return True
    except Exception as e:
        logger.error(f"KerasOCR not found or not accessible: {e}")
        logger.error("Please install KerasOCR with: pip install keras-ocr tensorflow")
        return False

def main():
    """Main application entry point."""
    logger.info("Starting SAGE Desktop AI Assistant...")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check API keys
    if not check_api_keys():
        logger.warning("Some features may not work without proper API key configuration")
    
    # Check KerasOCR
    if not check_keras_ocr():
        logger.warning("Screen reading features will not work without KerasOCR")
    
    try:
        # Import and create application
        from src.ui import create_application
        
        # Create application
        app = create_application()
        
        logger.info("SAGE Desktop AI Assistant started successfully")
        
        # Run application
        sys.exit(app.run())
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
