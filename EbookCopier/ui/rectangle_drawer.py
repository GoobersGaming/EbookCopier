import sys
import logging
from PySide6.QtWidgets import (QApplication, QLabel,
                               QGraphicsOpacityEffect, QDialog, )
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QTimer
from PySide6.QtGui import (QPainter, QColor, QPen, QBrush,
                           QGuiApplication)
import keyboard
from threading import Thread

logger = logging.getLogger(__name__)


class RectangleEditor(QDialog):
    close_requested = Signal(str)

    def __init__(self, parent=None, coords=None, monitor_num=1):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.monitor_num = monitor_num
        self.coords = coords
        self.keyboard_listener_active = True
        self.close_requested.connect(self.handle_key_action)

        # Setup window properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        # Rectangle drawing variables
        self.start_pos = None
        self.end_pos = None
        self.drawing = False
        self.dragging = False
        self.resizing = False
        self.selected_side = None
        self.rectangle = None
        self.drag_offset = QPoint()

        # Setup the monitor
        self.setup_monitor()
        QTimer.singleShot(0, self._apply_non_focus_style)
        # Create instruction label
        self.create_instruction_label()

        # Set initial rectangle if coords provided
        if coords:
            if monitor_num > 1:
                # Convert absolute coords to monitor-relative
                screen = QGuiApplication.screens()[monitor_num - 1]
                screen_geo = screen.geometry()
                x1 = coords["x1"] - screen_geo.x()
                y1 = coords["y1"] - screen_geo.y()
                x2 = coords["x2"] - screen_geo.x()
                y2 = coords["y2"] - screen_geo.y()
                self.rectangle = QRect(QPoint(x1, y1), QPoint(x2, y2))
            else:
                self.rectangle = QRect(
                    QPoint(coords["x1"], coords["y1"]),
                    QPoint(coords["x2"], coords["y2"])
                )

        # Start keyboard listener in a separate thread
        self.start_keyboard_listener()

    def start_keyboard_listener(self):
        """Start the keyboard listener thread"""
        def listener():
            keyboard.add_hotkey('enter', lambda: self.close_requested.emit("confirm"))
            keyboard.add_hotkey('esc', lambda: self.close_requested.emit("cancel"))

        self.keyboard_thread = Thread(target=listener, daemon=True)
        self.keyboard_thread.start()

    def safe_close(self):
        """Thread-safe window closing"""
        self.stop_keyboard_listener()
        if self.coords is None:  # Only set None if ESC was pressed
            self.coords = None
        self.close()

    def handle_key_action(self, action):
        print(f"Key action received: {action}")
        if action == "confirm":
            self.confirm_selection()

        elif action == "cancel":
            self.cancel_selection()

    def stop_keyboard_listener(self):
        """Stop the keyboard listener"""
        if hasattr(self, 'keyboard_thread'):
            keyboard.unhook_all()
            self.keyboard_listener_active = False

    def closeEvent(self, event):
        """Clean up when window is closed"""
        self.stop_keyboard_listener()
        super().closeEvent(event)
        print("Super close event")

    def setup_monitor(self):
        """Set up the window to cover the specified monitor"""
        screens = QGuiApplication.screens()
        if self.monitor_num < 1 or self.monitor_num > len(screens):
            raise ValueError(f"Invalid monitor number {self.monitor_num}. Only {len(screens)} monitors available.")

        screen = screens[self.monitor_num - 1]
        screen_geo = screen.geometry()

        # Store monitor offset
        self.monitor_offset = screen_geo.topLeft()

        # Set window geometry to cover the entire monitor
        self.setGeometry(screen_geo)

    def create_instruction_label(self):
        """Create a semi-transparent instruction label"""
        self.instruction_label = QLabel(self)
        self.instruction_label.setStyleSheet("""
            QLabel {
                background-color: rgba(60, 60, 60, 180);
                color: white;
                padding: 15px;
                border-radius: 5px;
                font-size: 12px;
            }
        """)

        message = "Draw/Resize Capture Screen If Needed\n"
        message += "Drag edges to resize | Drag inside to move\n"
        message += "Enter: Confirm  Esc: Cancel"
        self.instruction_label.setText(message)

        # Add opacity effect
        opacity = QGraphicsOpacityEffect()
        opacity.setOpacity(0.9)
        self.instruction_label.setGraphicsEffect(opacity)

        # Position in top-left corner
        self.instruction_label.move(20, 20)
        self.instruction_label.adjustSize()

    def paintEvent(self, event):
        """Paint the transparent overlay and rectangle"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill the entire window with semi-transparent color
        painter.fillRect(self.rect(), QColor(0, 0, 0, 60))

        # Draw the rectangle if it exists
        if self.rectangle:
            # Draw filled rectangle (semi-transparent white)
            painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.rectangle)

            # Draw outline (bright red)
            pen = QPen(QColor(255, 50, 50, 220))
            pen.setWidth(3)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.rectangle)

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()

            if self.rectangle:
                side = self.get_selected_side(pos)
                if side:
                    self.resizing = True
                    self.selected_side = side
                    return
                elif self.rectangle.contains(pos):
                    self.dragging = True
                    self.drag_offset = pos - self.rectangle.topLeft()
                    return

            # Start drawing a new rectangle
            self.drawing = True
            self.start_pos = pos
            self.end_pos = pos
            self.rectangle = QRect(self.start_pos, self.end_pos)
            self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        pos = event.position().toPoint()

        # Update cursor based on position
        if self.rectangle:
            side = self.get_selected_side(pos)
            if self.resizing and self.selected_side:
                # Resize if resizing action is active
                self.resize_rectangle(pos)
                self.update()
            elif self.dragging:
                # move the rectangle if dragging is active
                new_top_left = pos - self.drag_offset
                self.rectangle.moveTopLeft(new_top_left)
                self.update()
            elif side in ["top", "bottom"]:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif side in ["left", "right"]:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif self.rectangle.contains(pos):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)

        # Handle drawing/resizing/dragging
        if self.drawing:
            self.end_pos = pos
            self.rectangle = QRect(self.start_pos, self.end_pos).normalized()
            self.update()
        elif self.resizing and self.selected_side:
            self.resize_rectangle(pos)
            self.update()
        elif self.dragging:
            new_top_left = pos - self.drag_offset
            self.rectangle.moveTo(new_top_left)
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.resizing = False
            self.dragging = False
            self.selected_side = None

    def resize_rectangle(self, pos):
        """Resize the rectangle based on which side is selected"""
        if not self.rectangle:
            return

        rect = self.rectangle
        if self.selected_side == "top":
            rect.setTop(pos.y())
        elif self.selected_side == "bottom":
            rect.setBottom(pos.y())
        elif self.selected_side == "left":
            rect.setLeft(pos.x())
        elif self.selected_side == "right":
            rect.setRight(pos.x())

        self.rectangle = rect.normalized()

    def get_selected_side(self, pos):
        """Determine which side of the rectangle is near the cursor"""
        if not self.rectangle:
            return None

        # Set a margin for how close the mouse needs to be to the edge to trigger resizing
        margin = 10  # The smaller this value, the stricter the proximity requirement

        # Calculate the distance from the cursor to the edges
        dist_top = abs(pos.y() - self.rectangle.top())
        dist_bottom = abs(pos.y() - self.rectangle.bottom())
        dist_left = abs(pos.x() - self.rectangle.left())
        dist_right = abs(pos.x() - self.rectangle.right())

        # Only consider sides if the cursor is within the margin distance
        if dist_top <= margin:
            return "top"
        elif dist_bottom <= margin:
            return "bottom"
        elif dist_left <= margin:
            return "left"
        elif dist_right <= margin:
            return "right"

        return None

    def confirm_selection(self):
        """Prepare coordinates and request close"""
        if self.rectangle:
            x1 = self.rectangle.left() + self.monitor_offset.x()
            y1 = self.rectangle.top() + self.monitor_offset.y()
            x2 = self.rectangle.right() + self.monitor_offset.x()
            y2 = self.rectangle.bottom() + self.monitor_offset.y()

            self.coords = {
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "monitor": self.monitor_num
            }
        keyboard.clear_all_hotkeys()

        self.accept()
        print("Ive accepted")

    def cancel_selection(self):
        """Cancel selection and request close"""
        self.coords = None
        keyboard.clear_all_hotkeys()

        self.reject()

    def get_coords(self):
        """Return the selected coordinates"""
        return self.coords

    def _apply_non_focus_style(self):
        """Prevent window activation while allowing mouse/keyboard events."""
        if not sys.platform == "win32":
            return  # Windows-only feature

        try:
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_TOPMOST = 0x00000008
            # WS_EX_TRANSPARENT = 0x00000020  # Allows mouse events to pass through

            hwnd = int(self.winId())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= WS_EX_NOACTIVATE | WS_EX_TOPMOST
            # style |= WS_EX_NOACTIVATE | WS_EX_TOPMOST | WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

            # Ensure window stays interactive
            ctypes.windll.user32.SetWindowPos(
                hwnd, -1, 0, 0, 0, 0,
                0x0001 | 0x0002 | 0x0020  # SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
            )
        except Exception as e:
            print(f"Could not set window style: {e}")


if __name__ == "__main__":
    import time
    time.sleep(15)
    app = QApplication(sys.argv)

    editor = RectangleEditor(monitor_num=1)
    result = editor.exec()  # blocks until dialog is closed

    if result == QDialog.DialogCode.Accepted:
        print("Selected coordinates:", editor.get_coords())
    else:
        print("Selection cancelled.")
