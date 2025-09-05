# SAGE Desktop AI Assistant - Complete Setup Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Prerequisites
1. **Install Python 3.8+**
   - Download from: https://python.org
   - ✅ Check "Add Python to PATH" during installation

2. **Get Groq API Key**
   - Visit: https://console.groq.com/
   - Sign up/login and create an API key
   - Copy the key (you'll need it in Step 3)

3. **Note about KerasOCR**
   - KerasOCR will be installed automatically with the requirements
   - It will download ML models (~200MB) on first run
   - No separate software installation needed!

### Step 2: Install SAGE
1. **Download/Clone** this project to your desired folder
2. **Open Command Prompt** or PowerShell in the project folder
3. **Run setup**:
   ```bash
   python setup.py
   ```

### Step 3: Configure API Key
1. **Copy the example environment file**:
   ```bash
   copy .env.example .env
   ```
2. **Edit .env file** and add your Groq API key:
   ```
   GROQ_API_KEY=your_actual_groq_api_key_here
   ```

### Step 4: Test Installation
```bash
python test_installation.py
```

### Step 5: Run SAGE
```bash
python main.py
```
Or double-click `run.bat` on Windows.

---

## 🛠️ Detailed Installation

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Python**: 3.8 or newer
- **RAM**: 4GB minimum, 8GB recommended (for TensorFlow/KerasOCR)
- **Storage**: 1GB for application + dependencies + ML models
- **Internet**: Required for AI responses and initial model download

### Dependencies Installation

#### Windows
```powershell
# Install Python packages
python -m pip install --upgrade pip
pip install -r requirements.txt

# Install Tesseract OCR
# Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install tesseract
pip install -r requirements.txt
```

#### Linux (Ubuntu/Debian)
```bash
# Update system
sudo apt update

# Install system dependencies
sudo apt install tesseract-ocr tesseract-ocr-eng python3-pip portaudio19-dev

# Install Python packages
pip3 install -r requirements.txt
```

### Manual Dependency Check
If automatic installation fails, install packages individually:

```bash
# Core UI and system
pip install PySide6>=6.6.0
pip install psutil>=5.9.0

# AI and LangChain
pip install langchain>=0.1.0
pip install langchain-groq>=0.1.0
pip install groq>=0.4.0

# Voice processing
pip install SpeechRecognition>=3.10.0
pip install pyttsx3>=2.90
pip install gTTS>=2.4.0
pip install pygame>=2.5.0
pip install pyaudio>=0.2.11

# Screen capture and OCR
pip install Pillow>=10.0.0
pip install keras-ocr>=0.9.0
pip install mss>=9.0.0
pip install opencv-python>=4.8.0
pip install tensorflow>=2.8.0

# System integration
pip install pynput>=1.7.6

# Database
pip install aiosqlite>=0.19.0

# Utilities
pip install python-dotenv>=1.0.0
pip install requests>=2.31.0
```

---

## 🎯 Configuration Guide

### API Keys Setup

#### Method 1: Environment File (Recommended)
1. Copy `.env.example` to `.env`
2. Edit `.env`:
   ```
   GROQ_API_KEY=gsk_your_actual_groq_api_key_here
   OPENAI_API_KEY=sk-your_openai_key_here  # Optional
   ```

#### Method 2: System Environment Variables
```bash
# Windows (Command Prompt)
set GROQ_API_KEY=your_key_here

# Windows (PowerShell)
$env:GROQ_API_KEY="your_key_here"

# macOS/Linux
export GROQ_API_KEY="your_key_here"
```

#### Method 3: Direct Configuration
Edit `config/settings.py`:
```python
GROQ_API_KEY = "your_actual_groq_api_key_here"
```

### KerasOCR Configuration
KerasOCR works automatically with no configuration needed!

**Advantages of KerasOCR over Tesseract:**
- ✅ No separate software installation required
- ✅ Better text detection and recognition accuracy
- ✅ Works well with complex layouts and fonts
- ✅ Built-in text detection and recognition
- ✅ Deep learning-based approach

**First Run Notes:**
- KerasOCR will download pre-trained models (~200MB) on first use
- This happens automatically and only once
- Models are cached for future use

### UI Customization
Edit `config/settings.py` to customize:

```python
UI_CONFIG = {
    "window_width": 350,           # Initial width
    "window_height": 120,          # Collapsed height
    "expanded_height": 500,        # Expanded height
    "background_color": "rgba(30, 30, 30, 0.9)",  # Window background
    "accent_color": "#007ACC",     # Button and accent color
    "start_position": (100, 100),  # Initial position (x, y)
}
```

### Voice Settings
```python
VOICE_CONFIG = {
    "tts_language": "en",          # TTS language
    "speech_timeout": 5.0,         # Voice input timeout
    "phrase_timeout": 1.0,         # Phrase detection timeout
}
```

### AI Settings
```python
AI_CONFIG = {
    "model": "llama-3.1-70b-versatile",  # Groq model
    "temperature": 0.7,                   # Response creativity
    "max_tokens": 500,                    # Response length
    "screen_capture_interval": 5.0,       # Screen monitoring frequency
}
```

---

## 🎮 Usage Guide

### Basic Operations

#### Starting the Application
1. **Command line**: `python main.py`
2. **Windows**: Double-click `run.bat`
3. **From anywhere**: After building executable

#### Main Interface
- **Drag to move**: Click and drag anywhere on the window
- **Expand/Collapse**: Click the 📋 button
- **Voice input**: Click the 🎤 button
- **Text input**: Type in the text field and press Enter
- **Close**: Click the ✕ button

#### Chat Features
- **Text messages**: Type and press Enter or click ➤
- **Voice messages**: Click 🎤, speak, system will auto-detect end
- **Screen context**: AI automatically sees your screen content
- **History**: Previous conversations are saved and accessible

### Voice Usage

#### Push-to-Talk Mode
1. Click the microphone button 🎤
2. Button turns red 🔴 when listening
3. Speak clearly into your microphone
4. System automatically detects when you finish
5. Text appears in input field
6. Message is sent automatically

#### Voice Responses
- AI can respond with voice using TTS
- Toggle voice responses in settings
- Choose between Google TTS (better quality) or local TTS (faster)

#### Troubleshooting Voice
- **No microphone detected**: Check system audio settings
- **Poor recognition**: Speak clearly, reduce background noise
- **No voice output**: Check system volume and audio settings

### Screen Reading

#### How It Works
- SAGE continuously monitors your screen
- Extracts text using OCR (Optical Character Recognition)
- Provides this context to the AI for relevant assistance

#### What It Sees
- Text from applications, documents, web pages
- UI elements with text content
- Does NOT capture images, videos, or graphical content

#### Privacy Notes
- All screen processing happens locally
- No screen content is sent to the cloud
- You can disable screen monitoring in settings

### AI Assistance

#### Context-Aware Help
- AI sees what's on your screen
- Provides relevant suggestions and assistance
- Understands the context of your current activity

#### Example Interactions
- **Coding**: "Explain this error message"
- **Reading**: "Summarize this document"
- **Research**: "Find more information about this topic"
- **General**: "What should I do next with this?"

#### Conversation Memory
- AI remembers your conversation history
- Maintains context across multiple messages
- Can reference previous discussions

---

## 🔧 Troubleshooting

### Installation Issues

#### "Python not found"
- Install Python from https://python.org
- Ensure "Add to PATH" was selected during installation
- Restart command prompt after installation

#### "pip not found"
- Python 3.4+ includes pip automatically
- If missing: `python -m ensurepip --upgrade`

#### "Module not found" errors
```bash
# Reinstall requirements
pip install --force-reinstall -r requirements.txt

# Install specific packages
pip install PySide6 langchain-groq speech_recognition
```

#### "Permission denied" errors
```bash
# Windows: Run Command Prompt as Administrator
# macOS/Linux: Use sudo for system-wide install
sudo pip install -r requirements.txt

# Or install to user directory
pip install --user -r requirements.txt
```

### Runtime Issues

#### "Tesseract not found"
1. **Install Tesseract OCR**:
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - macOS: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`

2. **Set path manually** in `config/settings.py`:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

#### "API key not configured"
- Check your `.env` file exists and contains the correct key
- Verify the key is valid at https://console.groq.com/
- Ensure no extra spaces or quotes around the key

#### "Microphone not working"
1. **Check system permissions**: Grant microphone access to Python
2. **Test microphone**: Use Windows Sound Recorder or similar
3. **Install PyAudio**: `pip install pyaudio`
4. **Check device**: Run test: `python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"`

#### "UI not appearing"
- Check if running in background: Look for SAGE in system tray
- Try different screen position: Edit `start_position` in settings
- Check for multiple displays: Window might be on different screen

#### "Slow performance"
- Increase screen capture interval in settings
- Reduce AI context window size
- Close other resource-intensive applications
- Check available RAM (need at least 2GB free)

### Application Errors

#### "Failed to initialize LLM"
- Verify internet connection
- Check API key is correct and has quota
- Try different Groq model in settings

#### "OCR extraction failed"
- Update graphics drivers
- Check screen scaling settings (100% recommended)
- Verify Tesseract installation

#### "Voice processing error"
- Check microphone permissions
- Install Microsoft Visual C++ Redistributable
- Try different microphone input device

### Performance Optimization

#### Reduce CPU Usage
```python
# In config/settings.py
AI_CONFIG["screen_capture_interval"] = 10.0  # Increase from 5.0
SCREEN_CONFIG["ocr_confidence_threshold"] = 80  # Increase from 60
```

#### Reduce Memory Usage
```python
# In config/settings.py
AI_CONFIG["max_context_history"] = 5  # Reduce from 10
DATABASE_CONFIG["max_history"] = 500  # Reduce from 1000
```

#### Improve Response Speed
```python
# In config/settings.py
VOICE_CONFIG["use_gtts"] = False  # Use local TTS instead
AI_CONFIG["max_tokens"] = 200  # Reduce response length
```

---

## 🔨 Building Executable

### Prerequisites for Building
```bash
# Install build tools
pip install pyinstaller cx-freeze
```

### Build Process
```bash
# Run build script
python build.py
```

### Manual Build (PyInstaller)
```bash
pyinstaller --onefile --windowed --name "SAGE_Assistant" main.py
```

### Build Output
- **Executable**: `dist/SAGE_Assistant.exe` (Windows)
- **Release package**: `dist/SAGE_Release/`
- **Installer**: `dist/SAGE_Release/install.bat` (Windows)

### Installation from Executable
1. **Automated**: Run `install.bat` as Administrator
2. **Manual**: Copy executable to desired location

### Portable Usage
- Copy the entire `SAGE_Release` folder to any location
- Run `SAGE_Assistant.exe` directly
- Configuration files will be created in the same folder

---

## 📞 Support and Help

### Getting Help
1. **Check this guide** for common issues
2. **Run diagnostics**: `python test_installation.py`
3. **Check logs**: Look in `logs/sage.log` for error details
4. **Update dependencies**: `pip install --upgrade -r requirements.txt`

### Reporting Issues
When reporting problems, include:
- Your operating system
- Python version (`python --version`)
- Error messages from logs
- Steps to reproduce the issue

### Community
- **Documentation**: This README and PROJECT_STRUCTURE.md
- **Code Comments**: Extensive inline documentation
- **Examples**: Configuration examples in settings.py

---

## 🎉 Congratulations!

You now have a fully functional AI desktop assistant with:
- ✅ Floating, always-on-top interface
- ✅ Voice input and output
- ✅ Screen reading and context awareness
- ✅ Intelligent AI responses with streaming
- ✅ Local data storage and privacy
- ✅ Production-quality code and error handling

**Enjoy your new AI companion!** 🤖✨
