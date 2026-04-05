import sys
import os
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false;*.debug=false"
from PyQt6.QtWidgets import QApplication
from ui import FloatingBubble
from dotenv import load_dotenv

def main():
    load_dotenv()
    # Read the GROQ API key from the environment variables (loaded by dotenv)
    groq_api_key = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
    if groq_api_key == "YOUR_GROQ_API_KEY_HERE":
        print("WARNING: Please set your GROQ_API_KEY environment variable or replace it in main.py.")

    app = QApplication(sys.argv)
    
    bubble = FloatingBubble(groq_api_key)
    bubble.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
