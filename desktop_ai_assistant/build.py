"""
Build script for creating executable versions of SAGE Desktop AI Assistant.
Supports both PyInstaller and cx_Freeze.
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path

def clean_build_dirs():
    """Clean previous build directories."""
    print("Cleaning previous build directories...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}")
    
    print("✓ Build directories cleaned")

def build_with_pyinstaller():
    """Build executable using PyInstaller."""
    print("\nBuilding with PyInstaller...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "SAGE_Assistant",
        "--icon", "assets/icon.ico",  # Add icon if available
        "--add-data", "config;config",
        "--add-data", "assets;assets",
        "--hidden-import", "langchain_groq",
        "--hidden-import", "PySide6",
        "--hidden-import", "speech_recognition",
        "--hidden-import", "keras_ocr",
        "--hidden-import", "tensorflow",
        "--hidden-import", "mss",
        "--hidden-import", "pyttsx3",
        "--hidden-import", "pygame",
        "--hidden-import", "PIL",
        "--hidden-import", "cv2",
        "--hidden-import", "numpy",
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "jupyter",
        "main.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✓ PyInstaller build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller build failed: {e}")
        return False
    except FileNotFoundError:
        print("✗ PyInstaller not found. Install with: pip install pyinstaller")
        return False

def build_with_cx_freeze():
    """Build executable using cx_Freeze."""
    print("\nBuilding with cx_Freeze...")
    
    # Create setup_cx.py for cx_Freeze
    setup_content = '''
import sys
from cx_Freeze import setup, Executable

# Dependencies
build_options = {
    "packages": [
        "PySide6", "langchain_groq", "speech_recognition", 
        "keras_ocr", "tensorflow", "mss", "pyttsx3", "pygame", 
        "PIL", "cv2", "numpy", "asyncio", "sqlite3"
    ],
    "excludes": ["tkinter", "matplotlib", "jupyter"],
    "include_files": [
        ("config/", "config/"),
        ("assets/", "assets/")
    ]
}

# Executable
executables = [
    Executable(
        "main.py",
        base="Win32GUI" if sys.platform == "win32" else None,
        target_name="SAGE_Assistant.exe" if sys.platform == "win32" else "SAGE_Assistant",
        icon="assets/icon.ico" if Path("assets/icon.ico").exists() else None
    )
]

setup(
    name="SAGE Desktop AI Assistant",
    version="1.0.0",
    description="Floating Desktop AI Assistant",
    options={"build_exe": build_options},
    executables=executables
)
'''
    
    setup_file = Path("setup_cx.py")
    setup_file.write_text(setup_content)
    
    try:
        subprocess.check_call([sys.executable, "setup_cx.py", "build"])
        print("✓ cx_Freeze build completed successfully")
        
        # Clean up
        setup_file.unlink()
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ cx_Freeze build failed: {e}")
        setup_file.unlink(missing_ok=True)
        return False
    except FileNotFoundError:
        print("✗ cx_Freeze not found. Install with: pip install cx-freeze")
        setup_file.unlink(missing_ok=True)
        return False

def create_installer_script():
    """Create a simple installer script."""
    installer_content = '''
@echo off
echo SAGE Desktop AI Assistant Installer
echo =====================================
echo.

echo Copying files...
if not exist "%LOCALAPPDATA%\\SAGE" mkdir "%LOCALAPPDATA%\\SAGE"
copy /Y "SAGE_Assistant.exe" "%LOCALAPPDATA%\\SAGE\\"
copy /Y "config\\*" "%LOCALAPPDATA%\\SAGE\\config\\" 2>nul

echo Creating desktop shortcut...
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\\shortcut.vbs"
echo sLinkFile = "%USERPROFILE%\\Desktop\\SAGE Assistant.lnk" >> "%TEMP%\\shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\\shortcut.vbs"
echo oLink.TargetPath = "%LOCALAPPDATA%\\SAGE\\SAGE_Assistant.exe" >> "%TEMP%\\shortcut.vbs"
echo oLink.WorkingDirectory = "%LOCALAPPDATA%\\SAGE" >> "%TEMP%\\shortcut.vbs"
echo oLink.Description = "SAGE Desktop AI Assistant" >> "%TEMP%\\shortcut.vbs"
echo oLink.Save >> "%TEMP%\\shortcut.vbs"
cscript /nologo "%TEMP%\\shortcut.vbs"
del "%TEMP%\\shortcut.vbs"

echo.
echo Installation completed successfully!
echo You can now run SAGE from your desktop or from:
echo %LOCALAPPDATA%\\SAGE\\SAGE_Assistant.exe
echo.
pause
'''
    
    installer_file = Path("dist/install.bat")
    installer_file.parent.mkdir(exist_ok=True)
    installer_file.write_text(installer_content)
    print("✓ Created installer script: dist/install.bat")

def package_release():
    """Package the release files."""
    print("\nPackaging release...")
    
    release_dir = Path("dist/SAGE_Release")
    release_dir.mkdir(exist_ok=True)
    
    # Copy executable
    exe_files = list(Path("dist").glob("SAGE_Assistant*"))
    if exe_files:
        shutil.copy2(exe_files[0], release_dir)
    
    # Copy config files
    if Path("config").exists():
        shutil.copytree("config", release_dir / "config", dirs_exist_ok=True)
    
    # Copy assets
    if Path("assets").exists():
        shutil.copytree("assets", release_dir / "config", dirs_exist_ok=True)
    
    # Create README
    readme_content = """
SAGE Desktop AI Assistant
========================

Installation:
1. Run install.bat as Administrator (recommended)
   OR
2. Manually copy SAGE_Assistant.exe to your desired location

Configuration:
1. Edit config/settings.py to set your API keys
2. Set GROQ_API_KEY environment variable

Requirements:
- Tesseract OCR (for screen reading)
- Working microphone (for voice input)
- Internet connection (for AI responses)

Usage:
- Double-click SAGE_Assistant.exe to start
- Click the expand button to open chat
- Use the microphone button for voice input
- Drag the window to move it around

For support, visit: https://github.com/your-repo/sage
"""
    
    (release_dir / "README.txt").write_text(readme_content)
    
    # Copy installer
    if Path("dist/install.bat").exists():
        shutil.copy2("dist/install.bat", release_dir)
    
    print(f"✓ Release packaged in: {release_dir}")

def main():
    """Main build function."""
    print("SAGE Desktop AI Assistant Build Script")
    print("=" * 45)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Clean previous builds
    clean_build_dirs()
    
    # Try building with PyInstaller first
    success = build_with_pyinstaller()
    
    # If PyInstaller fails, try cx_Freeze
    if not success:
        print("\nPyInstaller failed, trying cx_Freeze...")
        success = build_with_cx_freeze()
    
    if success:
        # Create installer script (Windows)
        if sys.platform == "win32":
            create_installer_script()
        
        # Package release
        package_release()
        
        print("\n" + "=" * 45)
        print("✓ Build completed successfully!")
        print(f"Executable created in: dist/")
        print("Release package created in: dist/SAGE_Release/")
        
        if sys.platform == "win32":
            print("\nTo install:")
            print("1. Run dist/SAGE_Release/install.bat as Administrator")
            print("2. Or manually copy files to desired location")
        
    else:
        print("\n" + "=" * 45)
        print("✗ Build failed!")
        print("Please check the errors above and try again")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("2. Install build tools: pip install pyinstaller cx-freeze")
        print("3. Check that main.py runs correctly: python main.py")

if __name__ == "__main__":
    main()
