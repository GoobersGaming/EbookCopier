import os
import time
from utils import browser
from ui import popup_windows
from utils import logs
from ui.help import cont_message
from ui.main_ui import BookCopierApp
from ui.rectangle_drawer import RectangleEditor
from utils.take_screenshots import capture_ebook
from pathlib import Path


"""Main Python Module For Running The Script"""
#TODO:
        # Standanize Variable/Function Naming
        # Stadanize Commenting

def start_button_action(book_param, main_window, settings):
    if not _validate_inputs(book_param):
        return
    overlay = popup_windows.disable_window(main_window) 
    try:
        if not _prepare_browser_enviroment():
            return
        # Find what monitor edge is on
        book_param.monitor_display = browser.get_edge_display_number()
        logs.LOGGER.debug(f"book_param.monitor_display set: {book_param.monitor_display}")
        if not _confirm_continuation(book_param):
            return
        if not _process_capture_box(settings, book_param, main_window):
            return
        main_window.withdraw()
        finished_book = _record_book(settings, book_param)
        if finished_book == "cancelled":
            _book_cancelled(book_param.file_path)
        else:
            _book_completed(book_param.file_path)
        app.reset_ui()
        book_param.clear_values()
        logs.LOGGER.info("App reset, book_params cleared")
    
    finally:
        main_window.deiconify() 
        popup_windows.restore_window(overlay)

def _book_cancelled(file_path):
    logs.LOGGER.info("Ebook Copier Cancelled")
    if popup_windows.ask_yes_no("Delete PDF", "Do You Want To Delete Unfinished Book?", "Delete", "Keep", btn_focus="Delete"):
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
        finally:
            popup_windows.message_box("PDF Removed", f"{file_path}\n Was Removed")
            logs.LOGGER.info("PDF Deleted")

def _book_completed(file_path):
    popup_windows.message_box("Finished", f"PDF Saved To:\n {file_path}")
    completed_path = os.path.dirname(file_path)
    os.startfile(completed_path)
    logs.LOGGER.info("Book Finished")



def _validate_inputs(book):
    """Validate User Inputs, and show error warnings for missing inputs"""
    try:
        book.validate()
    except ValueError as e:
        error_code = str(e)
        if error_code == "empty_file_path":
            logs.LOGGER.debug(f"{book.file_path} invalid file path")
            popup_windows.message_box("Missing Save Path", "Please Enter A Save Location For Your PDF")

        elif error_code == "invalid_directory":
            logs.LOGGER.debug(f"{book.file_path} invalid file path")
            popup_windows.message_box("Missing File Dir", "Please Enter A Valid Save Location For Your PDF")

        elif error_code == "invalid_timer":
            logs.LOGGER.debug(f"book.timer: {book.timer}")
            popup_windows.message_box("Missing Timer", "Please Enter A Number For The Timer")

        elif error_code == "invalid_length":
            logs.LOGGER.debug(f"book.book_length: {book.book_length}")
            popup_windows.message_box("Missing Page Count", "Please Enter The Book's Length")

        elif error_code == "no_site_selected":
            logs.LOGGER.debug(f"book.selected_site: {book.selected_site}")
            popup_windows.message_box("No Site Selected", "Please Selct A Site Before Continuing")

        elif error_code == "invalid_page_view":
            logs.LOGGER.debug(f"page_view: {book.page_view}")
            popup_windows.message_box("No Page View Selected", "Please Select A Valid Page View")
        return False
    logs.LOGGER.info("User inputs valid")
    return True

def _prepare_browser_enviroment():
    """Find, Activate, And Full Screen Microsoft Edge"""
    time.sleep(0.1)
    if not browser.activate_edge():
        popup_windows.message_box("Microsoft Edge Not Found", "Please Open Microsoft Edge To The Book You Wish To Copy")
        logs.LOGGER.info("Microsoft Edge is Not Open")
        return False
    time.sleep(0.5)

    if not browser.enter_fullscreen_if_needed():
        logs.LOGGER.info("Microsoft Edge Failed To Enter Full Screen")
        popup_windows.message_box("Fullscreen Failed", "Failed To Enter Fullscreen In Microsoft Edge, Please Try Again")
        return False
    
    logs.LOGGER.info("Browser enviroment prepared")
    return True

