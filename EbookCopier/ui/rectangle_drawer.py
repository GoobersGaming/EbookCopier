import tkinter as tk
import win32api
import win32con
import ctypes
import keyboard
import logging
logger = logging.getLogger(__name__)
"""Rectangle Drawer, For User To Draw Capture Area For Screenshot"""
# TODO: Add a coords check, to accept bad coordinates.
# Remove windows api/ctypes. The window still steals focus.
# Adjust window style.Brighten up/change color of the label, brighten up and thicken outline.


class RectangleEditor:
    def __init__(self, parent, coords=None, monitor_num=1):
        self.root = tk.Toplevel(parent)

        # Get monitor info first
        self.monitor_num = monitor_num
        self.monitor_info = self.get_monitor_info(monitor_num)

        # Set window to cover only the specified monitor
        self.setup_window_for_monitor()
        self.root.attributes("-alpha", 0.4)
        self.root.attributes("-topmost", True)
        # self.root.attributes("-disabled", True)
        # self.root.attributes("-transparentcolor", "black")  # Make clicks pass through
        self.root.overrideredirect(True)
        self.root.configure(bg="black")

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_TRANSPARENT = 0x00000020
            current_style = ctypes.windll.user32.GetWindowLongA(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongA(
                hwnd,
                GWL_EXSTYLE,
                current_style | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT)
        except Exception as e:
            logging.info(f"Couldnt set rectangle editor window attributes {str(e)}")

        # Create instruction message (positioned relative to this monitor)
        self.create_message_box()

        # Rectangle variables
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.rect = None
        self.rect_fill = None
        self.drawing = False
        self.resizing = False
        self.dragging = False
        self.selected_side = None
        self.rectangle_coords = None
        self.current_cursor = ""

        # If coordinates were provided, draw initial rectangle
        if coords:

            if monitor_num > 1:
                _, x1, y1 = self.absolute_to_monitor_coords_win(coords["x1"], coords["y1"])
                _, x2, y2 = self.absolute_to_monitor_coords_win(coords["x2"], coords["y2"])
                self.draw_rectangle(x1, y1, x2, y2)
                self.rectangle_coords = (x1, y1, x2, y2)
            else:
                self.draw_rectangle(coords["x1"], coords["y1"], coords["x2"], coords["y2"])
                self.rectangle_coords = coords

        # Bind Global keyboard events
        keyboard.add_hotkey("enter", self._on_enter)
        keyboard.add_hotkey("esc", self._on_escape)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_click_press)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_click_release)
        self.canvas.bind("<Motion>", self.on_hover)

    def _on_enter(self):
        self.done()

    def _on_escape(self):
        self.cancel()

    def absolute_to_monitor_coords_win(self, abs_x, abs_y):
        monitors = win32api.EnumDisplayMonitors()
        for monitor in monitors:
            monitor_info = win32api.GetMonitorInfo(monitor[0])
            monitor_rect = monitor_info["Monitor"]
            if (monitor_rect[0] <= abs_x < monitor_rect[2] and monitor_rect[1] <= abs_y < monitor_rect[3]):
                rel_x = abs_x - monitor_rect[0]
                rel_y = abs_y - monitor_rect[1]
                return monitor_info, rel_x, rel_y
        return None, None, None

    def get_monitor_info(self, monitor_num):
        """Get information about the specified monitor (1-based index)"""
        monitors = win32api.EnumDisplayMonitors()
        if monitor_num < 1 or monitor_num > len(monitors):
            raise ValueError(f"Invalid monitor number {monitor_num}. Only {len(monitors)} monitors available.")

        monitor = monitors[monitor_num - 1]
        monitor_info = win32api.GetMonitorInfo(monitor[0])

        return {
            "monitor": monitor_num,
            "handle": monitor[0],
            "work_area": monitor_info["Work"],  # Excludes taskbar
            "monitor_area": monitor_info["Monitor"],  # Full monitor area
            "is_primary": bool(monitor_info.get("Flags", 0) & win32con.MONITORINFOF_PRIMARY)
        }

    def setup_window_for_monitor(self):
        """Configure the window to cover only the specified monitor"""
        monitor = self.monitor_info["monitor_area"]

        # Calculate geometry
        width = monitor[2] - monitor[0]
        height = monitor[3] - monitor[1]
        x_offset = monitor[0]
        y_offset = monitor[1]

        # Remove window decorations
        self.root.overrideredirect(True)

        # Set geometry - critical for multi-monitor support
        self.root.geometry(f"{width}x{height}+{x_offset}+{y_offset}")

        # Store offsets for coordinate conversion
        self.monitor_offset_x = x_offset
        self.monitor_offset_y = y_offset

    def get_absolute_coords(self, x, y):
        """Convert monitor-relative coordinates to absolute screen coordinates"""
        return x + self.monitor_offset_x, y + self.monitor_offset_y

    def get_relative_coords(self, x, y):
        """Convert absolute screen coordinates to monitor-relative coordinates"""
        return x - self.monitor_offset_x, y - self.monitor_offset_y

    def create_message_box(self):
        """Create instruction message in top-left corner"""
        """Position message box relative to the target monitor"""
        self.msg_box = tk.Toplevel(self.root)
        self.msg_box.attributes("-topmost", True)
        self.msg_box.overrideredirect(True)
        self.msg_box.configure(bg="#333333", bd=2, relief=tk.RAISED)

        # Position relative to current monitor
        msg_width = 300
        msg_height = 100
        msg_x = 20  # Relative to monitor
        msg_y = 20  # Relative to monitor

        self.msg_box.geometry(
            f"{msg_width}x{msg_height}+{msg_x + self.monitor_offset_x}+{msg_y + self.monitor_offset_y}"
        )

        # Message text
        message = "Draw/Resize Capture Screen If Needed \n"
        message += "Drag edges to resize | Drag inside to move\n"
        message += "Enter: Confirm  Esc: Cancel"

        tk.Label(
            self.msg_box,
            text=message,
            bg="#333333", fg="white",
            padx=15, pady=10,
            font=("Helvetica", 12),
            justify=tk.LEFT
        ).pack(expand=True)

    def on_hover(self, event):
        """Change cursor when hovering over rectangle edges"""
        if not self.rect:
            self.reset_cursor()
            return

        x, y = event.x, event.y
        side = self.get_selected_side(x, y)

        if side == "top" or side == "bottom":
            self.set_cursor("sb_v_double_arrow")
        elif side == "left" or side == "right":
            self.set_cursor("sb_h_double_arrow")
        elif self.is_inside_rect(x, y):
            self.set_cursor("fleur")
        else:
            self.reset_cursor()

    def set_cursor(self, cursor_name):
        """Set the cursor if it"s not already set"""
        if self.current_cursor != cursor_name:
            self.canvas.config(cursor=cursor_name)
            self.current_cursor = cursor_name

    def reset_cursor(self):
        """Reset to default cursor"""
        if self.current_cursor != "":
            self.canvas.config(cursor="")
            self.current_cursor = ""

    def on_click_press(self, event):
        """Handle mouse button press"""
        x, y = event.x, event.y

        if self.rect:
            self.selected_side = self.get_selected_side(x, y)
            if self.selected_side:
                self.resizing = True
                return
            elif self.is_inside_rect(x, y):
                self.dragging = True
                self.drag_start_x = x
                self.drag_start_y = y
                return

        self.start_x, self.start_y = x, y
        self.drawing = True
        if self.rect:
            self.canvas.delete(self.rect)
            self.canvas.delete(self.rect_fill)
            self.rect = None
            self.rect_fill = None

    def on_click_release(self, event):
        """Handle mouse button release"""
        self.drawing = False
        self.resizing = False
        self.dragging = False

    def on_move(self, event):
        """Handle mouse movement"""
        x, y = event.x, event.y

        if self.drawing:
            self.draw_rectangle(self.start_x, self.start_y, x, y)
        elif self.resizing:
            coords = self.canvas.coords(self.rect)
            if self.selected_side == "top":
                self.draw_rectangle(coords[0], y, coords[2], coords[3])
            elif self.selected_side == "bottom":
                self.draw_rectangle(coords[0], coords[1], coords[2], y)
            elif self.selected_side == "left":
                self.draw_rectangle(x, coords[1], coords[2], coords[3])
            elif self.selected_side == "right":
                self.draw_rectangle(coords[0], coords[1], x, coords[3])
        elif self.dragging:
            coords = self.canvas.coords(self.rect)
            dx = x - self.drag_start_x
            dy = y - self.drag_start_y
            self.draw_rectangle(
                coords[0] + dx, coords[1] + dy,
                coords[2] + dx, coords[3] + dy
            )
            self.drag_start_x = x
            self.drag_start_y = y

    def draw_rectangle(self, x1, y1, x2, y2):
        """Draw or update the rectangle with highlighted area"""
        # Ensure coordinates are properly ordered
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        if not self.rect:
            # Create the rectangle outline
            self.rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="red", width=2, dash=(5, 5)
            )
            # Create the highlighted fill (non-transparent)
            self.rect_fill = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="", fill="white"
            )
            # Make sure the outline stays on top
            self.canvas.tag_raise(self.rect)
        else:
            # Update both the outline and the fill
            self.canvas.coords(self.rect, x1, y1, x2, y2)
            self.canvas.coords(self.rect_fill, x1, y1, x2, y2)
            self.canvas.tag_raise(self.rect)

        # Store the final coordinates
        self.start_x, self.start_y = x1, y1
        self.end_x, self.end_y = x2, y2

    def get_selected_side(self, x, y):
        """Determine which side of the rectangle is near the cursor"""
        if not self.rect:
            return None

        coords = self.canvas.coords(self.rect)
        margin = 10  # Sensitivity for edge selection

        # Check top and bottom edges
        if abs(y - coords[1]) <= margin and coords[0] <= x <= coords[2]:
            return "top"
        elif abs(y - coords[3]) <= margin and coords[0] <= x <= coords[2]:
            return "bottom"
        # Check left and right edges
        elif abs(x - coords[0]) <= margin and coords[1] <= y <= coords[3]:
            return "left"
        elif abs(x - coords[2]) <= margin and coords[1] <= y <= coords[3]:
            return "right"
        return None

    def is_inside_rect(self, x, y):
        """Check if the point is inside the rectangle"""
        if not self.rect:
            return False
        coords = self.canvas.coords(self.rect)
        return (coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3])

    def done(self, event=None):
        """Confirm the selection and exit"""
        if self.rect:
            coords = self.canvas.coords(self.rect)
            # Convert to absolute screen coordinates
            x1, y1 = self.get_absolute_coords(coords[0], coords[1])
            x2, y2 = self.get_absolute_coords(coords[2], coords[3])

            self.rectangle_coords = {
                "x1": int(x1),
                "y1": int(y1),
                "x2": int(x2),
                "y2": int(y2),
                "monitor": self.monitor_num
            }

        self.root.destroy()
        keyboard.unhook_all()
        return

    def cancel(self, event=None):
        """Cancel the selection and exit"""
        self.rectangle_coords = None
        self.root.destroy()
        keyboard.unhook_all()

    def get_coords(self):
        """Return the rectangle coordinates"""
        return self.rectangle_coords
