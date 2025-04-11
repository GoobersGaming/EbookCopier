from ebook_capture.managers import CaptureConfig, PauseManager, PDFManager, ScreenshotManger, PageProcessor
import keyboard
import time
from ui import popup_windows
import logging
logger = logging.getLogger(__name__)


"""Logic For Copying The Book"""
# TODO:  # Better Solution For Hoopla Reloading When Losing Focus
# Collect Blank Data Per Site
# Ensure raise comes back to a popup..
# Maximum second pass length


def capture_ebook(book, settings):
    """Setup components"""
    capture_config = CaptureConfig(book.capture_box)
    pause_manager = PauseManager(timer=int(book.timer),
                                 extra_delay=settings.extra_delay[book.selected_site])
    pause_manager.start_listener()
    screenshot_manager = ScreenshotManger(capture_config=capture_config,
                                          blank_attempts=2,
                                          threshold=settings.thresholds[book.selected_site],
                                          extra_delay=settings.extra_delay[book.selected_site],
                                          retry_delay=int(book.timer))

    pdf_manager = PDFManager(max_img=settings.max_images,
                             max_memory=settings.max_memory_mb,
                             output_pdf=book.file_path)

    processor = PageProcessor(screenshot_manager,
                              pause_manager,
                              pdf_manager,
                              extra_delay=settings.extra_delay[book.selected_site])
    logging.info("Components loaded..")
    try:
        # first pass till user declared book length
        logging.info("First Pass")
        logging.debug(f"Begin Ebook copying, selected site: {book.selected_site}, timer: {book.timer},\n"
                      f"thresholds: {settings.thresholds[book.selected_site]}, extra_delay: {settings.extra_delay[book.selected_site]}, "
                      f"max images {settings.max_images}, max_memory: {settings.max_memory_mb},\nfile path: {book.file_path}")
        time.sleep(settings.extra_delay[book.selected_site])

        if not _process_initial_pages(book, processor, pause_manager, int(book.timer)):
            logging.info("catpure ebook cancelled")
            return "cancelled"

        # Second pass continue till duplicate
        logging.info("Second pass")
        if not processor.end_of_book:
            if not _process_remaining_pages(processor, pause_manager, int(book.timer)):
                logging.info("capture ebook cancelled")
                return "cancelled"
        return True

    except Exception as e:
        # TODO: Ensure we are raising run cancelling errors back to main, for popup_window.messagebox
        logging.error(f"Runtimer error during capture: {str(e)}")
        raise RuntimeError(f"Runtime Error during capture: {str(e)}") from e
    finally:
        _cleanup_resources(pause_manager, pdf_manager)
        logging.info("Book Finished")


def _process_initial_pages(book, processor, pause_manager, timer):
    """Process pages up to delcared book length"""
    for page in range(int(book.book_length)):
        if _should_cancel(pause_manager):
            return False

        logging.debug(f"Page: {page} of {int(book.book_length)}")
        result = processor.process_page()
        logging.debug(f"Process initial pages result: {result}")

        if result == "cancelled":
            return False

        if result == "End":
            logging.debug("Initial process ended")
            return True

        navigate_to_next_page(timer, pause_manager)

    return True


def _process_remaining_pages(processor, pause_manager, timer):
    """Continue processing until duplicate found"""
    while True:
        if _should_cancel(pause_manager):
            return False

        result = processor.process_page(end_of_book_mode=True)
        logging.debug(f"Processing remaining pages result: {result}")
        if result == "cancelled":
            return False
        if result == "End":  # Found final duplicate
            logging.debug("Second process ended.")
            return True

        navigate_to_next_page(timer, pause_manager)


def _should_cancel(pause_manager):
    return (pause_manager.is_cancelled() or pause_manager.check_for_pause(delay=False))


def _cleanup_resources(pause_manager, pdf_manager):
    pause_manager.stop_listener()
    pdf_manager.finalize()


def navigate_to_next_page(timer, pause_manager):
    if popup_windows.check_enviroment():
        # Browser needed to be activated/focused or fullscreened
        pause_manager.check_for_pause(delay=True)  # Wait for extra delay rather than, standard timer
    keyboard.press_and_release("right")
    logging.info("Navigating to next page.")
    pause_manager.check_for_pause(delay=False)
    return True
