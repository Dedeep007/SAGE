"""
Simple test to verify chat bubble visibility
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea
from PySide6.QtCore import QTimer
from src.ui import ChatBubble

def test_bubble_visibility():
    app = QApplication(sys.argv)
    
    # Create a simple window
    window = QWidget()
    window.setWindowTitle("Bubble Test")
    window.resize(400, 300)
    window.setStyleSheet("background-color: #2b2b2b;")
    
    layout = QVBoxLayout(window)
    
    # Create scroll area like in the main app
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    
    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    
    # Add test bubbles
    user_bubble = ChatBubble("This is a user message", is_user=True)
    ai_bubble = ChatBubble("This is an AI response", is_user=False)
    
    content_layout.addWidget(user_bubble)
    content_layout.addWidget(ai_bubble)
    content_layout.addStretch()
    
    scroll_area.setWidget(content_widget)
    layout.addWidget(scroll_area)
    
    window.show()
    
    # Test updating the AI bubble
    def update_ai_bubble():
        ai_bubble.update_text("Updated AI response - this should be visible!")
        print(f"AI bubble visible: {ai_bubble.isVisible()}")
        print(f"AI bubble text: '{ai_bubble.text_label.text()}'")
        print(f"AI bubble geometry: {ai_bubble.geometry()}")
    
    QTimer.singleShot(2000, update_ai_bubble)
    
    app.exec()

if __name__ == "__main__":
    test_bubble_visibility()
