import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QHBoxLayout, QFrame, 
                             QGraphicsDropShadowEffect, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QPointF, QSize, QPropertyAnimation, QEasingCurve, QTimer, QEvent
from PyQt6.QtGui import QMouseEvent, QFont, QColor, QPainter, QPen

try:
    from agent import DesktopAgent
except ImportError:
    class DesktopAgent:
        def __init__(self, key): pass
        def run(self, cmd, callbacks=None): return f"Processed: {cmd}"
        def stop(self): pass

from langchain_core.callbacks import BaseCallbackHandler

class UICallbackHandler(BaseCallbackHandler):
    def __init__(self, callback_signal, action_state_signal, hide_ui_signal):
        self.callback_signal = callback_signal
        self.action_state_signal = action_state_signal
        self.hide_ui_signal = hide_ui_signal

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
        tool_name = serialized.get("name", "tool")
        self.callback_signal.emit(f"⚙️ Using: {tool_name}...")
        
        action_tools = ["find_and_click_tool", "find_click_and_type_tool", "type_text_immediately_tool", "press_key_tool", "scroll_screen_tool"]
        if tool_name in action_tools:
            self.action_state_signal.emit(True)
            self.hide_ui_signal.emit()

    def on_tool_end(self, output: str, **kwargs):
        self.action_state_signal.emit(False)

    def on_tool_error(self, error: BaseException, **kwargs):
        self.action_state_signal.emit(False)

    def on_llm_start(self, serialized: dict, prompts: list, **kwargs):
        self.callback_signal.emit("✨ SAGE is thinking...")

class AgentWorker(QThread):
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_update = pyqtSignal(str)
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal()
    action_state_changed = pyqtSignal(bool)
    hide_ui = pyqtSignal()

    def __init__(self, agent: DesktopAgent, command: str):
        super().__init__()
        self.agent = agent
        self.command = command

    def run(self):
        try:
            self.processing_started.emit()
            handler = UICallbackHandler(self.status_update, self.action_state_changed, self.hide_ui)
            result = self.agent.run(self.command, callbacks=[handler])
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.processing_finished.emit()

class ScreenBorderOverlay(QWidget):
    """Fullscreen overlay to brighten screen borders while SAGE is working."""
    def __init__(self):
        super().__init__()
        # Ensure it's not interactive, stays on top, has no icon
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Get primary screen resolution
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.setGeometry(screen_geometry)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dynamic glow border around the screen
        pen = QPen(QColor(167, 139, 250, 200)) # Vivid purple
        pen.setWidth(20) # Thick border
        # Draw inside boundaries properly
        painter.setPen(pen)
        rect = self.rect()
        rect.adjust(10, 10, -10, -10)
        painter.drawRect(rect)


class DraggableButton(QPushButton):
    dragged = pyqtSignal(QPoint)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            # If we don't call super, we don't get the clicked effect.
            # We delay the click using logic or just call super.
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            if delta.manhattanLength() > 5: # Small threshold to differentiate click vs drag
                self.dragged.emit(delta)
                self.old_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        super().mouseReleaseEvent(event)


