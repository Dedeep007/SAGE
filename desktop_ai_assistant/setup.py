"""
Setup script for SAGE Desktop AI Assistant.
Handles installation of dependencies and configuration.
"""
import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required Python packages."""
    print("Installing required Python packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Python packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install Python packages: {e}")
        return False

def check_keras_ocr():
    """Check if KerasOCR is installed."""
    print("Checking KerasOCR installation...")
    
    try:
        import keras_ocr
        print("✓ KerasOCR is installed")
        
        # Note about model download
        print("📦 Note: KerasOCR will download models (~200MB) on first run")
        return True
    except Exception:
        print("✗ KerasOCR not found")
        print("Installing KerasOCR will also install TensorFlow (~500MB)")
        print("This provides better OCR without requiring separate software installation")
        return False

def create_directories():
    """Create necessary directories."""
    print("Creating directories...")
    
    directories = [
        "logs",
        "data",
        "assets/icons"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directories created")

def setup_environment():
    """Setup environment variables and configuration."""
    print("\nSetting up environment...")
    
    env_example = """
# SAGE Desktop AI Assistant Environment Variables
# Copy this file to .env and update with your actual API keys

# Groq API Key (Required for AI functionality)
GROQ_API_KEY=your_groq_api_key_here

# OpenAI API Key (Optional, for advanced vision features)
OPENAI_API_KEY=your_openai_api_key_here
"""
    
    env_file = Path(".env.example")
    env_file.write_text(env_example)
    
    print("✓ Created .env.example file")
    print("\nIMPORTANT: Please:")
    print("1. Copy .env.example to .env")
    print("2. Update .env with your actual API keys")
    print("3. Get a Groq API key from: https://console.groq.com/")

def main():
    """Main setup function."""
    print("SAGE Desktop AI Assistant Setup")
    print("=" * 40)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    success = True
    
    # Create directories
    create_directories()
    
    # Install requirements
    if not install_requirements():
        success = False
    
    # Check KerasOCR
    if not check_keras_ocr():
        print("Warning: Screen reading features will be limited without KerasOCR")
    
    # Setup environment
    setup_environment()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure your API keys in .env file")
        print("2. Run the application: python main.py")
    else:
        print("✗ Setup completed with errors")
        print("Please resolve the issues above before running the application")
    
    print("\nFor building an executable:")
    print("Run: python build.py")

if __name__ == "__main__":
    main()
