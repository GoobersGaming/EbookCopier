import win32gui
import win32con
import win32api
import time
import keyboard
from utils import logs
"""Add Logging"""

def is_edge_active():
    """Check if any Edge window is active."""
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    # More robust check that works with Edge's various title formats
    return "Microsoft Edge" in title or "Edge" in title

def activate_edge():
    """Activate Microsoft Edge window."""
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Microsoft Edge" in title or "Edge" in title:
                hwnds.append(hwnd)
        return True
    
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    
    if not hwnds:
        logs.LOGGER.info("Microsoft Edge is not Running")
        return False

    hwnd = hwnds[0]  # Take the first found Edge window

    if is_edge_active():
        return True

    # Restore if minimized
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.2)  # Shorter delay usually sufficient

    # Try different methods to ensure it comes to foreground
    win32gui.SetForegroundWindow(hwnd)
    win32gui.BringWindowToTop(hwnd)
    # win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
    #                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    # win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
    #                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    return True

def is_edge_fullscreen():
    """Improved check for Edge fullscreen mode."""
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Microsoft Edge" in title or "Edge" in title:
                hwnds.append(hwnd)
        return True
    
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    
    if not hwnds:
        return False

    hwnd = hwnds[0]  # Or handle multiple windows if needed
    
    # Get window style and extended style
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    
    # Check for borderless (F11 fullscreen characteristics)
    is_borderless = not (style & win32con.WS_CAPTION) and not (style & win32con.WS_THICKFRAME)
    
    # Check if window covers the entire monitor
    monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
    monitor_info = win32api.GetMonitorInfo(monitor)
    monitor_rect = monitor_info["Monitor"]
    
    window_rect = win32gui.GetWindowRect(hwnd)
    
    # Account for small differences due to taskbar or rounding
    tolerance = 8  # pixels
    covers_monitor = (
        abs(window_rect[0] - monitor_rect[0]) <= tolerance and
        abs(window_rect[1] - monitor_rect[1]) <= tolerance and
        abs(window_rect[2] - monitor_rect[2]) <= tolerance and
        abs(window_rect[3] - monitor_rect[3]) <= tolerance
    )
    
    return is_borderless and covers_monitor

def enter_fullscreen_if_needed():
    """More robust fullscreen activation."""
    if is_edge_fullscreen():
        return True
    
    # Ensure Edge is active first
    activate_edge()  # Use your existing activation function
    time.sleep(0.2)
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts and not is_edge_fullscreen():
        logs.LOGGER.debug(f"Attempt {attempts + 1} to set fullscreen...")
        keyboard.press_and_release("f11")
        #pyautogui.hotkey('f11')
        time.sleep(0.5)  # Increased delay for more reliable state change
        attempts += 1
    
    if is_edge_fullscreen():
        logs.LOGGER.info("Successfully set Edge to fullscreen")
        return True
    
    logs.LOGGER.info(f"Failed to set fullscreen after {max_attempts} attempts.")
    return False

def get_edge_display_number():
    """Returns which display/monitor Edge is currently on (1-based index). Returns None if Edge not found."""
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Microsoft Edge" in title or "Edge" in title:
                hwnds.append(hwnd)
        return True
    
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    
    if not hwnds:
        return None  # Edge not found
    
    hwnd = hwnds[0]  # Take the first found Edge window
    
    # Get the monitor that contains the center of the window
    rect = win32gui.GetWindowRect(hwnd)
    window_center_x = (rect[0] + rect[2]) // 2
    window_center_y = (rect[1] + rect[3]) // 2
    
    monitors = win32api.EnumDisplayMonitors()
    for i, monitor in enumerate(monitors, 1):
        monitor_info = win32api.GetMonitorInfo(monitor[0])
        work_area = monitor_info["Work"]
        
        if (work_area[0] <= window_center_x <= work_area[2] and
            work_area[1] <= window_center_y <= work_area[3]):
            return i  # Returns 1-based monitor number
    
