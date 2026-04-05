import os
import time
from langchain.tools import tool
import pyautogui
from mss import mss
from gradio_client import Client, handle_file
import subprocess
import traceback

# Optional safety measure for PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

def take_screenshot(filename='current_screenshot.png'):
    try:
        with mss() as sct:
            sct.shot(output=filename)
        return filename
    except Exception as e:
        return None

def _get_element_coordinates(instruction: str) -> tuple[int, int]:
    time.sleep(1.0)
    image_path = take_screenshot()
    if not image_path:
        raise Exception("Failed to take screenshot.")
    
    max_retries = 3
    result = None
    for attempt in range(max_retries):
        try:
            client = Client("johnisafridge/GUI-Actor")
            result = client.predict(
                    image=handle_file(image_path),
                    instruction=instruction,
                    api_name="/predict"
            )
            break
        except Exception as e:
            if "ReadTimeout" in str(e) or "timeout" in str(e).lower() or "Connection" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(10) # Wait longer for space to wake up
                    continue
            raise e

    import re
    coords = re.findall(r"[\(\[]([0-9.]+),\s*([0-9.]+)[\)\]]", str(result))
    
    if coords:
        x_norm, y_norm = float(coords[0][0]), float(coords[0][1])
        width, height = pyautogui.size()
        x = int(x_norm * width)
        y = int(y_norm * height)
        return x, y
    else:
        raise Exception(f"GUI-Actor could not natively map the coordinates for '{instruction}'. A pop-up, menu, or off-screen error may be blocking the UI! Use read_screen_text_tool immediately to verify the visual state.")

@tool
def find_and_click_tool(element_description: str) -> str:
    """
    Finds a UI element on the screen based on its visual description and clicks it natively.
    Input: description of what to find and click (e.g. 'search bar', 'submit button').
    """
    try:
        x, y = _get_element_coordinates(element_description)
        pyautogui.moveTo(x, y, duration=0.2)
        pyautogui.click()
        time.sleep(2.0) # Wait for UI response
        screen_info = read_screen_text_tool.invoke("A physical click just occurred. Read out the screen text. Did a new popup, error message, or menu appear?")
        return f"Successfully found and clicked '{element_description}' at ({x}, {y}).\n\n--- POST-ACTION SCREEN STATE ---\n{screen_info}"
    except Exception as e:
        return f"Error executing find_and_click_tool: {traceback.format_exc()}"

@tool
def find_click_and_type_tool(input_params: str) -> str:
    """
    Finds a UI element (like a search bar or text input), clicks it to gain physical focus, and immediately types the specified text.
    Input MUST be a comma-separated string containing exactly: "element_description, text_to_type". 
    Example: "Chrome address bar, dragon"
    """
    try:
        parts = input_params.split(",", 1)
        if len(parts) != 2:
            return "Error: Input must be exactly two parts separated by a comma. Format: 'element description, text to type'"
        
        desc = parts[0].strip()
        text = parts[1].strip()
        
        x, y = _get_element_coordinates(desc)
        pyautogui.moveTo(x, y, duration=0.2)
        pyautogui.click()
        time.sleep(0.5)
        pyautogui.write(text, interval=0.05)
        time.sleep(2.0) # Wait for typing overlay to settle
        screen_info = read_screen_text_tool.invoke("Text was just typed onto the screen. Read out the screen text. Did a popup, error, or new dialog appear?")
        return f"Successfully found '{desc}', physically clicked it, and typed '{text}'.\n\n--- POST-ACTION SCREEN STATE ---\n{screen_info}"
    except Exception as e:
        return f"Error executing find_click_and_type_tool: {traceback.format_exc()}"

@tool
def scroll_screen_tool(direction_and_amount: str) -> str:
    """
    Scrolls the screen autonomously.
    Input should be the direction and amount, e.g., 'down 500' or 'up 300'.
    """
    try:
        parts = direction_and_amount.lower().split()
        direction = parts[0] if len(parts) > 0 else "down"
        amount = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 500
        
        clicks = -amount if direction == "down" else amount
        pyautogui.scroll(clicks)
        return f"Successfully scrolled {direction} by {amount} units."
    except Exception as e:
        return f"Error executing scroll_screen_tool: {traceback.format_exc()}"

@tool
def read_screen_text_tool(instruction: str = "Read all text and describe what is visible on the screen.") -> str:
    """
    Reads the screen text and analyzes its content using a visual model.
    Input: instruction or query about the screen content.
    """
    try:
        import base64
        import time
        from groq import Groq
        
        # Delay up to 1s to allow UI to gracefully collapse and not block text content from vision
        time.sleep(1.0)
        
        image_path = take_screenshot()
        if not image_path:
            return "Failed to take screenshot."
            
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        client = Groq()
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
              {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": f"data:image/webp;base64,{base64_image}"}}
                ]
              }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None
        )
        
        result = ""
        for chunk in completion:
            result += chunk.choices[0].delta.content or ""
            
        return f"Screen Analysis:\n{result}"
        
    except Exception as e:
        return f"Error executing read_screen_text_tool: {traceback.format_exc()}"

@tool
def open_application_tool(app_name: str) -> str:
    """
    Searches for and opens a local application by its name or command 
    (e.g., 'notepad', 'calc', 'chrome').
    ALWAYS use this tool when the user asks to open an app or folder.
    """
    try:
        if " " in app_name:
            command = app_name
        else:
            command = f"start {app_name}"
            
        result = os.system(command)
        
        if result == 0:
            time.sleep(3.5) # Wait for App Boot
            screen_info = read_screen_text_tool.invoke(f"{app_name} was just opened. Does the screen show the app, or is there a profile selector or menu blocking it?")
            return f"Successfully executed start command for '{app_name}'.\n\n--- POST-ACTION SCREEN STATE ---\n{screen_info}"
        else:
            return f"Failed to execute command. Attempted: '{command}'. Return code: {result}"
            
    except Exception as e:
        return f"Error launching {app_name}: {traceback.format_exc()}"



@tool
def type_text_immediately_tool(text: str) -> str:
    """
    Types the given text on the keyboard IMMEDIATELY, assuming the target input is ALREADY focused.
    Extremely useful directly after pressing the Windows key to search!
    WARNING: For browsers or web pages, you MUST use find_click_and_type_tool instead to prevent losing focus!
    """
    try:
        pyautogui.write(text, interval=0.05)
        return f"Successfully typed: '{text}'"
    except Exception as e:
        return f"Error executing type_text_immediately_tool: {traceback.format_exc()}"

@tool
def press_key_tool(key: str) -> str:
    """
    Presses a specific key or hotkey combination.
    Examples: 'enter', 'win', 'space', 'tab', 'down', 'alt+f4', 'ctrl+c'.
    """
    try:
        keys = [k.strip().lower() for k in key.split("+")]
        if len(keys) > 1:
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(keys[0])
        time.sleep(1.5)
        screen_info = read_screen_text_tool.invoke(f"Keys '{key}' were pressed. Read out the screen changes.")
        return f"Successfully pressed key(s): '{key}'.\n\n--- POST-ACTION SCREEN STATE ---\n{screen_info}"
    except Exception as e:
        return f"Error executing press_key_tool: {traceback.format_exc()}"

# Ensure tools are easily imported
TOOLS = [find_and_click_tool, find_click_and_type_tool, scroll_screen_tool, read_screen_text_tool, open_application_tool, type_text_immediately_tool, press_key_tool]
