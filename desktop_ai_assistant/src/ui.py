"""
Main UI module using PySide6 for the floating AI assistant interface.
Implements a modern, glassmorphic design with animations and drag functionality.
"""
import sys
import asyncio
import logging
from typing import Optional, List
import json
import time

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QLineEdit, QPushButton, QLabel, QFrame,
    QScrollArea, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    QPoint, QRect, QSize, Signal, QThread, QObject
)
from PySide6.QtGui import (
    QPalette, QColor, QFont, QPainter, QPen, QBrush,
    QLinearGradient, QPixmap, QIcon, QKeySequence
)
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from config.settings import UI_CONFIG, VOICE_CONFIG, HOTKEYS
from src.ai_agent import get_ai_agent, ConversationMessage
from src.voice_processor import get_voice_processor, VoiceResult
from src.screen_reader import get_screen_reader, ScreenContext

logger = logging.getLogger(__name__)


class StreamingWorker(QObject):
    """Worker for handling AI streaming responses in a separate thread."""
    token_received = Signal(str)
    response_complete = Signal()
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.ai_agent = get_ai_agent()
    
    async def process_message(self, message: str):
        """Process message and emit streaming tokens."""
        try:
            response_parts = []
            async for token in self.ai_agent.process_message(message):
                response_parts.append(token)
                self.token_received.emit(token)
            
            self.response_complete.emit()
            
        except Exception as e:
            logger.error(f"Error in streaming worker: {e}")
            self.error_occurred.emit(str(e))


