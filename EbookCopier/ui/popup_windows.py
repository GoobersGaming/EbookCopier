import time
import winsound
import pyautogui
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from ui.styles import configure_styles
from utils import browser
import logging
logger = logging.getLogger(__name__)

"""Popup windws for the main GUI App"""
# TODO:
# Some of the window ui can be combined like Dupe/Blank/threebuttoonclass can be one class. Perhaps messagebox/yesno
# Look For A True Way To Not Steal Window Focus With Popups.


def check_enviroment():
    """Ensures Edge Is Active, and Fullscreen, and will move mouse out of the way"""
    try:
        response = None
        if not browser.is_edge_window_active_and_focused():
            browser.activate_edge_window()
            response = True
            logging.info("Activating Microsoft Edge")
            time.sleep(.5)
        if not browser.is_edge_fullscreen():
            browser.enter_fullscreen_if_needed()
            response = True
            logging.info("Microsoft Edge Entering Full Screen")
        # Multimonitor mouse check
        cur_x, cur_y = pyautogui.position()
        screen_width, screen_height = pyautogui.size()
        # Target bottom middle of screen
        target_x = screen_width // 2
        target_y = screen_height
        if not (abs(cur_x - target_x) < 5 and abs(cur_y - target_y) < 5):
            pyautogui.moveTo(target_x, target_y)
            logging.info("Moving mouse")
            time.sleep(0.5)

    except pyautogui.FailSafeException:
        logging.warning("Fail-safe trioggered")
    except Exception as e:
        raise RuntimeError(f"Enviroment check failed: {str(e)}")
    logging.info("Enviroment check complete.")
    return response  # Return True if browser was manipulated


def create_root(win_attr="default", resize=(False, False), theme="clam", toplevel=True):
    """ Creates Root Window With Attributes And Style.
    Args:
        win_attr (str | list[tuple[str, bool]]):
            - `"default"`: Enables `-toolwindow` and `-topmost=True`.
            - `[(attr, value), ...]`: Sets custom attributes.
            Example: `[("-alpha", 0.9), ("-disabled", False)]`.
        resize (tuple[bool, bool], optional): Sets windows resize options for X and Y
        theme (str, optional): Sets window theme.
        toplevel (bool, optional): Sets window to tk.Toplevel
    """
    if toplevel:
        root = tk.Toplevel()
    else:
        root = tk.Tk()
    root.resizable(resize[0], resize[1])
    if win_attr == "default":
        root.attributes("-toolwindow", True)
        root.attributes("-topmost", True)
    elif isinstance(win_attr, list):
        for item in win_attr:
            try:
                if len(item) == 2:
                    root.attributes(item[0], item[1])
                else:
                    root.attributes(item[0], True)
            except Exception as e:
                logging.error(f"Failed to set attribute {item}: {str(e)}")

    style = ttk.Style(root)
    style.theme_use(theme)
    configure_styles(root)
    return root


def set_root_geometry(root):
    """Centers Customs Messageboxes"""
    root.update_idletasks()
    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"+{x}+{y}")


def set_response(root, response_var, value):
    """Handles Popup Reponses"""
    if response_var is not None:
        response_var[0] = value
    root.grab_release()
    root.withdraw()
    root.after(50, root.destroy)


def custom_ask(title, message, buttons, help_items=None):
    """Show dialog with custom buttons and optional help

    Args:
        title (str): Window Title
        message (str): Main window text
        buttons (dict{str:, bool | str}]): Sets Button Name, And Buttons Return Value
        help_items (list): List of help items for NavigationPopup (optional)
    Returns:
        response
    """
    winsound.MessageBeep(winsound.MB_ICONHAND)
    if not tk._default_root:
        root = tk.Tk()
        root.withdraw()
    dialog = ThreeButtonDialog(tk._default_root, title, message, buttons, help_items)
    return dialog.result


