import logging
import tkinter as tk
from tkinter import ttk, filedialog
from ui.styles import configure_styles
from utils.logs import setup_logging
from settings.config import Book
logger = logging.getLogger(__name__)

"""TODO:
Recolor ToolTip"""


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip, text=self.text,
                         background="#ffffe0", relief="solid",
                         borderwidth=1, padx=5, pady=5,
                         font=("Segoe UI", 9))
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def remove(self):
        self.active = False
        self.hide_tooltip()
        self.widget.unbind("<Enter>")
        self.widget.unbind("<Leave>")


class BookCopierUI:
    def __init__(self, settings, start_command=None):
        self.settings = settings
        self._setup_logger()
        self.window = tk.Tk()
        configure_styles(self.window)
        # self._setup_styles()  # Added style configuration
        self._setup_main_window()
        self._create_widgets()
        self.start_command = start_command
        self.site_var.trace_add("write", self._handle_site_change)

    def _setup_main_window(self):
        self.window.title("Book Copier")
        self.window.resizable(False, False)

        # Center window
        window_width = 450  # Slightly wider for better spacing
        window_height = 260  # Taller for better spacing
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        # self.window.eval('tk::PlaceWindow . center')
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.window.grid_rowconfigure(0, weight=0)
        self.window.grid_columnconfigure(0, weight=0)
        self.window.grid_rowconfigure(0, weight=1)  # Center vertically
        self.window.grid_rowconfigure(1, weight=1)  # Bottom space
        self.window.grid_columnconfigure(0, weight=1)  # Center horizontally
        self.window.grid_columnconfigure(1, weight=1)  #

    def _create_widgets(self):
        vcmd = (self.window.register(self._validate_int_input), "%P")
        # Create a frame for better organization
        main_frame = ttk.Frame(self.window, padding="10 10 10 10")
        main_frame.grid(row=1, column=1, sticky="")  # Placed in center cell

        # Row 0: Site Selector
        ttk.Label(main_frame, text="Select Site:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.site_var = tk.StringVar()
        self.site_selector = ttk.Combobox(main_frame,
                                          justify="center",
                                          textvariable=self.site_var,
                                          values=["", "Libby", "Hoopla"],
                                          state="readonly", style="TCombobox")
        self.site_selector.grid(row=0, column=1, columnspan=4, padx=5, pady=5, sticky=tk.EW)
        self.site_selector.current(0)

        # Row 1: Page View Selector
        ttk.Label(main_frame, text="Page View:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.page_view = tk.StringVar()
        self.page_view_selector = ttk.Combobox(main_frame,
                                               justify="center",
                                               textvariable=self.page_view,
                                               values=["One Page", "Two Pages"],
                                               state="readonly", style="TCombobox")
        self.page_view_selector.grid(row=1, column=1, columnspan=4, padx=5, pady=5, sticky=tk.EW)
        self.page_view_selector.current(0)

        # Row 2: Page Count and Timer
        ttk.Label(main_frame, text="Page Count:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.page_var = tk.StringVar()
        self.page_count = ttk.Entry(main_frame, validate="key", validatecommand=vcmd, width=8, textvariable=self.page_var)
        self.page_count.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(main_frame, text="Timer (sec):").grid(row=2, column=2, padx=5, pady=5, sticky=tk.E)
        self.timer_var = tk.StringVar(value="5")
        self.timer_entry = ttk.Entry(main_frame, validate="key", validatecommand=vcmd, width=8, textvariable=self.timer_var)
        self.timer_entry.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)
        self.tooltip_timer = ToolTip(self.timer_entry, "How long to wait for a page to load before taking a screenshot.")

        # Row 3: File Selection
        ttk.Label(main_frame, text="Save PDF As:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.path_label = ttk.Entry(main_frame, width=35, state="readonly")
        self.path_label.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)

        browse_btn = ttk.Button(main_frame, text="...", width=3, command=self._ask_user_save_location)
        browse_btn.grid(row=3, column=4, padx=5, pady=5, sticky=tk.W)

        # Row 4: Start Button
        start_btn = ttk.Button(main_frame,
                               text="Start Processing",
                               command=lambda: self.start_command(self.get_book_params()))
        start_btn.grid(row=4, column=0, columnspan=5, pady=10, sticky=tk.EW)

        # Configure grid weights for resizing
        for i in range(5):
            main_frame.grid_rowconfigure(i, weight=1)
        for i in range(5):
            main_frame.grid_columnconfigure(i, weight=1)

    def get_book_params(self):
        """Returns all parameters as a Book Object"""
        book = Book()
        book.file_path = self.path_label.get()
        book.selected_site = self.site_var.get()
        book.timer = self.timer_var.get()
        book.book_length = self.page_var.get()
        book.page_view = self.page_view.get()
        # #logs.LOOGGER.debug(f"File Path: {book.file_path}, Selected Site: {book.selected_site}, Timer: {book.timer}, Book Length: {book.book_length},"
        #                   f"Page View: {book.page_view}")
        return book

    def reset_ui(self):
        # Reset File Path
        self.path_label.config(state="normal")
        self.path_label.delete(0, tk.END)
        self.path_label.config(state="readonly")

        # Reset Page Count
        self.page_var.set("")

        # Reset Selected Site
        self.site_selector.current(0)

    def _handle_site_change(self, *args):
        """Handles changes to site selector"""
        selected_site = self.site_var.get()

        if selected_site == "Hoopla":
            self.page_view_selector.current(0)
            self.page_view_selector.config(state="disabled", style="TCombobox")
            # self.page_view_selector.config(style="Disabled.TCombobox")
            self.tooltip_page = ToolTip(self.page_count, "Please Make Sure You Are Getting The Page Count When In Full Screen On The Webpage, FN+F11")
        else:
            self.page_view_selector.config(state="readonly", style="TCombobox")
            # self.page_view_selector.config(style="TCombobox")
            try:
                self.tooltip_page.remove()
            except AttributeError:
                pass

    def _setup_logger(self):
        log_level = []
        console_level = None
        if self.settings.console_level == "INFO":
            console_level = logging.INFO
        elif self.settings.console_level == "DEBUG":
            console_level = logging.DEBUG
        elif self.settings.console_level == "WARNING":
            console_level = logging.WARNING
        elif self.settings.console_level == "ERROR":
            console_level = logging.ERROR
        elif self.settings.console_level == "CRITICAL":
            console_level = logging.CRITICAL
        if not self.settings.info:
            log_level.append(logging.INFO)
        if not self.settings.debug:
            log_level.append(logging.DEBUG)
        setup_logging(
            log_dir="logs", console_logging=self.settings.console_logging, console_level=console_level
        )
        logging.info("Logger configured")
        # Mute PIL debug logs
        logging.getLogger("PIL").setLevel(logging.WARNING)
        # logs.LOOGGER = logs.AppLogger(ignore_levels=log_level).get_logger()

    def _validate_int_input(self, P):
        return P.isdigit() or P == ""

    def _ask_user_save_location(self):
        """Open file dialog to let user select save location."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save PDF As"
        )
        if file_path:
            self.path_label.config(state="normal")
            self.path_label.delete(0, tk.END)
            self.path_label.insert(0, file_path)
            self.path_label.config(state="readonly")

    def run(self):
        self.window.mainloop()

    def set_start_command(self, command):
        self.start_command = command