def _confirm_continuation(book):
    """Show continuation dialog"""
    message_content, help_content = cont_message(book.selected_site, book.page_view)
    response = popup_windows.custom_ask(title="Before Continuing", 
                                        message = message_content, 
                                        buttons={"Continue": True, 
                                                 "Cancel": False, 
                                                 "Help": "Help"}, 
                                                 help_items = help_content)   
    if response is False:
        logs.LOGGER.info("Continuation cancelled")
        return False
    else:
        logs.LOGGER.info("Continuation continued")
        return True

def _process_capture_box(settings, book, main_window):
    """Handles Capture Box Selection And Saving To Toml"""
    default_bounding_box = _get_saved_bounding_box(settings, book)

    editor = RectangleEditor(
        coords=default_bounding_box,
        monitor_num=book.monitor_display,
        parent=main_window
    )
    main_window.wait_window(editor.root)

    book.capture_box = editor.get_coords()
    
    _save_bounding_box(settings, book)
    
    _prepare_browser_enviroment()

    if book.capture_box:
        logs.LOGGER.info("Capture area set")
        return True
    else:
        logs.LOGGER.warning("Capture area not set")
        return False

def _record_book(settings, book_param):
    finished_book_args = {"timer": int(book_param.timer), 
                          "total_pages": int(book_param.book_length), 
                          "capture_area": book_param.capture_box, 
                          "max_img": settings.max_images, 
                          "max_mem": settings.max_memory_mb,
                          "selected_site": book_param.selected_site, 
                          "output_pdf": book_param.file_path}
    if book_param.capture_box:
        logs.LOGGER.debug(f"Starting capture_ebook, args: {finished_book_args}")
        finished_book = capture_ebook(**finished_book_args)
        logs.LOGGER.info("capture_ebook has finished")
        logs.LOGGER.debug(f"finished_book: {finished_book}")
        return finished_book


def _get_saved_bounding_box(settings, book):
    """Retrieve Saved Bounding Box Data If It Exists"""
    try:
        return settings.saved_capture_boxes[book.selected_site][str(book.monitor_display)][book.page_view]
    except Exception:
        logs.LOGGER.info(f"No Saved Bounding Box Data For Site:{book.selected_site} Monitor:{book.monitor_display}, Page View:{book.page_view}")
        return None

def _save_bounding_box(settings, book):
    """Save Bouning Box to settings/toml, if new or changed"""
    if not book.capture_box:
        return
    box = book.capture_box.copy()
    box.pop("monitor")

    try:
        if settings.saved_capture_boxes[book.selected_site][str(book.monitor_display)][book.page_view] != box:
            settings.update_saved_capture_box(
                book.selected_site,
                book.page_view,
                book.capture_box
            )
            logs.LOGGER.info("Capture Box Entry Updated in config.toml")
            logs.LOGGER.debug(f"Config.toml updated, selected_site: {book.selected_site}, page_view: {book.page_view}, capture_box: {book.capture_box}")
        logs.LOGGER.info("Using existing capture box data from config.toml")
    except KeyError:
        # No existing entry - save new one
        settings.update_saved_capture_box(book.selected_site, book.page_view, book.capture_box)
        logs.LOGGER.info(f"Capture Box Entry Addedd to config.toml")
        logs.LOGGER.debug(f"Entry added to Config.toml, selected_site: {book.selected_site}, page_view: {book.page_view}, capture_box: {book.capture_box}")

if __name__ == "__main__":
    update_path = Path("update.bat").resolve()
    if update_path.exists():
        new_location = update_path.parent.parent / update_path.name
        update_path.replace(new_location)
    app = BookCopierApp(start_command=start_button_action)
    app.run()