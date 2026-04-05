import os
import time
from dotenv import load_dotenv
load_dotenv()
from tools import find_click_and_type_tool, read_screen_text_tool, press_key_tool

print("Opening Brave Browser...")
os.system("start brave")
time.sleep(4) 

print("\n--- Visual Grounding Test ---")
print("Agent is reading the screen natively:")
print(read_screen_text_tool.invoke("Describe the browser header and find a bookmark or extension icon."))

print("\n--- Precision Macro Test ---")
print("Target: 'Chrome address bar, dragon'")
res = find_click_and_type_tool.invoke("Chrome address bar, dragon")
print(res)

time.sleep(2)
press_key_tool.invoke("alt+f4")
print("Browser Closed.")