def message_box(title, message, button="OK", btn_focus=False, ebook_running=False, delay=1.0):
    """Custom Message Box With One Button
    Args:
        title (str): Window Title
        message (str): Main window text
        buttons (str): Sets Button Text
        btn_focus (bool): set button focus
    Returns:
        response
    """
    root = create_root()
    root.title(title)

    response = [False]

    container = ttk.Frame(root, style="Container.TFrame")
    container.pack(padx=10, pady=10)

    lbl_message = ttk.Label(
        container,
        text=message,
        style="Hel.TLabel",
        wraplength=400
    )
    lbl_message.pack(padx=20, pady=10)

    button_frame = ttk.Frame(container, style="Container.TFrame")
    button_frame.pack(padx=0, pady=(0, 10))

    btn_true = ttk.Button(button_frame, text=button, style="TButton", command=lambda: set_response(root, response, True))
    btn_true.pack(side=tk.LEFT, padx=10)

    # Make it modal(blocks input to other windows)
    root.grab_set()

    # Center Dialog
    set_root_geometry(root)

    if btn_focus is True:
        btn_true.focus_set()
    elif btn_focus is False:
        btn_true.focus_set()
    root.wait_window()
    # Ensures monitor enviroment is set correctly after closing.
    if ebook_running is True:
        check_enviroment(delay)

    # logs.LOOGGER.info(f"Messagebox: {title}, response: {response[0]}")
    return response[0]


def ask_yes_no(title, message, true_button="Yes", false_button="No", btn_focus=None, ebook_running=True, delay=1.0):
    """Show dialog with true | false response

    Args:
        title (str): Window Title
        message (str): Main window text
        true_button (str, optional): Set button text for True response
        false_button (str, optional): Set button text for False response
        btn_focus (str, optional): Set focus on which button
            - if equals `true_button` value, focuses the true button
            - if equals `false_button` value, focuses the false button
    Returns:
        response (bool) : Returns bool of button clicked
    """
    root = create_root()
    if not ebook_running:
        if hasattr(root, "master") and root.master.winfo_exists():
            root.transient(root.master)

    root.title(title)

    response = [False]

    container = ttk.Frame(root, style="Container.TFrame")
    container.pack(padx=10, pady=10)

    lbl_message = ttk.Label(
        container,
        text=message,
        style="Hel.TLabel",
        wraplength=400
    )
    lbl_message.pack(padx=20, pady=10)

    button_frame = ttk.Frame(container, style="Container.TFrame")
    button_frame.pack(padx=0, pady=(0, 10))

    btn_true = ttk.Button(button_frame, text=true_button, style="TButton", command=lambda: set_response(root, response, True))
    btn_true.pack(side=tk.LEFT, padx=10)

    btn_false = ttk.Button(button_frame, text=false_button, style="TButton", command=lambda: set_response(root, response, False))
    btn_false.pack(side=tk.LEFT, padx=10)

    # Make it modal(blocks input to other windows)
    root.grab_set()

    # Center Dialog
    set_root_geometry(root)

    if btn_focus == true_button:
        btn_true.focus_set()
    elif btn_focus == false_button:
        btn_false.focus_set()
    root.wait_window()
    # Ensures monitor enviroment is set correctly after closing.
    if ebook_running is True:
        check_enviroment()

    root.grab_release()
    # logs.LOOGGER.info(f"Askyn: {title}, response: {response[0]}")
    return response[0]


