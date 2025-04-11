from utils.logs import setup_logging
import logging
import os
import time
from utils import browser
from ui import popup_windows
from ui.help import cont_message
from ui.main_ui import BookCopierUI
from ui.rectangle_drawer import RectangleEditor
from pathlib import Path
from ebook_capture import capture_ebook
from settings.config import UserSettings

# TODO: Do I want to overwrite the file if it exists, when user choses a file path?
# remove pathlib? not really needed, seems under utilize, use os.
# standarize my naming covention and commenting to be uniform
# am i over logging?
# Make my messagebox nicer. espically for displaying file location.
# Add more browser support?
# True no focus stealing "interactive" windows.
# add a settings window to visually adjust config.toml
# Move update.bat to python script.
# if update -> new file handles download/movement and main restart -> run update file, closes main, updates -> restart main, delete update file
# Add more user configuration over log size, image types, compression, etc.
# Remove PyMuPDF


class BookCopier:
    """Validates/gathers user inputs, prepares enviroment, handles the starting and finishing of the automated capture proocess."""
    def __init__(self, main_window, settings):
        self.main_window = main_window
        self.settings = settings
        self.overlay = None
        self.book = None

    def start(self, book_param):
        if not self._validate_inputs(book_param):
            return
        self.book = book_param
        self.overlay = popup_windows.disable_window(self.main_window)
        try:
            if not self._prepare_browser_enviroment():
                return
            self.book.monitor_display = browser.get_edge_display_number()
            logging.debug(f"Edge located on: {book_param.monitor_display} monitor")

            if not self._confirm_continuation():
                return

            if not self._process_capture_box():
                return

            # Withdraw main ui window, and begin book processing
            self.main_window.withdraw()
            finished_book = self._record_book()
            logging.debug(f"Finished Book is: {finished_book}")

            # Handle finished book
            if finished_book == "cancelled":
                self._handle_cancelled_book()
            else:
                self._handle_completed_book()
            self._reset_application()

        except Exception as e:
            logging.error(f"Runtime error: {str(e)}")
            popup_windows.message_box("Runtime Error", f"Run failed\nError: {str(e)}")

        finally:
            # Restore main ui window
            self.main_window.deiconify()
            popup_windows.restore_window(self.overlay)

    def _validate_inputs(self, book):
        """Validate user inputs"""

        validation_responses = {
            "empty_file_path": ("Missing Save Path", "Please enter a save location for pdf."),
            "invalid_file_path": ("Missing File Dir", "Please enter a valid save location for your pdf"),
            "invalid_timer": ("Invalid Timer", "Please enter a valid timer for delay between pages"),
            "empty_site_selected": ("Invalid Site", "Please choose a valid site from the dropdown menu"),
            "invalid_page_view": ("Invalid Page View", "Please select a valid page view for the site"),
            "invalid_book_length": ("Invalid Book Length", "Please enter the number of pages in the book.")
        }
        try:
            book.validate()
            logging.info("Valid user inputs")
            return True

        except ValueError as e:
            error_code = str(e)
            if error_code in validation_responses:
                title, message = validation_responses[error_code]
                # Remove prefix from string
                for prefix in ["empty_", "invalid_"]:
                    if error_code.startswith(prefix):
                        attribute_name = error_code[len(prefix):]
                        break
                    else:
                        attribute_name = error_code
                # Get value from Book, returns None as default
                attribute_value = getattr(book, attribute_name, None)
                logging.debug(f"Invalid input ({error_code}): {attribute_value}")
                popup_windows.message_box(title, message)
            return False

    def _prepare_browser_enviroment(self):
        """Check and Setup browser"""
        logging.info("Activate Edge")
        if not browser.activate_edge_window():
            popup_windows.message_box("Microsoft Edge not found", "Please make sure Microsoft Edge is open, and you are on the book you wish to copy")
            logging.warning("Microsoft Edge not found, Are you sure its running?")
            return False
        logging.info("edge is active")
        time.sleep(0.5)

        if not browser.enter_fullscreen_if_needed():
            logging.warning("Microsoft edge failed to enter full screen.")
            popup_windows.message_box("Fullscreen failed", "Microsoft Edge failed to enter fullscreen, See administrator if this continues.")
            return False
        logging.info("Browser envrioment prepare")
        return True

    def _confirm_continuation(self):
        "Get user confirmation to continue to selection area"
        message_content, help_content = cont_message(self.book.selected_site, self.book.page_view)
        reponse = popup_windows.custom_ask(
            title="Before Continuing",
            message=message_content,
            buttons={"Continue": True, "Cancel": False, "Help": "help"},
            help_items=help_content
        )
        if reponse is False:
            logging.info("User cancelled continuation")
            return False

        logging.info("User confirmed continuation")
        return True

    def _process_capture_box(self):
        # TODO: consider adding a raise to popup if failure
        """Sets/saves selection area of screen"""
        starting_bounding_box = self._get_saved_bounding_box()
        logging.debug(f"Rectangle Editors starting bounding box: {starting_bounding_box}")
        rect_drawer = RectangleEditor(
            coords=starting_bounding_box,
            monitor_num=self.book.monitor_display,
            parent=self.main_window
        )
        # Wait for rectangle editor to finish
        self.main_window.wait_window(rect_drawer.root)

        self.book.capture_box = rect_drawer.get_coords()
        # Save user bbox cords
        self._save_bounding_box()
        # re-prepare browser
        self._prepare_browser_enviroment()

        if self.book.capture_box:
            return True
        logging.warning("Capture box not set")
        return False

    def _record_book(self):
        """Start the capture recording"""
        # TODO: Add a else raise?
        if self.book.capture_box:
            logging.info("Ebook capture started..")
            recorded_book = capture_ebook(self.book, self.settings)
            logging.info(f"recorded book: {recorded_book}")
            return recorded_book

    def _handle_cancelled_book(self):
        """Handles capture process being cancelled"""
        logging.info("Run cancelled")
        if popup_windows.ask_yes_no("Delete PDF", "Do you wish to delete the unfinished book?", "Delete", "Keep", btn_focus="Delete"):
            try:
                os.remove(self.book.file_path)
            except FileNotFoundError:
                # incase book was cancelled before a batch was actually saved
                pass
            finally:
                popup_windows.message_box("PDF removed", f"{self.book.file_path}\nDeleted")
                logging.info("PDF removed")
        else:
            # User chose to keep unfinished book
            self._handle_completed_book()

    def _handle_completed_book(self):
        """handle capture process successfully completing"""
        popup_windows.message_box("Finished", f"PDF saved to:\n{self.book.file_path}")
        completed_path = os.path.dirname(self.book.file_path)
        os.startfile(completed_path)
        logging.info(f"Book completed, saved to: {self.book.file_path}")

    def _reset_application(self):
        """resets ui and book params"""
        app.reset_ui()
        self.book.clear_values()
        logging.info("App reset")

    def _get_saved_bounding_box(self):
        """Retrieve saved bounding box data if it exists"""
        logging.debug(f"Checking for saved bbox data, site: {self.book.selected_site}, monitor: {self.book.monitor_display}, page view: {self.book.page_view}")
        try:
            bbox = self.settings.saved_capture_boxes[self.book.selected_site][str(self.book.monitor_display)][self.book.page_view]
            logging.debug(f"Saved bbox{bbox}, from site{self.book.selected_site}, on monitor: {self.book.monitor_display}, with page view: {self.book.page_view}")
            return bbox
        except Exception:
            return None

    def _save_bounding_box(self):
        """Save bounding box after selection"""
        if not self.book.capture_box:
            return
        box = self.book.capture_box.copy()
        box.pop("monitor")
        try:
            if self.settings.saved_capture_boxes[self.book.selected_site][str(self.book.monitor_display)][self.book.page_view] != box:
                self.settings.update_saved_capture_box(
                    self.book.selected_site,
                    self.book.page_view,
                    self.book.capture_box)
                logging.info("Saving capture box data to config.toml")
                logging.debug(f"Saving capture box: {self.book.capture_box}, of page view: {self.book.page_view}, for site: {self.book.selected_site}")
            else:
                logging.info("Using previously saved capture box data")
        except KeyError:
            # No previously saved capture box data, save new data to config.toml
            self.settings.update_saved_capture_box(self.book.selected_site, self.book.page_view, self.book.capture_box)


if __name__ == "__main__":
    update_path = Path("update.bat").resolve()
    if update_path.exists():
        new_location = update_path.parent.parent / update_path.name
        update_path.replace(new_location)

    setup_logging(console_logging=True, console_level=logging.DEBUG)
    logging.info("Logger started")
    user_settings = UserSettings()
    app = BookCopierUI(user_settings)
    book_copier = BookCopier(app.window, user_settings)
    app.set_start_command(book_copier.start)
    app.run()
