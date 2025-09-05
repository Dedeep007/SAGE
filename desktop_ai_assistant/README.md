# SAGE Desktop AI Assistant

A production-quality, floating desktop AI assistant with screen reading, voice capabilities, and intelligent context awareness.

## Features

### 🤖 AI-Powered Assistance
- **LangChain + Groq Integration**: Advanced reasoning with streaming responses
- **Context-Aware**: Automatically reads and understands your screen content
- **Conversational Memory**: Maintains conversation history and context

### 🎤 Voice Capabilities
- **Speech Recognition**: Convert speech to text using Google Speech Recognition with offline fallback
- **Text-to-Speech**: High-quality voice responses using Google TTS and local TTS
- **Push-to-Talk**: Easy voice input with visual feedback

### 👁️ Screen Reading
- **OCR Technology**: Real-time screen text extraction using KerasOCR
- **Context Analysis**: Intelligent content filtering and relevance detection
- **Automatic Monitoring**: Continuous screen context updates

### 🎨 Modern UI
- **Floating Design**: Always-on-top, draggable window
- **Glassmorphic Styling**: Modern, translucent design with blur effects
- **Smooth Animations**: Polished expand/collapse and interaction animations
- **Responsive Layout**: Adapts to content and user interactions

### 💾 Data Management
- **SQLite Database**: Local storage for conversation history
- **Privacy-First**: All data stored locally, no cloud dependencies
- **Smart Cleanup**: Automatic database maintenance and optimization

## Quick Start

### Prerequisites

1. **Python 3.8+** installed on your system
2. **KerasOCR** for screen reading functionality (auto-installed)
3. **Groq API Key** for AI functionality

### Installation

1. **Clone or download** this repository
2. **Navigate** to the project directory:
   ```bash
   cd desktop_ai_assistant
   ```
3. **Run the setup script**:
   ```bash
   python setup.py
   ```
4. **Configure API keys**:
   - Copy `.env.example` to `.env`
   - Add your Groq API key: `GROQ_API_KEY=your_actual_key_here`
   - Get a key from: https://console.groq.com/

### Running the Application

```bash
python main.py
```

## Building an Executable

To create a standalone executable (.exe file):

1. **Install build dependencies**:
   ```bash
   pip install pyinstaller cx-freeze
   ```

2. **Run the build script**:
   ```bash
   python build.py
   ```

3. **Find your executable** in the `dist/SAGE_Release/` folder

4. **Install using the provided installer**:
   - Run `install.bat` as Administrator (Windows)
   - Or manually copy files to your desired location

## Configuration

### API Keys

Set your API keys in one of these ways:

1. **Environment Variables** (Recommended):
   ```bash
   set GROQ_API_KEY=your_key_here
   ```

2. **Configuration File**:
   Edit `config/settings.py` and update the API key values

### UI Customization

Modify `config/settings.py` to customize:

- Window size and position
- Colors and styling
- Animation speeds
- Hotkeys

### Voice Settings

Configure voice processing in `config/settings.py`:

- Microphone settings
- Speech recognition parameters
- TTS voice and speed

### Screen Reading

Adjust OCR and screen monitoring:

- Capture intervals
- OCR confidence thresholds
- Screen regions to monitor

## Usage Guide

### Basic Operation

1. **Start the application** - The floating window appears
2. **Expand the chat** - Click the 📋 button
3. **Type messages** - Use the text input field
4. **Voice input** - Click the 🎤 button and speak
5. **Move the window** - Click and drag anywhere on the window

### Voice Commands

- **Hold microphone button** - For push-to-talk
- **Speak clearly** - The system supports natural language
- **Wait for processing** - Voice recognition takes a moment

### Screen Context

- **Automatic monitoring** - SAGE reads your screen continuously
- **Context-aware responses** - AI understands what you're looking at
- **Privacy control** - All processing happens locally

### Keyboard Shortcuts

