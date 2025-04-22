from utils.logs import setup_logging
import logging
import os
import time
from utils import browser
from ui.popup_windows import DialogResult
from ui.popup_windows import MessageBox, continuation
from ui.help import cont_message
from ui.main_ui import BookCopierUI
from ui.rectangle_drawer import RectangleEditor
from ebook_capture import capture_ebook
from settings.config import UserSettings
from PySide6.QtWidgets import QApplication, QDialog
from ui.styles import pyside_themes
logger = logging.getLogger(__name__)

# TODO: Proper checking of user response, proper user response values(enums)
# TODO: Edit Book Length After Continuation
# TODO: Do I want to overwrite the file if it exists, when user choses a file path?
# convert os.path to pathlib
# standarize my naming covention and commenting to be uniform
# clean up logging, ensure no double logging of same info, overlogging?
# Add more browser support
# add a settings UI
# add a add new site UI
# auto create a startup shortcut, that can also change its python path if needed
# Add more user configuration over log size, image types, compression, etc.
# Remove PyMuPDF
# Add licenseing, readme attributes.
# handle directory persistence for cross session persistance


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
        try:
            if not self._prepare_browser_enviroment():
                return
            self.book.monitor_display = browser.get_edge_display_number()
            logger.debug(f"Edge located on: {book_param.monitor_display} monitor")

            if not self._confirm_continuation():
                return
            # Lets user ensure on they are on starting page, and double check page count
            user_check_length = MessageBox.information(title="Check Webpage",
                                                       message=f"Make sure the book is on PAGE ONE, and that {book_param.book_length} is the correct length of the book while in FN+F11 MODE!",
                                                       button_options=[
                                                           {"text": "Continue", "return": DialogResult.ACCEPT},
                                                           {"text": "Cancel", "return": DialogResult.REJECT}])
            if user_check_length != DialogResult.ACCEPT:
                return

            if not self._process_capture_box():
                return
            # Withdraw main ui window, and begin book processing
            self.main_window.hide_window()

            # self.main_window.withdraw()
            finished_book = self._record_book()
            logger.debug(f"Finished Book is: {finished_book}")

            # Handle finished book
            if finished_book is False:
                self._handle_cancelled_book()
            elif finished_book is True:
                self._handle_completed_book()
            else:
                raise RuntimeError(f"Finished book failed give a valid return: {finished_book}")
            self._reset_application()

        except Exception as e:
            logger.error(f"Runtime error: {str(e)}")
            MessageBox.error("Runtime Error", f"Run Failed\nError: {str(e)}")

        finally:
            # Restore/Reset
            self.main_window.restore_window()

    def _validate_inputs(self, book):
        """Validate user inputs"""

        validation_responses = {
            "empty_file_path": ("Missing Save Path", "Please choose a location to save the finished PDF."),
            "invalid_file_path": ("Missing File Dir", "Please enter a valid save location for your PDF"),
            "invalid_timer": ("Invalid Timer", "Please enter a valid timer for delay between pages"),
            "empty_site_selected": ("Invalid Site", "Please choose a valid site from the dropdown menu"),
            "invalid_page_view": ("Invalid Page View", "Please select a valid page view for the site"),
            "invalid_book_length": ("Invalid Book Length", "Please enter the number of pages in the book.")
        }
        try:
            book.validate()
            logger.info("Valid user inputs")
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
                logger.debug(f"Invalid input ({error_code}): {attribute_value}")
                MessageBox.information(title, message)
            return False

    def _prepare_browser_enviroment(self):
        """Check and Setup browser"""
        logger.info("Activate Edge")

        if not browser.activate_edge_window():
            MessageBox.warning("Microsfot Edge not found", "Please make sure Microsoft Edge is open, "
                               "and you are on the book you wish to copy")
            logger.warning("Microsoft Edge not found, Are you sure its running?")
            return False
        logger.info("edge is active")
        time.sleep(0.5)

        if not browser.enter_fullscreen_if_needed():
            logger.warning("Microsoft edge failed to enter full screen.")
            MessageBox.warning("Fullscreen Failed", "Microsoft Edge failed to enter fullscreen, See administrator if this continues")
            return False
        logger.info("Browser envrioment prepare")
        return True

    def _confirm_continuation(self):
        "Get user confirmation to continue to selection area"
        message_content, help_content = cont_message(self.book.selected_site, self.book.page_view)
        response = continuation(title="Before Continuing",
                                message=message_content,
                                help_items=help_content)
        if response != DialogResult.ACCEPT:
            logger.info("User cancelled continuation")
            return False

        logger.info("User confirmed continuation")
        return True

    def _process_capture_box(self):
        # TODO: consider adding a raise to popup if failure
        """Sets/saves selection area of screen"""
        starting_bounding_box = self._get_saved_bounding_box()
        logger.debug(f"Rectangle Editors starting bounding box: {starting_bounding_box}")
        rect_drawer = RectangleEditor(coords=starting_bounding_box, monitor_num=self.book.monitor_display)
        # Show rectangle editor
        result = rect_drawer.exec()
        # check rect_drawer return output
        if result == QDialog.DialogCode.Accepted:
            coords = rect_drawer.get_coords()
            logger.debug("rectdrawer cords: {rect_drawer.get_coords()}")
            print("Got coords:", coords)
        else:
            logger.info("User cancelled")
        # Add coords to book.
        print(f"result: {result}")
        self.book.capture_box = rect_drawer.get_coords()
        # Save user bbox cords
        self._save_bounding_box()
        # re-prepare browser
        self._prepare_browser_enviroment()

        if self.book.capture_box:
            return True
        logger.warning("Capture box not set")
        return False

    def _record_book(self):
        """Start the capture recording"""
        # TODO: Add a else raise?
        if self.book.capture_box:
            logger.info("Ebook capture started..")
            recorded_book = capture_ebook(self.book, self.settings)
            logger.info(f"recorded book: {recorded_book}")
            return recorded_book

    def _handle_cancelled_book(self):
        """Handles capture process being cancelled"""
        logger.info("Run cancelled")
        delete_response = MessageBox.question(title="Delete Pdf",
                                              message="Do you wish to delete the unfinished book?",
                                              button_options=[
                                                  {"text": "Delete", "return": DialogResult.ACCEPT},
                                                  {"text": "Keep", "return": DialogResult.REJECT}])
        if delete_response == DialogResult.ACCEPT:
            try:
                os.remove(self.book.file_path)
            except FileNotFoundError:
                # incase book was cancelled before a batch was actually saved
                pass
            finally:
                MessageBox.information("PDF remove", f"{self.book.file_path}\nDeleted")
                logger.info("PDF removed")
        else:
            # User chose to keep unfinished book
            self._handle_completed_book()

    def _handle_completed_book(self):
        """handle capture process successfully completing"""
        MessageBox.information("Finished", f"PDF saved too:\n{self.book.file_path}")

        completed_path = os.path.dirname(self.book.file_path)
        os.startfile(completed_path)
        logger.info(f"Book completed, saved to: {self.book.file_path}")

    def _reset_application(self):
        """resets ui and book params"""
        self.main_window.reset_ui()
        self.main_window.restore_window()
        self.book.clear_values()
        logger.info("App reset")

    def _get_saved_bounding_box(self):
        """Retrieve saved bounding box data if it exists"""
        logger.debug(f"Checking for saved bbox data, site: {self.book.selected_site}, monitor: {self.book.monitor_display}, page view: {self.book.page_view}")
        try:
            bbox = self.settings.saved_capture_boxes[self.book.selected_site][str(self.book.monitor_display)][self.book.page_view]
            logger.debug(f"Saved bbox{bbox}, from site{self.book.selected_site}, on monitor: {self.book.monitor_display}, with page view: {self.book.page_view}")
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
                logger.info("Saving capture box data to config.toml")
                logger.debug(f"Saving capture box: {self.book.capture_box}, of page view: {self.book.page_view}, for site: {self.book.selected_site}")
            else:
                logger.info("Using previously saved capture box data")
        except KeyError:
            # No previously saved capture box data, save new data to config.toml
            self.settings.update_saved_capture_box(self.book.selected_site, self.book.page_view, self.book.capture_box)


if __name__ == "__main__":
    # Create a default logger, that we will update later to user pref to catch early issues.
    setup_logging(console_logging=True, console_level=logging.DEBUG)
    logger.info("Logger started")
    # set application
    app = QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(pyside_themes(theme="dark_theme"))

    # Set application wide quit behavior
    app.setQuitOnLastWindowClosed(True)

    # Start User settings
    user_settings = UserSettings()
    # Start main ui
    main_window = BookCopierUI(user_settings)
    # start starting process
    book_copier = BookCopier(main_window, user_settings)
    # set start button command
    main_window.set_start_command(book_copier.start)
    # show main window
    main_window.show()
    app.exec()