class ChatBubble(QFrame):
    def __init__(self, text, is_user=True, parent_width=350):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        if is_user:
            bg_color = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #a855f7)"
            text_color = "#FFFFFF"
            radius = "16px 16px 4px 16px"
        else:
            bg_color = "rgba(30, 41, 59, 150)"
            text_color = "#E2E8F0"
            radius = "16px 16px 16px 4px"
            
        self.label.setStyleSheet(f"""
            QLabel {{
                background: {bg_color};
                color: {text_color};
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 13px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        
        # Max width to ensure it doesn't balloon and wraps properly
        self.label.setMaximumWidth(int(parent_width * 0.8))
        
        if is_user:
            layout.addStretch()
            layout.addWidget(self.label)
        else:
            layout.addWidget(self.label)
            layout.addStretch()

class FloatingBubble(QWidget):
    def __init__(self, groq_api_key: str):
        super().__init__()
        self.agent = DesktopAgent(groq_api_key)
        self.is_expanded = False
        self.is_processing = False
        self.old_pos = None
        self.worker = None
        self.overlay = ScreenBorderOverlay()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Ensure wrapper is totally invisible 
        self.setStyleSheet("background: transparent;")
        
        # Windows API hook to make this UI window completely invisible to screenshots!
        try:
            import ctypes
            hwnd = int(self.winId())
            # WDA_EXCLUDEFROMCAPTURE (0x11) hides the window entirely from GDI screen captures natively
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x11)
        except Exception as e:
            print(f"Warning: Could not set window affinity - {e}")
        
        self.init_ui()
        
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(0)

        # 1. Launcher Bubble
        self.bubble_container = QWidget()
        self.bubble_container.setFixedSize(80, 80)
        self.bubble_container.setStyleSheet("background: transparent; border: none;") 
        self.bubble_layout = QVBoxLayout(self.bubble_container)
        self.bubble_layout.setContentsMargins(0,0,10,10)
        self.bubble_layout.setSpacing(5)

        self.floating_status = QLabel("")
        self.floating_status.setStyleSheet("""
            color: #F8FAFC; 
            font-size: 11px; 
            font-weight: bold; 
            background: rgba(15, 23, 42, 220); 
            border-radius: 8px; 
            padding: 5px 10px;
        """)
        self.floating_status.hide()
        self.bubble_layout.addWidget(self.floating_status, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.bubble_btn = DraggableButton("✨")
        self.bubble_btn.setFixedSize(60, 60)
        self.bubble_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.default_bubble_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8b5cf6, stop:1 #ec4899);
                color: white;
                border-radius: 30px;
                font-size: 24px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:hover {
                border: 2px solid rgba(255, 255, 255, 0.6);
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c3aed, stop:1 #db2777);
            }
        """
        self.cancel_bubble_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ef4444, stop:1 #b91c1c);
                color: white;
                border-radius: 30px;
                font-size: 22px;
                font-weight: bold;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                border: 2px solid rgba(255, 255, 255, 0.8);
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #dc2626, stop:1 #991b1b);
            }
        """
        
        self.bubble_btn.setStyleSheet(self.default_bubble_style)
        
        # Glow
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(25)
        self.shadow.setColor(QColor(139, 92, 246, 180))
        self.shadow.setOffset(0, 0)
        self.bubble_btn.setGraphicsEffect(self.shadow)
        
        # Drag Logic
        self.bubble_btn.dragged.connect(self.on_dragged)
        self.bubble_btn.clicked.connect(self.on_bubble_clicked)
        
        self.bubble_layout.addWidget(self.bubble_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 2. Chat Frame
        self.chat_frame = QFrame()
        self.chat_frame.setFixedWidth(380)
        self.chat_frame.setFixedHeight(550)
        self.chat_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 230);
                border-radius: 20px;
                border: none;
            }
        """)
        
        frame_shadow = QGraphicsDropShadowEffect()
        frame_shadow.setBlurRadius(40)
        frame_shadow.setColor(QColor(0, 0, 0, 150))
        frame_shadow.setOffset(0, 15)
        self.chat_frame.setGraphicsEffect(frame_shadow)

        self.chat_layout = QVBoxLayout(self.chat_frame)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(0)

        # Header
        self.header = QWidget()
        self.header.setFixedHeight(65)
        self.header.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(139, 92, 246, 0.1), stop:1 rgba(236, 72, 153, 0.1)); 
            border-top-left-radius: 20px; 
            border-top-right-radius: 20px; 
            border: none;
        """)
        header_layout = QHBoxLayout(self.header)
        
        title_label = QLabel("✦ SAGE Assistant")
        title_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #F8FAFC; border: none; letter-spacing: 1px; background: transparent;")
        
        self.min_btn = QPushButton("—")
        self.min_btn.setFixedSize(32, 32)
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #94A3B8; font-size: 16px; border: none; border-radius: 16px; font-weight: bold; }
            QPushButton:hover { color: #FFFFFF; background: rgba(59, 130, 246, 0.8); }
        """)
        self.min_btn.clicked.connect(self.toggle_mode)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #94A3B8; font-size: 16px; border: none; border-radius: 16px; }
            QPushButton:hover { color: #FFFFFF; background: rgba(239, 68, 68, 0.8); }
        """)
        self.close_btn.clicked.connect(self.close_app)
        
        header_layout.addSpacing(20)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.min_btn)
        header_layout.addWidget(self.close_btn)
        header_layout.addSpacing(10)
        
        self.chat_layout.addWidget(self.header)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: rgba(255,255,255,0.05); width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,0.2); border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.3); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setContentsMargins(10, 15, 10, 15)
        self.scroll_area.setWidget(self.scroll_widget)
        
        self.chat_layout.addWidget(self.scroll_area)

        # Status indicator
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #A78BFA; font-size: 12px; padding: 5px 20px; border: none; font-style: italic; background: transparent;")
        self.status_label.hide()
        self.chat_layout.addWidget(self.status_label)

        # Input Bar
        self.input_container = QWidget()
        self.input_container.setFixedHeight(80)
        self.input_container.setStyleSheet("background: rgba(15, 23, 42, 0.4); border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;")
        input_box_layout = QHBoxLayout(self.input_container)
        input_box_layout.setContentsMargins(15, 15, 15, 15)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask SAGE a command...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 41, 59, 200);
                border: none;
                border-radius: 24px;
                padding: 12px 20px;
                font-size: 14px;
                color: #F8FAFC;
            }
            QLineEdit:focus {
                background-color: rgba(30, 41, 59, 255);
                border: none;
            }
        """)
        self.input_field.returnPressed.connect(self.send_command)

        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8b5cf6, stop:1 #ec4899);
                color: white;
                border-radius: 20px;
                font-size: 20px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c3aed, stop:1 #db2777); }
            QPushButton:disabled { background: #475569; color: #94A3B8; }
        """)
        self.send_btn.clicked.connect(self.send_command)

        input_box_layout.addWidget(self.input_field)
        input_box_layout.addWidget(self.send_btn)
        
        self.chat_layout.addWidget(self.input_container)

        self.chat_frame.hide()
        self.main_layout.addWidget(self.bubble_container, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(self.chat_frame)
        screen = QApplication.primaryScreen().availableGeometry()
        b_w, b_h = 110, 110
        self.move(screen.width() - b_w - 20, screen.height() - b_h - 20)
        self.resize(b_w, b_h)

        # Welcome message
        self.add_message("Hello! I am SAGE. How can I assist you today?", is_user=False)

    def ensure_in_bounds(self):
        screen = QApplication.primaryScreen().availableGeometry()
        curr_rect = self.geometry()
        new_x = max(screen.left() + 10, min(curr_rect.x(), screen.right() - curr_rect.width() - 10))
        new_y = max(screen.top() + 10, min(curr_rect.y(), screen.bottom() - curr_rect.height() - 10))
        if new_x != curr_rect.x() or new_y != curr_rect.y():
            self.move(new_x, new_y)

    def on_dragged(self, delta):
        new_x = self.x() + delta.x()
        new_y = self.y() + delta.y()
        screen = QApplication.primaryScreen().availableGeometry()
        new_x = max(screen.left() + 10, min(new_x, screen.right() - self.width() - 10))
        new_y = max(screen.top() + 10, min(new_y, screen.bottom() - self.height() - 10))
        self.move(new_x, new_y)

    def on_bubble_clicked(self):
        if self.is_processing:
            self.cancel_processing()
        else:
            self.toggle_mode()

    def toggle_mode(self):
        from PyQt6.QtCore import QRect
        self.is_expanded = not self.is_expanded
        
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(400)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        
        current_rect = self.geometry()
        right = current_rect.x() + current_rect.width()
        bottom = current_rect.y() + current_rect.height()
        
        if self.is_expanded:
            self.chat_frame.show()
            self.bubble_container.hide()
            screen = QApplication.primaryScreen().availableGeometry()
            new_x = max(screen.left() + 10, min(right - 410, screen.right() - 410 - 10))
            new_y = max(screen.top() + 10, min(bottom - 580, screen.bottom() - 580 - 10))
            end_rect = QRect(new_x, new_y, 410, 580)
            self.anim.setStartValue(current_rect)
            self.anim.setEndValue(end_rect)
            QTimer.singleShot(100, lambda: self.input_field.setFocus())
        else:
            self.chat_frame.hide()
            self.bubble_container.show()
            screen = QApplication.primaryScreen().availableGeometry()
            new_x = max(screen.left() + 10, min(right - 110, screen.right() - 110 - 10))
            new_y = max(screen.top() + 10, min(bottom - 110, screen.bottom() - 110 - 10))
            end_rect = QRect(new_x, new_y, 110, 110)
            self.anim.setStartValue(current_rect)
            self.anim.setEndValue(end_rect)
            
        self.anim.start()

    def add_message(self, text, is_user=True):
        bubble = ChatBubble(text, is_user)
        bubble.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=20, color=QColor(0,0,0,50), offset=QPointF(0.0, 5.0)))
        self.scroll_layout.addWidget(bubble)

        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def send_command(self):
        text = self.input_field.text().strip()
        if not text: return

        self.add_message(text, is_user=True)
        self.input_field.clear()
        
        self.worker = AgentWorker(self.agent, text)
        self.worker.result_ready.connect(self.on_result)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.status_update.connect(self.update_status)
        self.worker.processing_started.connect(self.on_processing_started)
        self.worker.processing_finished.connect(self.on_processing_finished)
        self.worker.action_state_changed.connect(self.on_action_state_changed)
        self.worker.hide_ui.connect(self.on_hide_ui_requested)
        self.worker.start()

    def on_processing_started(self):
        self.is_processing = True
        self.send_btn.setEnabled(False)
        self.status_label.show()
        self.status_label.setText("✨ SAGE is executing...")
        
        self.bubble_btn.setText("✖")
        self.bubble_btn.setStyleSheet(self.cancel_bubble_style)
        self.shadow.setColor(QColor(239, 68, 68, 180)) # Red glow
        
        self.floating_status.show()
        self.bubble_container.setFixedSize(200, 110)
        self.adjustSize()
        QTimer.singleShot(50, self.ensure_in_bounds)

    def on_hide_ui_requested(self):
        if self.is_expanded:
            self.toggle_mode()

    def on_action_state_changed(self, active: bool):
        if active:
            self.overlay.show()
        else:
            self.overlay.hide()

    def on_processing_finished(self):
        if not self.is_processing: return # was already cancelled manually
        self.is_processing = False
        self.send_btn.setEnabled(True)
        self.status_label.hide()
        
        # Revert bubble back to Normal
        self.floating_status.hide()
        self.bubble_container.setFixedSize(80, 80)
        self.bubble_btn.setFixedSize(60, 60)
        self.bubble_btn.setText("✨")
        self.bubble_btn.setStyleSheet(self.default_bubble_style)
        self.shadow.setColor(QColor(139, 92, 246, 180)) # Purple glow
        self.adjustSize()
        QTimer.singleShot(50, self.ensure_in_bounds)
        
        self.overlay.hide()
        
        # Optionally expand again (or just leave notification)
        if not self.is_expanded:
            self.toggle_mode()

    def cancel_processing(self):
        """Force stops the thread and aborts the agent command."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait() # Safely clear it
            self.add_message("⚠️ Process cancelled by user.", is_user=False)
        
        self.on_processing_finished()

    def update_status(self, text):
        self.status_label.setText(text)
        if self.is_processing and not self.is_expanded:
            clean = text.replace("⚙️ Using: ", "").replace("...", "")
            short_str = clean[:18] + ".." if len(clean) > 18 else clean
            self.floating_status.setText(short_str)

    def on_result(self, result):
        self.add_message(result, is_user=False)

    def on_error(self, err):
        self.add_message(f"⚠️ Error: {err}", is_user=False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def close_app(self):
        self.agent.stop()
        if self.worker: self.worker.terminate()
        self.overlay.close()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Inter", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)
    
    window = FloatingBubble("YOUR_GROQ_API_KEY")
    window.show()
    sys.exit(app.exec())
