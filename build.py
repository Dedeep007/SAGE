import PyInstaller.__main__
import sys
import os

def build_exe():
    print("Starting build process...")

    # Basic setup for Pyinstaller
    opts = [
        'main.py',
        '--name=DesktopAgent',
        '--onefile',
        '--noconsole',        # Ensures the command prompt is hidden
        '--clean',
        # Any necessary hidden imports (gradio_client, langchain, mss, pyqt6)
        '--hidden-import=langchain_groq',
        '--hidden-import=gradio_client',
        '--hidden-import=pyautogui',
        '--hidden-import=mss',
        '--hidden-import=PyQt6'
    ]

    try:
        PyInstaller.__main__.run(opts)
        print("Build complete! The executable should be in the 'dist' folder.")
    except Exception as e:
        print(f"Error during build: {e}")

if __name__ == '__main__':
    build_exe()