- **Ctrl+Space** - Toggle expand/collapse (when implemented)
- **Enter** - Send text message
- **Escape** - Minimize or close

## Architecture

### Core Components

```
main.py                 # Application entry point
├── src/
│   ├── ui.py          # PySide6-based floating UI
│   ├── ai_agent.py    # LangChain + Groq AI integration
│   ├── voice_processor.py  # Speech recognition & TTS
│   ├── screen_reader.py    # OCR and screen monitoring
│   ├── database.py    # SQLite data management
│   └── logging_config.py   # Logging setup
├── config/
│   └── settings.py    # Configuration management
└── assets/            # UI assets and icons
```

### Technology Stack

- **UI Framework**: PySide6 (Qt for Python)
- **AI/ML**: LangChain, Groq API, OpenAI (optional)
- **Voice**: SpeechRecognition, pyttsx3, gTTS, pygame
- **Vision**: OpenCV, Pillow, KerasOCR, mss
- **Database**: SQLite with aiosqlite
- **System**: pynput for hotkeys, psutil for system info

## Troubleshooting

### Common Issues

**"KerasOCR not found"**
- Install with: `pip install keras-ocr tensorflow`
- Note: Downloads ~200MB of models on first run
- No separate software installation required

**"Microphone not working"**
- Check microphone permissions
- Install PyAudio: `pip install pyaudio`
- Test with other applications

**"API key errors"**
- Verify your Groq API key is correct
- Check internet connection
- Ensure API quota is available

**"Import errors"**
- Run: `pip install -r requirements.txt`
- Use Python 3.8 or newer
- Check for conflicting installations

### Performance Optimization

**Reduce CPU usage**:
- Increase screen capture interval in settings
- Lower OCR confidence threshold
- Disable screen monitoring if not needed

**Improve response speed**:
- Use local TTS instead of Google TTS
- Reduce AI context window size
- Clear conversation history regularly

### Logging and Debugging

Logs are stored in `logs/sage.log`. To enable debug mode:

1. Edit `config/settings.py`
2. Change `LOGGING_CONFIG["level"] = "DEBUG"`
3. Restart the application

## Development

### Project Structure

- **Modular Design**: Each component is self-contained
- **Async Support**: Non-blocking operations for better UX
- **Error Handling**: Comprehensive exception management
- **Configuration**: Centralized settings management

### Extending Functionality

**Add new AI capabilities**:
- Modify `src/ai_agent.py`
- Add new LangChain tools or agents
- Update system prompts in `config/settings.py`

**Customize UI**:
- Edit `src/ui.py`
- Modify stylesheets and layouts
- Add new widgets or animations

**Integrate new APIs**:
- Add new modules in `src/`
- Update configuration in `config/settings.py`
- Handle API keys and authentication

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Security and Privacy

### Data Protection

- **Local Storage**: All data stays on your machine
- **No Cloud Dependencies**: Core functionality works offline
- **Encrypted Storage**: Database can be encrypted (optional)

### API Security

- **Environment Variables**: Keep API keys out of code
- **Rate Limiting**: Built-in request throttling
- **Error Handling**: Secure error messages

### Screen Privacy

- **Selective Monitoring**: Configure specific screen regions
- **Content Filtering**: OCR confidence thresholds
- **User Control**: Easy to disable screen reading

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: Check this README and code comments
- **Issues**: Report bugs via GitHub issues
- **Discussions**: Join community discussions
- **Updates**: Follow releases for new features

## Roadmap

### Upcoming Features

- [ ] Global hotkeys for system-wide access
- [ ] Plugin system for extensibility
- [ ] Multiple AI provider support
- [ ] Advanced screen analysis with computer vision
- [ ] Team collaboration features
- [ ] Mobile companion app

### Performance Improvements

- [ ] Optimized OCR processing
- [ ] Better memory management
- [ ] Faster startup times
- [ ] Reduced battery usage on laptops

---

**Made with ❤️ for productivity and AI enthusiasts**

*SAGE - Your intelligent desktop companion*
