"""
Simple test to verify chat bubble functionality
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication
from src.ui import FloatingAssistant
import time

def test_chat_bubble():
    app = QApplication(sys.argv)
    
    # Create the assistant
    assistant = FloatingAssistant()
    assistant.show()
    
    # Expand the chat
    assistant.toggle_expand()
    
    # Add test messages
    assistant._add_chat_bubble("Test user message", is_user=True)
    bubble = assistant._add_chat_bubble("Test AI response", is_user=False)
    
    print(f"Created bubble: {bubble}")
    print(f"Bubble visible: {bubble.isVisible()}")
    print(f"Bubble text: {bubble.text_label.text()}")
    
    # Update the bubble
    bubble.update_text("Updated AI response text")
    print(f"Updated text: {bubble.text_label.text()}")
    
    app.exec()

if __name__ == "__main__":
    test_chat_bubble()
