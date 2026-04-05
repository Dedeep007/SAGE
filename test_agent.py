from agent import DesktopAgent
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

agent = DesktopAgent(api_key)
print("\n--- SAGE E2E TESTING SCRIPT ---")
print("Command: Opening notepad, typing some test text, and closing via Alt+F4")
try:
    response = agent.run("Press the Windows key to open the start menu. Type 'notepad'. Press enter to open Notepad. Type 'Hello, SAGE is autonomously controlling this PC successfully!'. Wait a second, and then close notepad using the 'alt+f4' hotkey. If it asks to save, find and click the 'Don't Save' button.")
    print("Final Output:", response)
except Exception as e:
    print("Exception during test:", e)