class NavigationPopup:
    def __init__(self, root, items):
        self.root = root
        self.items = items
        self.current_index = 0

        # Create popup window
        self.popup = tk.Toplevel(root)
        self.popup.title("Navigation Popup")
        self.popup.attributes("-topmost", True)
        self.popup.geometry("700x500")
        self.popup.resizable(False, False)

        style = ttk.Style(self.popup)
        style.theme_use("clam")
        configure_styles(self.popup)

        # Create main container
        self.container = ttk.Frame(self.popup, style="Dupe.TFrame")
        self.container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Label
        self.label = ttk.Label(self.container, text="", style="Hel.TLabel", wraplength=500)
        self.label.pack(pady=10)

        # Image display (will be empty if no image)
        self.image_label = ttk.Label(self.container, style="Hel.TLabel")
        self.image_label.pack(pady=10)

        # Button frame
        self.button_frame = ttk.Frame(self.container, style="Dupe.TFrame")
        self.button_frame.pack(pady=20)

        # Buttons
        self.prev_button = ttk.Button(self.button_frame, text="Previous", command=self.show_previous)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = ttk.Button(self.button_frame, text="Next", command=self.show_next)
        self.next_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(self.button_frame, text="Cancel", command=self.close_popup)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Load first item
        self.show_item()

    def show_item(self):
        item = self.items[self.current_index]

        # Update label
        self.label.config(text=item["label"])

        # Display image if provided, otherwise clear the image area
        if "image_path" in item and item["image_path"] is not None:
            try:
                image = Image.open(item["image_path"])
                image = image.resize((300, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.image_label.config(image=photo)
                self.image_label.image = photo  # Keep reference
            except Exception as e:
                logging.warning(f"Error loading image: {e}")
                self.image_label.config(image="")
        else:
            pass
            self.image_label.config(image="")

        # Update button states
        self.prev_button["state"] = tk.NORMAL if self.current_index > 0 else tk.DISABLED

        # Check if last item
        if self.current_index == len(self.items) - 1:
            self.next_button.config(text="Done", command=self.close_popup)
            self.cancel_button.pack_forget()
        else:
            self.next_button.config(text="Next", command=self.show_next)
            self.cancel_button.pack(side=tk.LEFT, padx=5)

    def show_next(self):
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self.show_item()

    def show_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_item()

    def close_popup(self):
        self.popup.destroy()


class ThreeButtonDialog:
    def __init__(self, parent, title, message, buttons, help_items=None):
        self.parent = parent
        self.result = None
        self.help_items = help_items  # Store help items for later use

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.resizable(False, False)

        self.dialog.attributes("-toolwindow", True)  # Removes minimize/maximize
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)

        # Make the dialog stay on top
        self.dialog.attributes("-topmost", True)
        self.dialog.grab_set()  # Make it modal

        # Add Style
        style = ttk.Style(self.dialog)
        style.theme_use("clam")
        configure_styles(self.dialog)

        # Message
        lbl_message = ttk.Label(self.dialog, text=message, style="Hel.TLabel")
        lbl_message.pack(padx=20, pady=10)

        # Button frame
        btn_frame = ttk.Frame(self.dialog, style="Dupe.TFrame")
        btn_frame.pack(pady=10)

        # Create dynamic buttons
        for i, (text, return_value) in enumerate(buttons.items()):
            if text == "Help" and self.help_items:
                # Special handling for Help button
                ttk.Button(
                    btn_frame,
                    text=text,
                    style="TButton",
                    command=self.show_help_popup
                ).grid(row=0, column=i, padx=5)
            else:
                ttk.Button(
                    btn_frame,
                    text=text,
                    style="TButton",
                    command=lambda v=return_value: self.set_result(v)
                ).grid(row=0, column=i, padx=5)

        self.center_dialog()
        self.parent.wait_window(self.dialog)

    def on_close(self):
        self.result = False
        self.dialog.destroy()

    def show_help_popup(self):
        """Show the help popup without closing the main dialog"""
        # Temporarily release grab to allow interaction with help popup
        self.dialog.grab_release()

        # Create help popup
        help_popup = NavigationPopup(self.dialog, self.help_items)

        # Wait for help popup to close
        self.dialog.wait_window(help_popup.popup)

        # Restore grab to main dialog
        self.dialog.grab_set()

    def center_dialog(self):
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def set_result(self, value):
        self.result = value
        self.dialog.destroy()


def ask_user_keep_blank(blank_image, ebook_running=False, delay=1.0):
    """
    Display a window showing two images side by side with options to Keep or Skip.

    Args:
        blank_image (PIL.Image): Image to display

    Returns:
        response (bool): True if Keep is clicked, False if Skip is clicked
    """
    winsound.MessageBeep(winsound.MB_ICONHAND)
    root = create_root(win_attr=[("-topmost", True)])
    root.title("Blank Page Detected")

    # This will store the user"s choice
    response = [None]

    # Get screen dimensions for scaling
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    max_width = (screen_width - 100) // 2  # Half screen width with some padding
    max_height = screen_height - 350  # Adjust for additional label and buttons

    def scale_image(image):
        """Scale an image to fit within the max dimensions while maintaining aspect ratio"""
        if image is None:
            # Create a blank image if None is provided
            image = Image.new("RGB", (max_width, 100), color="gray")
        image.thumbnail((max_width, max_height), Image.LANCZOS)
        return ImageTk.PhotoImage(image)

    # Main container frame
    main_frame = ttk.Frame(root, style="Dupe.TFrame", padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Add the warning label at the top
    warning_label = ttk.Label(
        main_frame,
        text="BLANK PAGE DETECTED\n\nDo You Wish To Keep Current Image?",
        style="Title.TLabel",
        justify="center",
        padding=(0, 0, 0, 15),
    )
    warning_label.pack(pady=(0, 10))

    # Image comparison frame
    compare_frame = ttk.Frame(main_frame, style="Dupe.TFrame")
    compare_frame.pack(fill=tk.BOTH, expand=True)

    # Scale images
    prev_img_tk = scale_image(blank_image.copy())

    # Blank Image
    blank_frame = ttk.LabelFrame(compare_frame,
                                 style="Dupe.TLabelframe",
                                 padding="8")
    blank_frame.grid(row=0, column=0, padx=10, pady=5, sticky=tk.NSEW)
    prev_label = ttk.Label(blank_frame, image=prev_img_tk, background="#4a6baf", relief="flat", borderwidth=1)
    prev_label.image = prev_img_tk  # Keep a reference
    prev_label.pack()

    # Configure grid weights for resizing
    compare_frame.columnconfigure(0, weight=1)
    compare_frame.columnconfigure(1, weight=1)
    compare_frame.rowconfigure(0, weight=1)

    # Button frame
    button_frame = ttk.Frame(main_frame, style="Dupe.TFrame")
    button_frame.pack(pady=(15, 5))

    # Keep button (returns True)
    keep_button = ttk.Button(
        button_frame,
        text="Keep Current",
        command=lambda: set_response(root, response, True),
        style="TButton",
        width=12
    )
    keep_button.pack(side=tk.LEFT, padx=8)

    # Skip button (returns False)
    skip_button = ttk.Button(
        button_frame,
        text="Skip Current",
        command=lambda: set_response(root, response, False),
        style="TButton",
        width=12
    )
    skip_button.pack(side=tk.LEFT, padx=8)

    again_button = ttk.Button(
        button_frame,
        text="Try Again",
        command=lambda: set_response(root, response, "again"),
        style="TButton",
        width=12
    )
    again_button.pack(side=tk.LEFT, padx=8)

    # Center the window
    set_root_geometry(root)

    # Make the window modal
    root.grab_set()
    keep_button.focus_set()
    root.wait_window()
    # Ensures monitor enviroment is set correctly after closing.
    if ebook_running is True:
        check_enviroment()
    return response[0]


def ask_user_keep_dupe(prev_image, curr_image, ebook_running=True, delay=1.0):
    """
    Display a window showing two images side by side with options to Keep or Skip.

    Args:
        prev_image (PIL.Image): Shows last image saved
        curr_image (PIL.Image): Shows current image

    Returns:
        response (bool | str): returns value of button pressed True for Keep, False for Skip, "End" for End buttons.
    """

    winsound.MessageBeep(winsound.MB_ICONHAND)
    root = create_root(win_attr=[("-topmost", True)])
    root.title("Duplicate Page Detected")
    # This will store the user"s choice
    response = [None]

    # Get screen dimensions for scaling
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    max_width = (screen_width - 200) // 2  # Half screen width with some padding
    max_height = screen_height - 350  # Adjust for additional label and buttons

    def scale_image(image):
        """Scale an image to fit within the max dimensions while maintaining aspect ratio"""
        if image is None:
            # Create a blank image if None is provided
            image = Image.new("RGB", (max_width, 100), color="gray")
        image.thumbnail((max_width, max_height), Image.LANCZOS)
        return ImageTk.PhotoImage(image)

    # Main container frame
    main_frame = ttk.Frame(root, style="Dupe.TFrame", padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Add the warning label at the top
    warning_label = ttk.Label(
        main_frame,
        text="DUPLCIATE PAGE DETECTED\n\nKeep current image or skip?",
        style="Title.TLabel",
        justify="center",
        padding=(0, 0, 0, 15)
    )
    warning_label.pack(pady=(0, 10))

    # Image comparison frame
    compare_frame = ttk.Frame(main_frame, style="Dupe.TFrame")
    compare_frame.pack(fill=tk.BOTH, expand=True)

    # Scale images
    prev_img_tk = scale_image(prev_image.copy())
    curr_img_tk = scale_image(curr_image.copy())

    # Previous Image
    prev_frame = ttk.LabelFrame(
        compare_frame,
        text="Previous Image ",
        style="Dupe.TLabelframe" ,
        padding="8")
    prev_frame.grid(row=0, column=0, padx=10, pady=5, sticky=tk.NSEW)
    prev_label = ttk.Label(prev_frame, image=prev_img_tk, background="#4a6baf", relief="flat", borderwidth=1)
    prev_label.image = prev_img_tk  # Keep a reference
    prev_label.pack()

    # Current Image
    curr_frame = ttk.LabelFrame(compare_frame,
                                text="Current Image ",
                                style="Dupe.TLabelframe",
                                padding="8")
    curr_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
    curr_label = ttk.Label(curr_frame, image=curr_img_tk, background="#4a6baf", relief="flat", borderwidth=1)
    curr_label.image = curr_img_tk  # Keep a reference
    curr_label.pack()

    # Configure grid weights for resizing
    compare_frame.columnconfigure(0, weight=1)
    compare_frame.columnconfigure(1, weight=1)
    compare_frame.rowconfigure(0, weight=1)

    # Button frame
    button_frame = ttk.Frame(main_frame, style="Dupe.TFrame")
    button_frame.pack(pady=(15, 5))

    # Keep button (returns True)
    keep_button = ttk.Button(
        button_frame,
        text="Keep Current",
        command=lambda: set_response(root, response, True),
        style="TButton",
        width=12
    )
    keep_button.pack(side=tk.LEFT, padx=8)

    # Skip button (returns False)
    skip_button = ttk.Button(
        button_frame,
        text="Skip Current",
        command=lambda: set_response(root, response, False),
        style="TButton",
        width=12
    )
    skip_button.pack(side=tk.LEFT, padx=8)

    eob_button = ttk.Button(
        button_frame,
        text="End Of Book",
        command=lambda: set_response(root, response, "End"),
        style="TButton",
        width=12
    )
    eob_button.pack(side=tk.LEFT, padx=8)
    # Center the window
    set_root_geometry(root)

    # Make the window modal
    root.grab_set()

    keep_button.focus_set()
    root.wait_window()
    # Ensures monitor enviroment is set correctly after closing.
    if ebook_running is True:
        check_enviroment()
    return response[0]


def countdown(timer_label, count, countdown_window):
    if count >= 0:
        # Update the label text with the countdown
        timer_label.config(text=str(count))
        # Call the countdown function again after 1 second
        timer_label.after(1000, countdown, timer_label, count - 1, countdown_window)
    else:
        # Once the countdown ends, display "Time"s up!" and destroy the window
        # timer_label.config(text="Time"s up!")
        # countdown_window.destroy

        # main_window.destroy()
        countdown_window.destroy()
        countdown_window.quit()
        # countdown_window.after(1000, countdown_window.destroy)  # Close the window after 1 second


def show_countdown_popup(countdown_length):
    # Create a new popup window (Toplevel window)
    countdown_window = tk.Toplevel()
    countdown_window.attributes("-transparentcolor", "gray15")
    countdown_window.overrideredirect(True)

    # Make the window invisible except for the timer
    countdown_window.geometry("400x200")  # Adjust size as needed

    # Get the screen width and height for centering the popup
    screen_width = countdown_window.winfo_screenwidth()
    screen_height = countdown_window.winfo_screenheight()

    # Calculate the position to center the window
    x = (screen_width // 2) - 200  # Half of window width (400px) subtracted from screen width
    y = (screen_height // 2) - 100  # Half of window height (200px) subtracted from screen height

    # Position the popup window at the calculated coordinates
    countdown_window.geometry(f"400x200+{x}+{y}")

    # Make the popup window invisible except for the timer
    countdown_window.configure(bg="gray15")  # Background color (will be invisible)
    countdown_window.overrideredirect(True)  # Remove window decorations (e.g., title bar, borders)

    # Create a label for the countdown timer
    timer_label = tk.Label(countdown_window, font=("Helvetica", 200), fg="white", bg="gray15")  # Large font for the timer
    timer_label.pack(expand=True)

    # Start the countdown from 10 seconds
    countdown(timer_label, countdown_length, countdown_window)

    # Run the popup window"s event loop
    countdown_window.mainloop()


def disable_window(window):
    """Disable all child widgets of a window"""
    disabled_widgets = []

    def recursive_disable(widget):
        for child in widget.winfo_children():
            # Only process widgets that support state
            if "state" in child.keys():
                try:
                    # Store both string and numeric state
                    current_state = child.cget("state")
                    disabled_widgets.append((child, current_state))
                    child.configure(state="disabled")
                except Exception:
                    continue
            recursive_disable(child)

    recursive_disable(window)
    return disabled_widgets


def restore_window(disabled_widgets):
    """Restore widgets to their original state"""
    for widget, original_state in disabled_widgets:
        try:
            # Convert state to string if needed
            if isinstance(original_state, (int, float)):
                state_map = {0: "normal", 1: "active", 8: "disabled"}
                state_str = state_map.get(int(original_state), "normal")
            else:
                state_str = str(original_state)

            # Skip if widget doesn"t support state configuration
            if "state" in widget.keys():
                widget.configure(state=state_str)
        except Exception as e:
            logging.warning(f"Error restoring widget state: {e}")
            continue