class AnimatedButton(QPushButton):
    """Custom button with hover animations."""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(self._get_button_style())
        
        # Animation setup
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(100)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def _get_button_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {UI_CONFIG['accent_color']};
                color: {UI_CONFIG['text_color']};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #0099E5;
            }}
            QPushButton:pressed {{
                background-color: #005A9E;
            }}
            QPushButton:disabled {{
                background-color: #444444;
                color: #888888;
            }}
        """
    
    def enterEvent(self, event):
        """Handle mouse enter for hover effect."""
        super().enterEvent(event)
        # Slight scale animation could be added here
    
    def leaveEvent(self, event):
        """Handle mouse leave."""
        super().leaveEvent(event)


class ChatBubble(QFrame):
    """Custom chat bubble widget with glassmorphic design."""
    
    def __init__(self, text: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text = text
        
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(self._get_bubble_style())
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Text label
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        
        # Set different text color for user vs AI
        text_color = "#FFFFFF" if self.is_user else "#F0F0F0"
        
        self.text_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 14px;
                font-weight: 500;
                line-height: 1.4;
                background: transparent;
                border: none;
                padding: 2px;
            }}
        """)
        
        layout.addWidget(self.text_label)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def _get_bubble_style(self) -> str:
        if self.is_user:
            bg_color = "rgba(0, 122, 204, 0.9)"  # More opaque blue for user
            alignment = "margin-left: 50px;"
            border = "2px solid rgba(0, 122, 204, 0.3);"
        else:
            bg_color = "rgba(70, 70, 70, 0.95)"  # Much more opaque for AI responses
            alignment = "margin-right: 50px;"
            border = "2px solid rgba(255, 255, 255, 0.1);"
        
        return f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 15px;
                {border}
                {alignment}
                margin: 6px;
                padding: 4px;
                min-height: 30px;
            }}
        """
    
    def update_text(self, new_text: str):
        """Update the bubble text (for streaming)."""
        logger.info(f"ChatBubble.update_text called with: '{new_text[:50]}...'")
        self.text = new_text
        self.text_label.setText(new_text)
        # Force refresh
        self.text_label.update()
        self.update()
        logger.info(f"ChatBubble text updated successfully")


class FloatingAssistant(QWidget):
    """Main floating assistant window."""
    
    # Define signals for thread-safe communication
    screen_context_received = Signal(object)  # ScreenContext
    
    def __init__(self):
        super().__init__()
        
        # State variables
        self.is_expanded = False
        self.is_dragging = False
        self.drag_position = QPoint()
        self.chat_bubbles: List[ChatBubble] = []
        self.current_response_bubble: Optional[ChatBubble] = None
        self.is_voice_active = False
        
        # Components
        self.ai_agent = get_ai_agent()
        self.voice_processor = get_voice_processor()
        self.screen_reader = get_screen_reader()
        
        # Streaming worker
        self.streaming_worker = StreamingWorker()
        self.streaming_worker.token_received.connect(self._on_token_received)
        self.streaming_worker.response_complete.connect(self._on_response_complete)
        self.streaming_worker.error_occurred.connect(self._on_error_occurred)
        
        # Screen context signal
        self.screen_context_received.connect(self._handle_screen_context_safe)
        
        # Setup UI
        self._setup_ui()
        self._setup_signals()
        self._setup_voice()
        self._setup_screen_monitoring()
        
        # Setup hotkeys
        self._setup_hotkeys()
        
        # Position window
        self.move(*UI_CONFIG["start_position"])
        
        logger.info("Floating assistant UI initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Window properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set initial size
        self.resize(UI_CONFIG["window_width"], UI_CONFIG["window_height"])
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)
        
        # Create main container with glassmorphic background
        self.container = QFrame()
        self.container.setStyleSheet(self._get_container_style())
        self.main_layout.addWidget(self.container)
        
        # Container layout
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setSpacing(10)
        
        # Header with title and controls
        self._create_header()
        
        # Chat area (initially hidden)
        self._create_chat_area()
        
        # Input area
        self._create_input_area()
        
        # Initially hide chat area
        self.chat_area.hide()
    
    def _get_container_style(self) -> str:
        """Get the glassmorphic container style."""
        return f"""
            QFrame {{
                background-color: {UI_CONFIG['background_color']};
                border-radius: {UI_CONFIG['border_radius']}px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """
    
    def _create_header(self):
        """Create the header with title and controls."""
        header_layout = QHBoxLayout()
        
        # Title
        self.title_label = QLabel("SAGE")
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {UI_CONFIG['text_color']};
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Expand/Collapse button
        self.expand_btn = AnimatedButton("📋")
        self.expand_btn.setFixedSize(30, 30)
        self.expand_btn.clicked.connect(self.toggle_expand)
        self.expand_btn.setToolTip("Expand/Collapse Chat")
        header_layout.addWidget(self.expand_btn)
        
        # Close button
        self.close_btn = AnimatedButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setToolTip("Close SAGE")
        header_layout.addWidget(self.close_btn)
        
        self.container_layout.addLayout(header_layout)
    
    def _create_chat_area(self):
        """Create the expandable chat area."""
        # Chat scroll area
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chat_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }
        """)
        
        # Chat content widget
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("""
            QWidget {
                background: transparent;
                padding: 5px;
            }
        """)
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()  # Push messages to bottom
        
        self.chat_area.setWidget(self.chat_content)
        self.container_layout.addWidget(self.chat_area)
    
    def _create_input_area(self):
        """Create the input area with text field and buttons."""
        input_layout = QHBoxLayout()
        
        # Text input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your message...")
        self.text_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {UI_CONFIG['text_color']};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {UI_CONFIG['accent_color']};
            }}
        """)
        self.text_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.text_input)
        
        # Voice button
        self.voice_btn = AnimatedButton("🎤")
        self.voice_btn.setFixedSize(40, 40)
        self.voice_btn.clicked.connect(self._toggle_voice)
        self.voice_btn.setToolTip("Voice Input (Hold to speak)")
        input_layout.addWidget(self.voice_btn)
        
        # Send button
        self.send_btn = AnimatedButton("➤")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.clicked.connect(self._send_message)
        self.send_btn.setToolTip("Send Message")
        input_layout.addWidget(self.send_btn)
        
        self.container_layout.addLayout(input_layout)
    
    def _setup_signals(self):
        """Setup signal connections."""
        # Enable drag functionality
        self.mousePressEvent = self._mouse_press_event
        self.mouseMoveEvent = self._mouse_move_event
        self.mouseReleaseEvent = self._mouse_release_event
    
    def _setup_voice(self):
        """Setup voice processing."""
        try:
            self.voice_processor.set_voice_callback(self._on_voice_result)
            logger.info("Voice processing setup completed")
        except Exception as e:
            logger.error(f"Failed to setup voice processing: {e}")
            self.voice_btn.setEnabled(False)
    
    def _setup_screen_monitoring(self):
        """Setup screen context monitoring."""
        try:
            self.screen_reader.add_context_callback(self._on_screen_context)
            self.screen_reader.start_monitoring()
            logger.info("Screen monitoring setup completed")
        except Exception as e:
            logger.error(f"Failed to setup screen monitoring: {e}")
    
    def _setup_hotkeys(self):
        """Setup global hotkeys."""
        # Note: For production, you might want to use a library like pynput
        # for global hotkeys. For now, we'll use local shortcuts.
        pass
    
    def toggle_expand(self):
        """Toggle between expanded and collapsed states."""
        target_height = UI_CONFIG["expanded_height"] if not self.is_expanded else UI_CONFIG["window_height"]
        
        # Create animation
        self.expand_animation = QPropertyAnimation(self, b"size")
        self.expand_animation.setDuration(UI_CONFIG["animation_duration"])
        self.expand_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.expand_animation.setStartValue(self.size())
        self.expand_animation.setEndValue(QSize(UI_CONFIG["window_width"], target_height))
        
        # Handle animation completion
        if not self.is_expanded:
            self.expand_animation.finished.connect(lambda: self.chat_area.show())
            self.chat_area.hide()  # Hide during collapse
        else:
            self.chat_area.hide()
        
        self.expand_animation.start()
        self.is_expanded = not self.is_expanded
        
        # Update button icon
        self.expand_btn.setText("📋" if not self.is_expanded else "➖")
    
    def _send_message(self):
        """Send user message to AI."""
        message = self.text_input.text().strip()
        if not message:
            return
        
        self.text_input.clear()
        
        # Ensure chat area is visible
        if not self.is_expanded:
            logger.info("Expanding chat area for message")
            self.toggle_expand()
        
        # Add user message bubble
        self._add_chat_bubble(message, is_user=True)
        
        # Create placeholder for AI response
        self.current_response_bubble = self._add_chat_bubble("", is_user=False)
        logger.info(f"Created AI response bubble: {self.current_response_bubble}")
        
        # Process message asynchronously using QTimer
        QTimer.singleShot(0, lambda: self._schedule_async_task(message))
    
    def _schedule_async_task(self, message: str):
        """Schedule async task safely."""
        try:
            # Use asyncio.run for better compatibility
            import asyncio
            import threading
            
            def run_async():
                try:
                    asyncio.run(self._process_message_async(message))
                except Exception as e:
                    logger.error(f"Error in async task: {e}")
                    # Update UI on error
                    QTimer.singleShot(0, lambda: self._handle_async_error())
            
            # Run in separate thread to avoid blocking UI
            thread = threading.Thread(target=run_async, daemon=True)
            thread.start()
            
        except Exception as e:
            logger.error(f"Error scheduling async task: {e}")
            if self.current_response_bubble:
                self.current_response_bubble.update_text("Sorry, I encountered an error processing your request.")
    
    def _handle_async_error(self):
        """Handle error from async task."""
        if self.current_response_bubble:
            self.current_response_bubble.update_text("Sorry, I encountered an error processing your request.")
    
    async def _process_message_async(self, message: str):
        """Process message asynchronously."""
        try:
            logger.info(f"Processing message: {message}")
            response_parts = []
            token_count = 0
            async for token in self.ai_agent.process_message(message):
                logger.info(f"Received token: '{token}' (type: {type(token)})")
                response_parts.append(str(token))  # Ensure it's a string
                token_count += 1
                # Update UI safely using QTimer
                full_response = ''.join(response_parts)
                logger.info(f"Token {token_count}: Full response so far: '{full_response[:50]}...'")
                # Use direct method call instead of lambda to avoid closure issues
                self._schedule_ui_update(full_response)
            
            # Mark response as complete
            try:
                logger.info(f"Response complete. Total tokens: {token_count}, Final response: {full_response}")
            except UnicodeEncodeError:
                logger.info(f"Response complete. Total tokens: {token_count}, Final response: {repr(full_response)}")
            QTimer.singleShot(0, lambda: self._mark_response_complete())
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            QTimer.singleShot(0, lambda: self._handle_message_error())
    
    def _schedule_ui_update(self, response_text: str):
        """Schedule UI update for response text."""
        logger.info(f"Scheduling UI update with: '{response_text[:50]}...'")
        QTimer.singleShot(0, lambda: self._update_response_bubble(response_text))
    
    def _update_response_bubble(self, response: str):
        """Update response bubble in UI thread."""
        logger.info(f"_update_response_bubble called with: '{response[:50]}...'")
        
        if self.current_response_bubble:
            logger.info("Current response bubble exists, updating text...")
            self.current_response_bubble.update_text(response)
            self._scroll_to_bottom()
            # Force a visual update
            self.current_response_bubble.repaint()
            self.chat_area.repaint()
            logger.info("Response bubble updated successfully")
        else:
            logger.warning("No current response bubble to update!")
    
    def _mark_response_complete(self):
        """Mark response as complete in UI thread."""
        logger.info("Marking response as complete...")
        # Get the final response text to speak
        if self.current_response_bubble and VOICE_CONFIG.get("ai_speak_responses", True):
            final_response = self.current_response_bubble.text_label.text()
            logger.info(f"Final response text: {final_response[:100]}...")
            if final_response.strip():
                # Schedule speaking the response
                logger.info("Scheduling AI speech...")
                QTimer.singleShot(100, lambda: self._speak_response(final_response))
        
        self.current_response_bubble = None
    
    def _speak_response(self, response_text: str):
        """Speak the AI response."""
        try:
            logger.info(f"Starting to speak response: {response_text[:50]}...")
            # Use threading to avoid blocking UI
            import threading
            def speak_async():
                try:
                    import asyncio
                    logger.info("Running TTS in thread...")
                    asyncio.run(self.voice_processor.speak_text(response_text))
                    logger.info("TTS completed successfully")
                except Exception as e:
                    logger.error(f"Error speaking response: {e}")
            
            thread = threading.Thread(target=speak_async, daemon=True)
            thread.start()
            logger.info("TTS thread started")
            
        except Exception as e:
            logger.error(f"Error scheduling speech: {e}")
    
    def _handle_message_error(self):
        """Handle message processing error in UI thread."""
        if self.current_response_bubble:
            self.current_response_bubble.update_text("Sorry, I encountered an error processing your request.")
        self.current_response_bubble = None
    
    def _add_chat_bubble(self, text: str, is_user: bool = True) -> ChatBubble:
        """Add a chat bubble to the conversation."""
        bubble = ChatBubble(text, is_user)
        
        # Debug logging
        logger.info(f"Adding {'user' if is_user else 'AI'} bubble: {text[:50]}...")
        
        # Insert before the stretch item (which is last)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self.chat_bubbles.append(bubble)
        
        # Ensure bubble is visible
        bubble.show()
        bubble.setVisible(True)
        
        # Force layout update
        self.chat_content.updateGeometry()
        
        # Scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)
        
        return bubble
    
    def _scroll_to_bottom(self):
        """Scroll chat area to bottom."""
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _toggle_voice(self):
        """Toggle voice input."""
        if not self.voice_processor.is_microphone_available():
            self._show_status("Microphone not available")
            return
        
        if not self.is_voice_active:
            self._start_voice_input()
        else:
            self._stop_voice_input()
    
    def _start_voice_input(self):
        """Start voice input."""
        self.is_voice_active = True
        self.voice_btn.setText("🔴")
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border-radius: 20px;
            }
        """)
        
        # Start listening
        asyncio.create_task(self._listen_for_voice())
    
    def _stop_voice_input(self):
        """Stop voice input."""
        self.is_voice_active = False
        self.voice_btn.setText("🎤")
        self.voice_btn.setStyleSheet("")  # Reset to default
    
    async def _listen_for_voice(self):
        """Listen for voice input."""
        try:
            result = self.voice_processor.listen_once(timeout=10.0)
            if result.success and result.text:
                self.text_input.setText(result.text)
                self._send_message()
            else:
                self._show_status("Could not understand voice input")
        except Exception as e:
            logger.error(f"Voice input error: {e}")
            self._show_status("Voice input failed")
        finally:
            self._stop_voice_input()
    
    def _on_voice_result(self, result: VoiceResult):
        """Handle voice recognition result."""
        if result.success and result.text:
            self.text_input.setText(result.text)
            if self.is_voice_active:
                self._send_message()
    
    def _on_screen_context(self, context: ScreenContext):
        """Handle new screen context (called from screen reader thread)."""
        # Emit signal to handle in main thread
        self.screen_context_received.emit(context)
    
    def _handle_screen_context_safe(self, context: ScreenContext):
        """Handle screen context safely in main thread."""
        self.ai_agent.update_screen_context(context)
        
        # Generate and speak proactive suggestion if text content is detected
        if context.text_content and len(context.text_content.strip()) > 20:
            logger.info(f"Screen context detected: {len(context.text_content)} characters")
            
            # Schedule proactive suggestion in main thread
            QTimer.singleShot(2000, lambda: self._generate_proactive_suggestion())
    
    def _show_status(self, message: str):
        """Show temporary status message."""
        # You could implement a toast notification here
        logger.info(f"Status: {message}")
    
    def _mouse_press_event(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def _mouse_move_event(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def _mouse_release_event(self, event):
        """Handle mouse release."""
        self.is_dragging = False
    
    def _on_token_received(self, token: str):
        """Handle streaming token from AI."""
        # This would be used if we used the threaded approach
        pass
    
    def _on_response_complete(self):
        """Handle completion of AI response."""
        self.current_response_bubble = None
    
    def _on_error_occurred(self, error: str):
        """Handle AI processing error."""
        if self.current_response_bubble:
            self.current_response_bubble.update_text(f"Error: {error}")
        self.current_response_bubble = None
    
    def _generate_proactive_suggestion(self):
        """Generate and speak proactive suggestions based on screen content."""
        try:
            # Create a task to generate suggestion
            QTimer.singleShot(0, lambda: self._schedule_suggestion_task())
        except Exception as e:
            logger.error(f"Error generating proactive suggestion: {e}")
    
    def _schedule_suggestion_task(self):
        """Schedule async suggestion generation."""
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Create task
            task = loop.create_task(self._generate_suggestion_async())
            
        except Exception as e:
            logger.error(f"Error scheduling suggestion task: {e}")
    
    async def _generate_suggestion_async(self):
        """Generate proactive suggestion asynchronously."""
        try:
            suggestion = await self.ai_agent.generate_proactive_suggestion()
            if suggestion and VOICE_CONFIG.get("ai_speak_suggestions", True):
                logger.info(f"Generated suggestion: {suggestion}")
                # Speak the suggestion
                await self.voice_processor.speak_text(suggestion)
        except Exception as e:
            logger.error(f"Error in suggestion generation: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Cleanup
        try:
            self.screen_reader.stop_monitoring()
            self.voice_processor.stop_listening()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        event.accept()
    
    def _add_test_messages(self):
        """Add test messages to verify chat visibility (for debugging)."""
        if not self.is_expanded:
            self.toggle_expand()
        
        # Add test user message
        self._add_chat_bubble("Hello, can you see this message?", is_user=True)
        
        # Add test AI response
        self._add_chat_bubble("Yes, I can see your message! This is a test AI response to verify the chat interface is working properly.", is_user=False)


class SAGEApplication(QApplication):
    """Main application class."""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Set application properties
        self.setApplicationName("SAGE Desktop Assistant")
        self.setApplicationVersion("1.0.0")
        self.setQuitOnLastWindowClosed(True)
        
        # Create main window
        self.assistant = FloatingAssistant()
        self.assistant.show()
    
    def run(self):
        """Run the application."""
        return self.exec()


def create_application() -> SAGEApplication:
    """Create and return the SAGE application."""
    app = SAGEApplication(sys.argv)
    return app
